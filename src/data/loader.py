import pandas as pd

from src.config import DATASET_PATH, COLUMN_NAMES


def load_dataset() -> pd.DataFrame:
    """
    Carga el dataset de resistencia a la compresión del concreto.

    Returns
    -------
    pandas.DataFrame
        Dataset con nombres de columnas simplificados en snake_case.

    Raises
    ------
    FileNotFoundError
        Si no existe data/raw/dataset.csv.
    ValueError
        Si el número de columnas no coincide con las 9 esperadas.
    """
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el dataset en: {DATASET_PATH}"
        )

    df = pd.read_csv(DATASET_PATH)

    if df.shape[1] != 9:
        raise ValueError(
            f"Se esperaban 9 columnas, pero se encontraron {df.shape[1]}."
        )

    df.columns = COLUMN_NAMES
    return df


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina los duplicados exactos identificados en la fase de calidad (25 registros).
    Conserva los valores continuos reales y el significado físico de ceros y outliers.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataset original.

    Returns
    -------
    pandas.DataFrame
        Dataset limpio sin duplicados exactos.
    """
    initial_count = len(df)
    clean_df = df.drop_duplicates().reset_index(drop=True)
    dropped = initial_count - len(clean_df)
    print(f"Limpieza de datos: {initial_count} filas originales -> {dropped} duplicados eliminados -> {len(clean_df)} filas conservadas.")
    return clean_df
