"""
metrics.py
Filtra volantes e calcula o índice de adequação ao perfil do Villarreal.
Perfil: bloco médio, pressão seletiva, transições verticais rápidas.
"""

import sys
import pandas as pd
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    df_std = pd.read_csv(RAW_DIR / "standard.csv", header=[0, 1], index_col=[0, 1, 2, 3])
    df_misc = pd.read_csv(RAW_DIR / "misc.csv", header=[0, 1], index_col=[0, 1, 2, 3])
    df_play = pd.read_csv(RAW_DIR / "playing_time.csv", header=[0, 1], index_col=[0, 1, 2, 3])
    return df_std, df_misc, df_play


def flatten_columns(df):
    """Achata o MultiIndex das colunas para nomes simples."""
    df.columns = ['_'.join(col).strip('_ ') if col[1] not in ['', col[0]] else col[0]
                  for col in df.columns]
    return df


def filter_midfielders(df, min_90s=10.0):
    """
    Filtra jogadores com posição primária MF e mínimo de minutos jogados.
    min_90s=10 significa pelo menos 900 minutos — evita jogadores com poucos dados.
    """
    df = df.copy()

    # Coluna de posição após flatten
    pos_col = [c for c in df.columns if 'pos' in c.lower()][0]
    age_col = [c for c in df.columns if 'age' in c.lower()][0]

    # A posição primária é o primeiro código antes da vírgula (ex: "DF,MF" -> lateral
    # que ocasionalmente joga no meio-campo, não um volante). Exigir MF como primária
    # evita incluir laterais/zagueiros híbridos no pool de volantes.
    primary_pos = df[pos_col].astype(str).str.split(',').str[0]
    df = df[primary_pos == 'MF']

    # Filtrar por minutos mínimos
    nineties_col = [c for c in df.columns if '90s' in c or 'Unnamed: 8' in c][0]
    df = df[pd.to_numeric(df[nineties_col], errors='coerce') >= min_90s]

    print(f"Volantes encontrados (min {min_90s} x90s): {len(df)}")
    return df


def percentile_normalize(series):
    """
    Normaliza por rank percentual (0-1) em vez de min-max.
    Robusto a outliers: um único valor extremo (comum em métricas de amostra
    pequena, ex. On-Off) não distorce a escala de todos os outros jogadores.
    """
    return series.rank(pct=True, method='average')


def build_villarreal_index(df_std, df_misc, df_play):
    """
    Constrói o índice de adequação ao perfil do Villarreal.

    Métricas usadas (todas por 90 minutos, exceto On-Off):
    - TklW (tackles ganhos)       → recuperação de bola
    - Int (interceções)           → leitura do jogo
    - Fls (faltas cometidas)      → agressividade controlada (invertido — menos é melhor)
    - CrdY (cartões amarelos)     → disciplina (invertido)
    - On-Off (saldo de gols do time com o jogador em campo vs fora, ajustado à
      média do próprio time) → impacto individual real. Preferido a PPM puro:
      PPM mede a qualidade do time (um reserva do Real Madrid tem PPM alto só
      por jogar lá), enquanto On-Off isola a contribuição marginal do jogador.
    """

    # Flatten
    df_std = flatten_columns(df_std.reset_index())
    df_misc = flatten_columns(df_misc.reset_index())
    df_play = flatten_columns(df_play.reset_index())

    # Filtrar volantes no misc (tem as métricas defensivas chave)
    df_misc = filter_midfielders(df_misc)

    # Colunas de identificação
    id_cols = ['league', 'season', 'team', 'player']

    # Selecionar métricas relevantes do misc
    misc_cols = id_cols + [c for c in df_misc.columns
                           if any(x in c for x in ['pos', 'age', '90s', 'TklW', 'Int', 'Fls', 'CrdY'])]
    df = df_misc[misc_cols].copy()

    # Juntar On-Off do playing_time (impacto ajustado ao time)
    onoff_cols = id_cols + [c for c in df_play.columns if 'On-Off' in c]
    if onoff_cols:
        df_onoff = df_play[onoff_cols].drop_duplicates(subset=id_cols)
        df = df.merge(df_onoff, on=id_cols, how='left')

    # Converter para numérico
    metric_cols = [c for c in df.columns if c not in id_cols + ['pos', 'age']]
    for col in metric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Calcular por 90 minutos
    nineties = df[[c for c in df.columns if '90s' in c][0]]
    df['TklW_p90'] = df[[c for c in df.columns if 'TklW' in c][0]] / nineties
    df['Int_p90']  = df[[c for c in df.columns if 'Int' in c][0]]  / nineties
    df['Fls_p90']  = df[[c for c in df.columns if 'Fls' in c][0]]  / nineties
    df['CrdY_p90'] = df[[c for c in df.columns if 'CrdY' in c][0]] / nineties
    onoff_col = [c for c in df.columns if 'On-Off' in c]
    df['OnOff'] = df[onoff_col[0]] if onoff_col else 0

    # Normalizar 0-1 (percentil, robusto a outliers)
    df['n_TklW'] = percentile_normalize(df['TklW_p90'])
    df['n_Int']  = percentile_normalize(df['Int_p90'])
    df['n_Fls']  = 1 - percentile_normalize(df['Fls_p90'])   # invertido
    df['n_CrdY'] = 1 - percentile_normalize(df['CrdY_p90'])  # invertido
    df['n_OnOff'] = percentile_normalize(df['OnOff'])

    # Índice final — pesos baseados no perfil do Villarreal
    # Recuperação e leitura pesam mais (núcleo do perfil de volante destruidor);
    # disciplina pesa pouco (métricas ruidosas em amostra de uma temporada);
    # impacto (On-Off) completa o índice sem carregar o viés de "jogar num time forte".
    df['villarreal_index'] = (
        df['n_TklW'] * 0.32 +
        df['n_Int']  * 0.28 +
        df['n_Fls']  * 0.10 +
        df['n_CrdY'] * 0.08 +
        df['n_OnOff'] * 0.22
    )

    df = df.sort_values('villarreal_index', ascending=False)
    return df


if __name__ == "__main__":
    df_std, df_misc, df_play = load_data()
    df_result = build_villarreal_index(df_std, df_misc, df_play)

    output_path = PROCESSED_DIR / "midfielder_index.csv"
    df_result.to_csv(output_path, index=False)
    print(f"\nTop 10 volantes para o perfil Villarreal:\n")
    print(df_result[['player', 'team', 'league', 'villarreal_index']].head(10).to_string(index=False))
    print(f"\nSalvo em {output_path}")
