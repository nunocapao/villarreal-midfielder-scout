"""
scraper.py
Baixa dados de volantes de La Liga e outras ligas europeias do FBref
via soccerdata, e salva em data/raw/
"""

import sys

import soccerdata as sd
import pandas as pd
from pathlib import Path

# Pasta de destino
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# soccerdata==1.9.x só expõe estes stat_types em read_player_season_stats:
# 'standard', 'keeper', 'shooting', 'playing_time', 'misc'.
# Não existe 'passing' nesse método (fica só em read_player_match_stats,
# jogo a jogo — muito mais requisições, não usado aqui).
STAT_TYPES = ["standard", "misc", "playing_time"]


def fetch_defensive_midfielders(leagues: list, season: str, path_to_browser: str | None = None) -> dict:
    """
    Baixa estatísticas de volantes.
    Retorna um dict {stat_type: DataFrame} para cada tipo em STAT_TYPES.

    O FBref bloqueia requisições simples (Cloudflare) com alguma frequência.
    Se isso acontecer, passe `path_to_browser` (ex: caminho do Chrome) para
    o soccerdata usar um navegador real — por isso seleniumbase está nas
    dependências do projeto.
    """
    fbref = sd.FBref(leagues=leagues, seasons=season, path_to_browser=path_to_browser)

    dfs = {}
    for stat_type in STAT_TYPES:
        print(f"Baixando estatísticas {stat_type}...")
        dfs[stat_type] = fbref.read_player_season_stats(stat_type=stat_type)
    return dfs


def save_raw(df: pd.DataFrame, name: str):
    path = RAW_DIR / f"{name}.csv"
    df.to_csv(path)
    print(f"Salvo em {path}")


if __name__ == "__main__":
    LEAGUES = ["Big 5 European Leagues Combined"]
    SEASON = "2526"

    try:
        dfs = fetch_defensive_midfielders(LEAGUES, SEASON)
    except Exception as exc:
        print(f"\nFalha ao baixar dados do FBref: {exc}")
        print("Se for um bloqueio do Cloudflare (403 / 'Just a moment...'), "
              "rode novamente passando path_to_browser=<caminho do Chrome> "
              "para usar um navegador real em vez de requests puro.")
        sys.exit(1)

    for stat_type, df in dfs.items():
        save_raw(df, stat_type)

    print("\nPronto! Ficheiros salvos em data/raw/")
    print(f"Jogadores no dataset: {len(dfs['standard'])}")
