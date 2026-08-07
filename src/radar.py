"""
radar.py
Radar chart comparando o perfil tático dos top 5 volantes
vs o perfil ideal do Villarreal CF.
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_DIR    = Path(__file__).resolve().parent.parent / "outputs" / "rankings"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
FIGURES_DIR   = Path(__file__).resolve().parent.parent / "outputs" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Dimensões do radar — as 5 características do perfil Villarreal
DIMENSIONS = [
    "Recuperação\n(TklW/90)",
    "Leitura\n(Int/90)",
    "Disciplina\n(sem faltas)",
    "Controlo\n(sem amarelos)",
    "Impacto\n(On-Off)"
]

RADAR_METRIC_COLS = ["n_TklW", "n_Int", "n_Fls", "n_CrdY", "n_OnOff"]


def load():
    df = pd.read_csv(OUTPUT_DIR / "final_ranking.csv", index_col=0)
    return df


def get_villarreal_ideal() -> list:
    """
    Perfil ideal = médias reais dos volantes atuais do Villarreal no dataset,
    em vez de um vetor de referência arbitrário. Cai de volta a um vetor
    fixo (0.7 em cada dimensão, o que representa "acima da mediana da liga")
    apenas se não houver volantes do Villarreal na amostra filtrada.
    """
    idx_path = PROCESSED_DIR / "midfielder_index.csv"
    df_idx = pd.read_csv(idx_path)
    vill = df_idx[df_idx["team"] == "Villarreal"]

    if vill.empty:
        print("Aviso: nenhum volante do Villarreal encontrado no dataset — "
              "usando perfil de referência genérico.")
        return [0.7] * len(RADAR_METRIC_COLS)

    print(f"Perfil ideal calculado a partir de {len(vill)} volante(s) do Villarreal: "
          f"{', '.join(vill['player'])}")
    return [float(vill[col].mean()) for col in RADAR_METRIC_COLS]


def get_radar_values(row) -> list:
    """Extrai os valores normalizados das 5 dimensões para um jogador."""
    return [float(row.get(col, 0)) for col in RADAR_METRIC_COLS]


def radar_chart(df: pd.DataFrame):
    top5 = df.head(5)
    n_dims = len(DIMENSIONS)
    villarreal_ideal = get_villarreal_ideal()

    # Ângulos para cada dimensão
    angles = np.linspace(0, 2 * np.pi, n_dims, endpoint=False).tolist()
    angles += angles[:1]  # fechar o polígono

    fig, axes = plt.subplots(1, 5, figsize=(20, 5),
                             subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("#0D1117")
    fig.suptitle(
        "Top 5 Volantes — Perfil Tático vs Ideal Villarreal CF",
        color="white", fontsize=14, fontweight="bold", y=1.02
    )

    colors = ["#FFD700", "#00C9FF", "#FF6B6B", "#69FF47", "#FF9F43"]

    for i, (ax, (_, row)) in enumerate(zip(axes, top5.iterrows())):
        values = get_radar_values(row)
        values += values[:1]  # fechar

        ideal = villarreal_ideal + villarreal_ideal[:1]

        ax.set_facecolor("#0D1117")
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        # Grid e labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(DIMENSIONS, color="white", fontsize=7)
        ax.set_yticks([0.25, 0.50, 0.75, 1.00])
        ax.set_yticklabels(["0.25", "0.50", "0.75", "1.0"],
                           color="#666666", fontsize=5)
        ax.set_ylim(0, 1)
        ax.spines["polar"].set_color("#333333")
        ax.grid(color="#333333", linewidth=0.5)

        # Perfil ideal (fundo)
        ax.fill(angles, ideal, color="#FFFFFF", alpha=0.08)
        ax.plot(angles, ideal, color="#FFFFFF",
                linewidth=1, linestyle="--", alpha=0.4)

        # Perfil do jogador
        ax.fill(angles, values, color=colors[i], alpha=0.35)
        ax.plot(angles, values, color=colors[i], linewidth=2)

        # Título do jogador
        market_val = row.get("market_value_eur_m", 0)
        score      = row.get("final_score", 0)
        ax.set_title(
            f"{row['player']}\n{row['team']}\n€{market_val:.1f}M | Score: {score:.3f}",
            color=colors[i], fontsize=8, fontweight="bold", pad=15
        )

    # Legenda
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color="white", linewidth=1,
               linestyle="--", alpha=0.6, label="Perfil ideal Villarreal"),
    ]
    fig.legend(handles=legend_elements, loc="lower center",
               facecolor="#1C1C1C", edgecolor="#444444",
               labelcolor="white", fontsize=9, ncol=1)

    plt.tight_layout()
    out_path = FIGURES_DIR / "radar_chart.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    print(f"Radar chart salvo em {out_path}")
    plt.close(fig)


if __name__ == "__main__":
    df = load()
    radar_chart(df)