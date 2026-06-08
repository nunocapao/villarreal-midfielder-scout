"""
metrics.py
Filtra volantes e calcula o índice de adequação ao perfil do Villarreal.
Perfil: bloco médio, pressão seletiva, transições verticais rápidas.
"""

import pandas as pd
from pathlib import Path

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


def filter_midfielders(df, min_90s=5.0):
    """
    Filtra jogadores com posição MF e mínimo de minutos jogados.
    min_90s=5 significa pelo menos 450 minutos — evita jogadores com poucos dados.
    """
    df = df.copy()

    # Coluna de posição após flatten
    pos_col = [c for c in df.columns if 'pos' in c.lower()][0]
    age_col = [c for c in df.columns if 'age' in c.lower()][0]

    # Filtrar por posição MF
    df = df[df[pos_col].str.contains('MF', na=False)]

    # Filtrar por minutos mínimos
    nineties_col = [c for c in df.columns if '90s' in c or 'Unnamed: 8' in c][0]
    df = df[pd.to_numeric(df[nineties_col], errors='coerce') >= min_90s]

    print(f"Volantes encontrados (min {min_90s} x90s): {len(df)}")
    return df


def build_villarreal_index(df_std, df_misc, df_play):
    """
    Constrói o índice de adequação ao perfil do Villarreal.

    Métricas usadas (todas por 90 minutos):
    - TklW (tackles ganhos)       → recuperação de bola
    - Int (interceções)           → leitura do jogo
    - Fls (faltas cometidas)      → agressividade controlada (invertido — menos é melhor)
    - CrdY (cartões amarelos)     → disciplina (invertido)
    - PPM (pontos por jogo do team quando em campo) → impacto em vitórias
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

    # Juntar PPM do playing_time
    ppm_cols = id_cols + [c for c in df_play.columns if 'PPM' in c]
    if ppm_cols:
        df_ppm = df_play[ppm_cols].drop_duplicates(subset=id_cols)
        df = df.merge(df_ppm, on=id_cols, how='left')

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
    ppm_col = [c for c in df.columns if 'PPM' in c]
    df['PPM'] = df[ppm_col[0]] if ppm_col else 0

    # Normalizar 0-1 (min-max)
    def normalize(series):
        mn, mx = series.min(), series.max()
        return (series - mn) / (mx - mn) if mx > mn else series * 0

    df['n_TklW'] = normalize(df['TklW_p90'])
    df['n_Int']  = normalize(df['Int_p90'])
    df['n_Fls']  = 1 - normalize(df['Fls_p90'])   # invertido
    df['n_CrdY'] = 1 - normalize(df['CrdY_p90'])  # invertido
    df['n_PPM']  = normalize(df['PPM'])

    # Índice final — pesos baseados no perfil do Villarreal
    # Recuperação e leitura pesam mais, disciplina e impacto em vitórias completam
    df['villarreal_index'] = (
        df['n_TklW'] * 0.30 +
        df['n_Int']  * 0.25 +
        df['n_Fls']  * 0.15 +
        df['n_CrdY'] * 0.10 +
        df['n_PPM']  * 0.20
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