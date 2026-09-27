import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.config import (
    FIGURES_DIR,
    TABLES_DIR,
    INPUT_COLUMNS,
    TARGET_COLUMN,
)
from src.data.loader import load_dataset


# ------------------------------------------------------------
# FUNCIONES AUXILIARES
# ------------------------------------------------------------

def prepare_output_directories():
    """Crea las carpetas de salida si todavía no existen."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)


def save_current_figure(filename: str):
    """
    Guarda la figura actual en results/figures/.

    Parameters
    ----------
    filename : str
        Nombre del archivo PNG.
    """
    output_path = FIGURES_DIR / filename
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()


# ------------------------------------------------------------
# 1. INFORMACIÓN GENERAL
# ------------------------------------------------------------

def basic_information(df: pd.DataFrame):
    """Muestra la estructura y las primeras observaciones del dataset."""
    print("\n" + "=" * 70)
    print("1. INFORMACIÓN GENERAL")
    print("=" * 70)

    print(f"Filas: {df.shape[0]}")
    print(f"Columnas: {df.shape[1]}")

    print("\nPrimeros 5 registros:")
    print(df.head())

    print("\nTipos de datos:")
    print(df.dtypes)


# ------------------------------------------------------------
# 2. CALIDAD DE DATOS
# ------------------------------------------------------------

def data_quality(df: pd.DataFrame):
    """Analiza valores faltantes y registros duplicados."""
    print("\n" + "=" * 70)
    print("2. CALIDAD DE DATOS")
    print("=" * 70)

    missing = df.isnull().sum()
    print("\nValores faltantes por columna:")
    print(missing)
    print(f"\nTotal de valores faltantes: {missing.sum()}")

    duplicated = df.duplicated().sum()
    print(f"Registros completamente duplicados: {duplicated}")

    quality_table = pd.DataFrame({
        "missing_values": missing,
        "missing_percentage": (missing / len(df)) * 100,
    })

    quality_table.to_csv(TABLES_DIR / "data_quality.csv")


# ------------------------------------------------------------
# 3. ESTADÍSTICA DESCRIPTIVA
# ------------------------------------------------------------

def descriptive_statistics(df: pd.DataFrame):
    """Genera estadísticas descriptivas y asimetría."""
    print("\n" + "=" * 70)
    print("3. ESTADÍSTICA DESCRIPTIVA")
    print("=" * 70)

    descriptive = df.describe().T
    descriptive["skewness"] = df.skew()
    descriptive["range"] = descriptive["max"] - descriptive["min"]

    print(descriptive)
    descriptive.to_csv(TABLES_DIR / "descriptive_statistics.csv")


# ------------------------------------------------------------
# 4. HISTOGRAMAS
# ------------------------------------------------------------

def plot_histograms(df: pd.DataFrame):
    """Genera un histograma individual para cada variable."""
    for column in df.columns:
        plt.figure(figsize=(8, 5))
        plt.hist(df[column], bins=30, edgecolor="black", alpha=0.75)
        plt.title(f"Distribución de {column}")
        plt.xlabel(column)
        plt.ylabel("Frecuencia")
        save_current_figure(f"histogram_{column}.png")


# ------------------------------------------------------------
# 5. BOXPLOTS
# ------------------------------------------------------------

def plot_boxplots(df: pd.DataFrame):
    """Genera boxplots individuales por variable."""
    for column in df.columns:
        plt.figure(figsize=(8, 4))
        plt.boxplot(df[column], vert=False)
        plt.title(f"Boxplot de {column}")
        plt.xlabel(column)
        save_current_figure(f"boxplot_{column}.png")


# ------------------------------------------------------------
# 6. CORRELACIONES
# ------------------------------------------------------------

def correlation_analysis(df: pd.DataFrame):
    """Calcula correlaciones de Pearson y Spearman."""
    print("\n" + "=" * 70)
    print("4. CORRELACIONES")
    print("=" * 70)

    pearson = df.corr(method="pearson")
    spearman = df.corr(method="spearman")

    pearson.to_csv(TABLES_DIR / "correlation_pearson.csv")
    spearman.to_csv(TABLES_DIR / "correlation_spearman.csv")

    print("\nPearson respecto a la resistencia:")
    print(pearson[TARGET_COLUMN].drop(TARGET_COLUMN).sort_values(ascending=False))

    print("\nSpearman respecto a la resistencia:")
    print(spearman[TARGET_COLUMN].drop(TARGET_COLUMN).sort_values(ascending=False))

    plt.figure(figsize=(10, 8))
    matrix = plt.imshow(pearson, aspect="auto")
    plt.colorbar(matrix)

    ticks = np.arange(len(pearson.columns))
    plt.xticks(ticks, pearson.columns, rotation=90)
    plt.yticks(ticks, pearson.columns)
    plt.title("Matriz de correlación de Pearson")
    save_current_figure("correlation_matrix_pearson.png")


# ------------------------------------------------------------
# 7. DISPERSIÓN DE VARIABLES VS RESISTENCIA
# ------------------------------------------------------------

def plot_scatter_against_target(df: pd.DataFrame):
    """Grafica cada entrada frente a la resistencia a compresión."""
    for column in INPUT_COLUMNS:
        plt.figure(figsize=(8, 5))
        plt.scatter(df[column], df[TARGET_COLUMN], alpha=0.55, s=22)
        plt.xlabel(column)
        plt.ylabel("Compressive Strength (MPa)")
        plt.title(f"{column} vs. resistencia a la compresión")
        save_current_figure(f"scatter_{column}_vs_strength.png")


# ------------------------------------------------------------
# 8. RELACIÓN AGUA / CEMENTO
# ------------------------------------------------------------

def analyze_water_cement_ratio(df: pd.DataFrame):
    """Analiza la variable derivada relación agua/cemento."""
    analysis_df = df.copy()
    analysis_df["water_cement_ratio"] = analysis_df["water"] / analysis_df["cement"]

    print("\n" + "=" * 70)
    print("5. RELACIÓN AGUA/CEMENTO")
    print("=" * 70)

    print(analysis_df["water_cement_ratio"].describe())

    correlation = analysis_df[["water_cement_ratio", TARGET_COLUMN]].corr()
    print("\nCorrelación con la resistencia:")
    print(correlation)

    plt.figure(figsize=(8, 5))
    plt.scatter(analysis_df["water_cement_ratio"], analysis_df[TARGET_COLUMN], alpha=0.55, s=22)
    plt.xlabel("Water/Cement Ratio")
    plt.ylabel("Compressive Strength (MPa)")
    plt.title("Relación agua/cemento vs. resistencia")
    save_current_figure("scatter_water_cement_ratio_vs_strength.png")


# ------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ------------------------------------------------------------

def main():
    """Ejecuta el análisis exploratorio completo."""
    prepare_output_directories()
    df = load_dataset()

    basic_information(df)
    data_quality(df)
    descriptive_statistics(df)
    plot_histograms(df)
    plot_boxplots(df)
    correlation_analysis(df)
    plot_scatter_against_target(df)
    analyze_water_cement_ratio(df)

    print("\n" + "=" * 70)
    print("ANÁLISIS FINALIZADO")
    print("=" * 70)
    print(f"Figuras guardadas en: {FIGURES_DIR}")
    print(f"Tablas guardadas en: {TABLES_DIR}")


if __name__ == "__main__":
    main()
