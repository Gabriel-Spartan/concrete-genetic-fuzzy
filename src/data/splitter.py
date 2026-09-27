import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import (
    SPLITS_DIR,
    CLEAN_DATASET_PATH,
    FUZZY_MATRIX_PATH,
    DISCRETIZED_DATASET_PATH,
    TRAIN_DISCRETIZED_PATH,
    VAL_DISCRETIZED_PATH,
    TEST_DISCRETIZED_PATH,
    TRAIN_CLEAN_PATH,
    VAL_CLEAN_PATH,
    TEST_CLEAN_PATH,
    TRAIN_FUZZY_PATH,
    VAL_FUZZY_PATH,
    TEST_FUZZY_PATH,
    TABLES_DIR,
    TARGET_COLUMN,
)


def split_datasets(random_state: int = 42) -> dict[str, pd.DataFrame]:
    """
    Divide de forma estratificada los datasets (limpio, difuso y discretizado) en:
    - Entrenamiento: 70%
    - Validación: 15%
    - Prueba (Test): 15%

    Garantiza que la distribución de la variable objetivo sea homogénea
    en todas las particiones y sincronizada mediante los mismos índices.
    """
    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Cargar datasets procesados
    clean_df = pd.read_csv(CLEAN_DATASET_PATH)
    fuzzy_df = pd.read_csv(FUZZY_MATRIX_PATH)
    discretized_df = pd.read_csv(DISCRETIZED_DATASET_PATH)

    assert len(clean_df) == len(fuzzy_df) == len(discretized_df), "Los datasets procesados deben tener el mismo número de filas."

    # 2. Partición Estratificada sobre los índices
    target = discretized_df[TARGET_COLUMN]

    train_idx, temp_idx = train_test_split(
        discretized_df.index,
        test_size=0.30,
        random_state=random_state,
        stratify=target,
    )

    temp_target = target.loc[temp_idx]
    val_idx, test_idx = train_test_split(
        temp_idx,
        test_size=0.50,
        random_state=random_state,
        stratify=temp_target,
    )

    # 3. Separar cada dataset
    splits = {
        "train_discretized": discretized_df.loc[train_idx].reset_index(drop=True),
        "val_discretized": discretized_df.loc[val_idx].reset_index(drop=True),
        "test_discretized": discretized_df.loc[test_idx].reset_index(drop=True),

        "train_clean": clean_df.loc[train_idx].reset_index(drop=True),
        "val_clean": clean_df.loc[val_idx].reset_index(drop=True),
        "test_clean": clean_df.loc[test_idx].reset_index(drop=True),

        "train_fuzzy": fuzzy_df.loc[train_idx].reset_index(drop=True),
        "val_fuzzy": fuzzy_df.loc[val_idx].reset_index(drop=True),
        "test_fuzzy": fuzzy_df.loc[test_idx].reset_index(drop=True),
    }

    # 4. Guardar archivos CSV
    splits["train_discretized"].to_csv(TRAIN_DISCRETIZED_PATH, index=False)
    splits["val_discretized"].to_csv(VAL_DISCRETIZED_PATH, index=False)
    splits["test_discretized"].to_csv(TEST_DISCRETIZED_PATH, index=False)

    splits["train_clean"].to_csv(TRAIN_CLEAN_PATH, index=False)
    splits["val_clean"].to_csv(VAL_CLEAN_PATH, index=False)
    splits["test_clean"].to_csv(TEST_CLEAN_PATH, index=False)

    splits["train_fuzzy"].to_csv(TRAIN_FUZZY_PATH, index=False)
    splits["val_fuzzy"].to_csv(VAL_FUZZY_PATH, index=False)
    splits["test_fuzzy"].to_csv(TEST_FUZZY_PATH, index=False)

    # 5. Generar reporte resumen de estratificación
    summary = pd.DataFrame({
        "Train_Count": splits["train_discretized"][TARGET_COLUMN].value_counts(),
        "Train_Pct": (splits["train_discretized"][TARGET_COLUMN].value_counts(normalize=True) * 100).round(2),
        "Val_Count": splits["val_discretized"][TARGET_COLUMN].value_counts(),
        "Val_Pct": (splits["val_discretized"][TARGET_COLUMN].value_counts(normalize=True) * 100).round(2),
        "Test_Count": splits["test_discretized"][TARGET_COLUMN].value_counts(),
        "Test_Pct": (splits["test_discretized"][TARGET_COLUMN].value_counts(normalize=True) * 100).round(2),
    })
    summary.to_csv(TABLES_DIR / "splits_summary.csv")

    return splits, summary


def main():
    print("\n" + "=" * 70)
    print("DIVISIÓN ESTRATIFICADA DEL DATASET (70% TRAIN / 15% VAL / 15% TEST)")
    print("=" * 70)

    splits, summary = split_datasets(random_state=42)

    total = len(splits["train_clean"]) + len(splits["val_clean"]) + len(splits["test_clean"])
    print(f"Total registros: {total}")
    print(f"  - Train (70%): {len(splits['train_clean'])} filas")
    print(f"  - Val   (15%): {len(splits['val_clean'])} filas")
    print(f"  - Test  (15%): {len(splits['test_clean'])} filas")

    print("\nDistribución estratificada de la variable objetivo:")
    print(summary)

    print(f"\nArchivos guardados exitosamente en: {SPLITS_DIR}")
    print(f"Resumen de partición guardado en: {TABLES_DIR / 'splits_summary.csv'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
