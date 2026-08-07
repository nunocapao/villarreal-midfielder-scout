"""
visualize.py
Gráfico de bolhas: índice tático vs valor de mercado.
Quadrante superior esquerdo = oportunidades de ouro para o Villarreal.
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_DIR  = Path(__file__).resolve().parent.parent / "outputs" / "rankings"
FIGURES_DIR = Path(__file__).resolve().parent.parent / "outputs" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

LEAGUE_COLORS = {
    "ESP-La Liga":         "#EA2E37",
    "ENG-Premier League":  "#00FF00",
    "GER-Bundesliga":      "#D4CD02",
    "FRA-Ligue 1":         "#398DDC",
    "ITA-Serie A":         "#D041AA",

}


def load():
    df = pd.read_csv(OUTPUT_DIR / "final_ranking.csv", index_col=0)
    age_col = [c for c in df.columns if 'age' in c.lower()][0]
    df = df.rename(columns={age_col: "age"})
    nineties_col = [c for c in df.columns if '90s' in c][0]
    df = df.rename(columns={nineties_col: "90s"})
    return df


def plot_bubble(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor("#0D1117")
    ax.set_facecolor("#0D1117")

    # Tamanho da bolha baseado em minutos jogados
    sizes = (df["90s"] * 12).clip(50, 600)

    for league, color in LEAGUE_COLORS.items():
        mask = df["league"] == league
        ax.scatter(
            df.loc[mask, "market_value_eur_m"],
            df.loc[mask, "villarreal_index"],
            s=sizes[mask],
            c=color,
            alpha=0.75,
            edgecolors="white",
            linewidths=0.4,
            label=league
        )

    # Linha de corte — top 15
    threshold_score = df["final_score"].iloc[14]
    top15 = df[df["final_score"] >= threshold_score]

    # Labels dos top 15
    for _, row in top15.iterrows():
        ax.annotate(
            row["player"],
            xy=(row["market_value_eur_m"], row["villarreal_index"]),
            xytext=(6, 4),
            textcoords="offset points",
            fontsize=7.5,
            color="white",
            fontweight="bold"
        )

    # Quadrante de ouro
    x_mid = df["market_value_eur_m"].median()
    y_mid = df["villarreal_index"].median()
    ax.axvline(x=x_mid, color="yellow", linewidth=0.6, linestyle="--", alpha=0.5)
    ax.axhline(y=y_mid, color="yellow", linewidth=0.6, linestyle="--", alpha=0.5)
    ax.text(1.2, df["villarreal_index"].max() * 0.97,
            "Zona de oportunidade", color="yellow", fontsize=8, alpha=0.8)

    # Estilo
    ax.set_xlabel("Valor de Mercado (€M)", color="white", fontsize=11)
    ax.set_ylabel("Índice Tático Villarreal", color="white", fontsize=11)
    ax.set_title(
        "Volantes Sub-28 — Custo-Benefício para o Villarreal CF\n"
        "Tamanho da bolha = minutos jogados | Quadrante superior esquerdo = oportunidade",
        color="white", fontsize=12, pad=15
    )
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333333")

    # Legenda das ligas
    legend = ax.legend(
        loc="lower right", fontsize=8,
        facecolor="#1C1C1C", edgecolor="#444444", labelcolor="white"
    )

    plt.tight_layout()
    out_path = FIGURES_DIR / "bubble_chart.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Gráfico salvo em {out_path}")
    plt.close(fig)


if __name__ == "__main__":
    df = load()
    print(f"Jogadores no gráfico: {len(df)}")
    plot_bubble(df)