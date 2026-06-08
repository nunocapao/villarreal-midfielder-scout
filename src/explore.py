"""
explore.py
Analisa os dados brutos para entender estrutura e colunas disponíveis.
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Carregar os três ficheiros
df_std = pd.read_csv(RAW_DIR / "standard.csv", header=[0, 1], index_col=[0, 1, 2, 3])
df_misc = pd.read_csv(RAW_DIR / "misc.csv", header=[0, 1], index_col=[0, 1, 2, 3])
df_play = pd.read_csv(RAW_DIR / "playing_time.csv", header=[0, 1], index_col=[0, 1, 2, 3])

print("=== STANDARD ===")
print(f"Shape: {df_std.shape}")
print(df_std.columns.tolist()[:20])

print("\n=== MISC ===")
print(f"Shape: {df_misc.shape}")
print(df_misc.columns.tolist()[:20])

print("\n=== PLAYING TIME ===")
print(f"Shape: {df_play.shape}")
print(df_play.columns.tolist()[:20])

print("\n=== EXEMPLO DE JOGADOR (standard) ===")
print(df_std.head(3).to_string())