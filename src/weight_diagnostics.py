"""
weight_diagnostics.py
Ferramenta de diagnóstico (não altera o pipeline): checa se os pesos manuais
do villarreal_index fazem sentido à luz dos dados.

- Correlação entre as métricas: pesos altos em métricas muito correlacionadas
  entre si equivalem, na prática, a contar a mesma informação duas vezes.
- PCA: mostra quanto da variância entre volantes cada dimensão realmente
  explica, e como ficariam os pesos se fossem derivados puramente dos dados
  (primeira componente principal) em vez de escolhidos à mão.

Isso não substitui o julgamento tático (os pesos manuais codificam o que
importa para o *estilo* do Villarreal, não só o que varia mais nos dados),
mas serve de checagem de sanidade.
"""

import pandas as pd
from pathlib import Path
from sklearn.decomposition import PCA

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

METRIC_COLS = ["n_TklW", "n_Int", "n_Fls", "n_CrdY", "n_OnOff"]

MANUAL_WEIGHTS = {
    "n_TklW": 0.32,
    "n_Int": 0.28,
    "n_Fls": 0.10,
    "n_CrdY": 0.08,
    "n_OnOff": 0.22,
}


def main():
    df = pd.read_csv(PROCESSED_DIR / "midfielder_index.csv")
    X = df[METRIC_COLS].dropna()

    print(f"Amostra: {len(X)} volantes\n")

    print("=== Correlação entre métricas normalizadas ===")
    print(X.corr().round(2).to_string())
    print()

    pca = PCA(n_components=len(METRIC_COLS))
    pca.fit(X)

    print("=== Variância explicada por componente ===")
    for i, var in enumerate(pca.explained_variance_ratio_):
        print(f"PC{i+1}: {var:.1%}")
    print()

    pc1 = pca.components_[0]
    pc1_weights = abs(pc1) / abs(pc1).sum()

    print("=== Pesos manuais vs. peso implícito na 1ª componente principal ===")
    print(f"{'Métrica':<10} {'Manual':>8} {'PCA (PC1)':>10}")
    for col, w_pca in zip(METRIC_COLS, pc1_weights):
        print(f"{col:<10} {MANUAL_WEIGHTS[col]:>8.2f} {w_pca:>10.2f}")
    print()
    print("PC1 é a direção de maior variância entre os volantes — não é")
    print("necessariamente 'o que importa para o Villarreal', mas se os pesos")
    print("manuais estiverem muito distantes dela, vale perguntar por quê.")


if __name__ == "__main__":
    main()
