"""
model.py
Cruza o índice tático com o valor de mercado do Transfermarkt.
Produz o ranking final de custo-benefício para o perfil Villarreal.
"""

import sys
import pandas as pd
from pathlib import Path

# Console do Windows costuma usar cp1252, que não representa vários
# caracteres de nomes de jogadores (ex: "ć", "ș") e quebra o print().
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
RAW_DIR       = Path(__file__).resolve().parent.parent / "data" / "raw"
OUTPUT_DIR    = Path(__file__).resolve().parent.parent / "outputs" / "rankings"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Posições do Transfermarkt que correspondem a volante
MIDFIELDER_POSITIONS = [
    "Defensive Midfield",
    "Central Midfield",
    "Attacking Midfield",
]

# Orçamento máximo do Villarreal (valor de mercado do jogador em €M)
MAX_VALUE = 30.0
MIN_VALUE = 1.0   # evitar jogadores sem valor registado


def load():
    df_index = pd.read_csv(PROCESSED_DIR / "midfielder_index.csv")
    df_market = pd.read_csv(RAW_DIR / "market_values.csv")
    return df_index, df_market


def clean_market(df_market: pd.DataFrame) -> pd.DataFrame:
    """Filtra apenas volantes com valor de mercado válido."""
    df = df_market[df_market["position"].isin(MIDFIELDER_POSITIONS)].copy()
    df = df[df["market_value_eur_m"].between(MIN_VALUE, MAX_VALUE)]
    df = df.drop_duplicates(subset=["player"])
    return df


def normalize_name(s: str) -> str:
    """Normalização simples para melhorar o match de nomes entre FBref e Transfermarkt."""
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def merge_datasets(df_index: pd.DataFrame, df_market: pd.DataFrame) -> pd.DataFrame:   
    """Junta os dois datasets pelo nome do jogador."""
    df_index["player_norm"]  = df_index["player"].apply(normalize_name)
    df_market["player_norm"] = df_market["player"].apply(normalize_name)

    df = df_index.merge(
        df_market[["player_norm", "market_value_eur_m", "position"]],
        on="player_norm",
        how="inner"
    )
    print(f"Jogadores com match entre FBref e Transfermarkt: {len(df)}")
    return df


def compute_value_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula o índice final de custo-benefício.
    Quanto maior o índice tático e menor o valor de mercado, melhor.
    """
    # Normalizar valor de mercado (invertido — mais barato = melhor score)
    df["n_value"] = 1 - (df["market_value_eur_m"] - MIN_VALUE) / (MAX_VALUE - MIN_VALUE)
    df["n_value"] = df["n_value"].clip(0, 1)

    # Índice final: 70% tático + 30% custo
    df["final_score"] = (
        df["villarreal_index"] * 0.70 +
        df["n_value"]          * 0.30
    )

    df = df.sort_values("final_score", ascending=False).reset_index(drop=True)
    df.index += 1  # ranking começa em 1
    return df


def print_report(df: pd.DataFrame):
    cols = ["player", "team", "league", "market_value_eur_m", "villarreal_index", "final_score"]
    print("\n" + "="*70)
    print("TOP 15 VOLANTES — CUSTO-BENEFÍCIO PARA O VILLARREAL CF")
    print("="*70)
    print(f"{'#':<4} {'Jogador':<22} {'Clube':<20} {'Liga':<20} {'€M':>5} {'Tático':>7} {'Score':>7}")
    print("-"*70)
    for rank, row in df.head(15).iterrows():
        print(f"{rank:<4} {row['player']:<22} {row['team']:<20} {row['league']:<20} "
              f"{row['market_value_eur_m']:>5.1f} {row['villarreal_index']:>7.3f} {row['final_score']:>7.3f}")
    print("="*70)


if __name__ == "__main__":
    df_index, df_market = load()

    df_market_clean = clean_market(df_market)
    print(f"Volantes no Transfermarkt (orçamento até €{MAX_VALUE}M): {len(df_market_clean)}")

    df_merged = merge_datasets(df_index, df_market_clean)
    
    #Filtro de idade — foco em jogadores entre 22 e 28 anos
    age_col = [c for c in df_merged.columns if 'age' in c.lower()][0]
    df_merged[age_col] = pd.to_numeric(df_merged[age_col], errors='coerce')
    df_merged = df_merged[df_merged[age_col].between(22, 28)]
    print(f"Após filtro de idade (22-28): {len(df_merged)}")

    df_final = compute_value_index(df_merged)

    output_path = OUTPUT_DIR / "final_ranking.csv"
    df_final.to_csv(output_path)
    print_report(df_final)
    print(f"\nRanking completo salvo em {output_path}")