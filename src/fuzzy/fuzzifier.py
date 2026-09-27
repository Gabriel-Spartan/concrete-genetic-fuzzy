import numpy as np
import pandas as pd

from src.config import (
    PROCESSED_DATA_DIR,
    CLEAN_DATASET_PATH,
    FUZZY_MATRIX_PATH,
    DISCRETIZED_DATASET_PATH,
    TARGET_COLUMN,
)
from src.data.loader import load_dataset, clean_dataset
from src.fuzzy.membership import trapmf, trimf, FUZZY_PARTITIONS


def fuzzify_dataframe(df: pd.DataFrame, include_target: bool = True) -> pd.DataFrame:
    """
    Evalúa cada fila del dataframe continuo en las funciones de pertenencia correspondientes.

    Genera la matriz difusa donde cada celda continua se expande en múltiples columnas
    con valores estrictamente acotados en [0.0, 1.0].
    """
    columns_to_fuzzify = list(FUZZY_PARTITIONS.keys())
    if not include_target:
        columns_to_fuzzify = [c for c in columns_to_fuzzify if c != TARGET_COLUMN]

    fuzzy_data = {}

    for var in columns_to_fuzzify:
        if var not in df.columns:
            continue

        x = df[var].to_numpy(dtype=float)
        partitions = FUZZY_PARTITIONS[var]

        for label, (kind, params) in partitions.items():
            col_name = f"{var}__{label}"
            if kind == "trap":
                mu = trapmf(x, params)
            elif kind == "tri":
                mu = trimf(x, params)
            else:
                raise ValueError(f"Tipo de función desconocida: {kind}")

            fuzzy_data[col_name] = np.round(mu, 4)

    fuzzy_matrix = pd.DataFrame(fuzzy_data, index=df.index)
    return fuzzy_matrix


def discretize_dataframe(df: pd.DataFrame, fuzzy_matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Discretiza el dataset asignando a cada variable continua la etiqueta lingüística 
    con mayor grado de pertenencia (criterio argmax / máxima pertenencia).

    Este dataset es el insumo directo para el algoritmo PRISM y el cálculo de LIFT.
    """
    discretized = pd.DataFrame(index=df.index)

    for var, partitions in FUZZY_PARTITIONS.items():
        if var not in df.columns:
            continue

        var_cols = [f"{var}__{label}" for label in partitions.keys()]
        subset = fuzzy_matrix[var_cols]
        winning_col = subset.idxmax(axis=1)
        winning_label = winning_col.apply(lambda col: col.split("__")[1])
        discretized[var] = winning_label

    return discretized


def main():
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("FASE DE FUZIFICACIÓN Y DISCRETIZACIÓN (SRC.FUZZY.FUZZIFIER)")
    print("=" * 70)

    # 1. Cargar y limpiar datos
    raw_df = load_dataset()
    clean_df = clean_dataset(raw_df)
    clean_df.to_csv(CLEAN_DATASET_PATH, index=False)
    print(f"Dataset limpio guardado en: {CLEAN_DATASET_PATH}")

    # 2. Generar Matriz Difusa
    fuzzy_matrix = fuzzify_dataframe(clean_df, include_target=True)
    fuzzy_matrix.to_csv(FUZZY_MATRIX_PATH, index=False)
    print(f"\nMatriz difusa generada:")
    print(f"  - Filas: {fuzzy_matrix.shape[0]}")
    print(f"  - Columnas difusas: {fuzzy_matrix.shape[1]}")
    print(f"  - Rango de valores: [{fuzzy_matrix.min().min()}, {fuzzy_matrix.max().max()}]")
    print(f"  - Archivo guardado en: {FUZZY_MATRIX_PATH}")

    # 3. Generar Dataset Discretizado
    discretized_df = discretize_dataframe(clean_df, fuzzy_matrix)
    discretized_df.to_csv(DISCRETIZED_DATASET_PATH, index=False)
    print(f"\nDataset discretizado (para PRISM) generado:")
    print(f"  - Filas: {discretized_df.shape[0]}")
    print(f"  - Columnas categóricas: {discretized_df.shape[1]}")
    print(f"  - Archivo guardado en: {DISCRETIZED_DATASET_PATH}")

    print("\nDistribución de la variable objetivo discretizada (compressive_strength):")
    print(discretized_df["compressive_strength"].value_counts(normalize=True).round(4) * 100)

    print("\n" + "=" * 70)
    print("PROCESO DE FUZIFICACIÓN COMPLETADO CON ÉXITO")
    print("=" * 70)


if __name__ == "__main__":
    main()
