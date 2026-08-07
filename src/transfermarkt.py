"""
transfermarkt.py
Recolhe valores de mercado de volantes do Transfermarkt via scraping direto.
"""

import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
import time

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# IDs das ligas no Transfermarkt
LEAGUE_URLS = {
    "ESP-La Liga":        "https://www.transfermarkt.com/laliga/startseite/wettbewerb/ES1",
    "ENG-Premier League": "https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1",
    "GER-Bundesliga":     "https://www.transfermarkt.com/bundesliga/startseite/wettbewerb/L1",
    "FRA-Ligue 1":        "https://www.transfermarkt.com/ligue-1/startseite/wettbewerb/FR1",
    "ITA-Serie A":        "https://www.transfermarkt.com/serie-a/startseite/wettbewerb/IT1",
}


def get_teams(league_url: str) -> list:
    """Recolhe os links de todos os clubes de uma liga."""
    resp = requests.get(league_url, headers=HEADERS)
    soup = BeautifulSoup(resp.content, "lxml")
    teams = []
    for a in soup.select("table.items td.hauptlink a"):
        href = a.get("href", "")
        if "/startseite/verein/" in href:
            full = "https://www.transfermarkt.com" + href
            if full not in teams:
                teams.append(full)
    return teams


def get_players_from_team(team_url: str, league: str) -> list:
    """Recolhe jogadores e valores de mercado de um clube."""
    resp = requests.get(team_url, headers=HEADERS)
    soup = BeautifulSoup(resp.content, "lxml")
    players = []
    for row in soup.select("table.items tbody tr"):
        try:
            name_tag = row.select_one("td.hauptlink a")
            pos_tag  = row.select_one("td.posrela table tr:nth-child(2) td")
            val_tag  = row.select_one("td.rechts.hauptlink")
            age_tag  = row.select_one("td:nth-child(3)")
            if not name_tag or not val_tag:
                continue
            name  = name_tag.text.strip()
            pos   = pos_tag.text.strip() if pos_tag else ""
            value = val_tag.text.strip()
            age   = age_tag.text.strip() if age_tag else ""
            players.append({
                "player": name,
                "position": pos,
                "age": age,
                "market_value_raw": value,
                "league": league
            })
        except Exception:
            continue
    return players


def parse_value(val_str: str) -> float:
    """Converte '€25.00m' ou '€500k' para float em milhões."""
    val_str = val_str.replace("€", "").replace(",", ".").strip()
    if "m" in val_str:
        return float(val_str.replace("m", ""))
    elif "k" in val_str:
        return float(val_str.replace("k", "")) / 1000
    return 0.0


if __name__ == "__main__":
    all_players = []

    for league, url in LEAGUE_URLS.items():
        print(f"\nProcessando {league}...")
        teams = get_teams(url)
        print(f"  {len(teams)} clubes encontrados")

        for team_url in teams:  # todos os clubes
            players = get_players_from_team(team_url, league)
            all_players.extend(players)
            time.sleep(2)  # respeitar o servidor

    df = pd.DataFrame(all_players)
    df["market_value_eur_m"] = df["market_value_raw"].apply(parse_value)

    output_path = RAW_DIR / "market_values.csv"
    df.to_csv(output_path, index=False)

    print(f"\nTotal jogadores: {len(df)}")
    print(df[["player", "position", "market_value_eur_m", "league"]].head(10).to_string(index=False))
    print(f"\nSalvo em {output_path}")