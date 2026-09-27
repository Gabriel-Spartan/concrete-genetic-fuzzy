"""
Módulo de Generación de Visualizaciones Técnicas para la Evaluación Final del Sistema
Fuzzy-Genético (Fase 8).

Genera:
1. ga_convergence_curve.png: Curva generacional de convergencia (Train/Val RMSE y Val R²).
2. scatter_actual_vs_predicted_test.png: Diagrama de dispersión Real vs. Predicho en Test ciego (Baseline vs. AG).
3. fuzzy_membership_comparison_age.png: Comparativa de funciones de pertenencia antes vs. después para 'age'.
4. fuzzy_membership_comparison_cement.png: Comparativa de funciones de pertenencia antes vs. después para 'cement'.
5. fuzzy_membership_comparison_water.png: Comparativa de funciones de pertenencia antes vs. después para 'water'.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import (
    FIGURES_DIR,
    TABLES_DIR,
    TEST_CLEAN_PATH,
    TARGET_COLUMN,
)
from src.fuzzy.membership import FUZZY_PARTITIONS, trapmf, trimf
from src.fuzzy.inference import FuzzyInferenceSystem
from src.genetic.chromosome import (
    decode_chromosome,
    get_nominal_chromosome,
)


# Configuración estética general
plt.rcParams.update({
    "font.sans-serif": "DejaVu Sans",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 1.0,
    "grid.color": "#e0e0e0",
    "grid.linestyle": "--",
    "grid.linewidth": 0.7,
})


def plot_ga_convergence(history_csv: Path, output_file: Path) -> None:
    """Genera la gráfica de convergencia generacional del Algoritmo Genético."""
    df = pd.read_csv(history_csv)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Panel 1: RMSE
    ax1.plot(df["generation"], df["train_rmse_best"], label="Train RMSE Mejor (70%)", color="#1f77b4", linewidth=2.2)
    if "train_rmse_mean" in df.columns:
        ax1.plot(df["generation"], df["train_rmse_mean"], label="Train RMSE Promedio", color="#1f77b4", linestyle=":", alpha=0.6)
    ax1.plot(df["generation"], df["val_rmse"], label="Val RMSE (15%)", color="#ff7f0e", linewidth=2.2)

    # Identificar mejor generación en validación
    best_idx = df["val_rmse"].idxmin()
    best_gen = df.loc[best_idx, "generation"]
    best_val_rmse = df.loc[best_idx, "val_rmse"]
    stop_gen = df["generation"].max()

    ax1.scatter([best_gen], [best_val_rmse], color="#2ca02c", s=120, zorder=5,
                label=f"Óptimo Validación (Gen {best_gen}: {best_val_rmse:.2f} MPa)")
    ax1.axvline(best_gen, color="#2ca02c", linestyle=":", alpha=0.7)
    ax1.axvline(stop_gen, color="#d62728", linestyle="--", alpha=0.7,
                label=f"Parada Temprana (Early Stopping Gen {stop_gen})")

    ax1.set_ylabel("RMSE (MPa)", fontsize=12, fontweight="bold")
    ax1.set_title("Convergencia Generacional del Algoritmo Genético (Fuzzy Tuning)", fontsize=14, fontweight="bold", pad=12)
    ax1.grid(True)
    ax1.legend(loc="upper right", framealpha=0.9)

    # Panel 2: Val R²
    ax2.plot(df["generation"], df["val_r2"], label="Val R² (Coef. Determinación)", color="#9467bd", linewidth=2.0)
    best_val_r2 = df.loc[best_idx, "val_r2"]
    ax2.scatter([best_gen], [best_val_r2], color="#2ca02c", s=100, zorder=5,
                label=f"Mejor R² Val (Gen {best_gen}: {best_val_r2:.4f})")
    ax2.axvline(best_gen, color="#2ca02c", linestyle=":", alpha=0.7)
    ax2.axvline(stop_gen, color="#d62728", linestyle="--", alpha=0.7)

    ax2.set_xlabel("Generación", fontsize=12, fontweight="bold")
    ax2.set_ylabel("R² (Validación)", fontsize=12, fontweight="bold")
    ax2.grid(True)
    ax2.legend(loc="lower right", framealpha=0.9)

    plt.tight_layout()
    fig.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[Graficado] Curva de convergencia guardada en: {output_file}")


def plot_actual_vs_predicted_test(tuned_chrom: np.ndarray, output_file: Path) -> None:
    """Genera la comparativa de dispersión Real vs. Predicho sobre el conjunto ciego de Test."""
    test_df = pd.read_csv(TEST_CLEAN_PATH)
    y_true = test_df[TARGET_COLUMN].values

    fis = FuzzyInferenceSystem()

    # Predicción Línea Base (Nominal)
    nominal_chrom = get_nominal_chromosome()
    nom_parts, nom_cents = decode_chromosome(nominal_chrom)
    y_pred_base = fis.predict(test_df, partitions=nom_parts, centroids=nom_cents)
    m_base = fis.evaluate(test_df, partitions=nom_parts, centroids=nom_cents)

    # Predicción Sintonizado con AG
    tun_parts, tun_cents = decode_chromosome(tuned_chrom)
    y_pred_tuned = fis.predict(test_df, partitions=tun_parts, centroids=tun_cents)
    m_tuned = fis.evaluate(test_df, partitions=tun_parts, centroids=tun_cents)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

    lims = [0, 85]

    # Panel 1: Baseline
    ax1.scatter(y_true, y_pred_base, color="#1f77b4", alpha=0.7, edgecolors="none", s=45, label="Muestras Test")
    ax1.plot(lims, lims, color="#d62728", linestyle="--", linewidth=1.8, label="Ideal (y = x)")
    ax1.fill_between(lims, [l - 10 for l in lims], [l + 10 for l in lims], color="#d62728", alpha=0.08, label="Banda ±10 MPa")
    ax1.set_xlim(lims)
    ax1.set_ylim(lims)
    ax1.set_xlabel("Resistencia Real (MPa)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Resistencia Predicha (MPa)", fontsize=12, fontweight="bold")
    ax1.set_title(f"FIS Inicial (Línea Base)\nRMSE: {m_base['rmse']:.2f} MPa | R²: {m_base['r2']:.4f} | Cob: {m_base['coverage_pct']:.1f}%",
                  fontsize=12, fontweight="bold")
    ax1.grid(True)
    ax1.legend(loc="upper left")

    # Panel 2: Tuned
    ax2.scatter(y_true, y_pred_tuned, color="#2ca02c", alpha=0.7, edgecolors="none", s=45, label="Muestras Test")
    ax2.plot(lims, lims, color="#d62728", linestyle="--", linewidth=1.8, label="Ideal (y = x)")
    ax2.fill_between(lims, [l - 10 for l in lims], [l + 10 for l in lims], color="#d62728", alpha=0.08, label="Banda ±10 MPa")
    ax2.set_xlim(lims)
    ax2.set_ylim(lims)
    ax2.set_xlabel("Resistencia Real (MPa)", fontsize=12, fontweight="bold")
    ax2.set_title(f"FIS Sintonizado con AG (Propuesto)\nRMSE: {m_tuned['rmse']:.2f} MPa | R²: {m_tuned['r2']:.4f} | Cob: {m_tuned['coverage_pct']:.1f}%",
                  fontsize=12, fontweight="bold")
    ax2.grid(True)
    ax2.legend(loc="upper left")

    fig.suptitle("Evaluación sobre Conjunto Ciego de Prueba (15% Test - 151 Muestras)", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    fig.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[Graficado] Dispersión Test guardada en: {output_file}")


def _eval_mf(kind: str, params: list[float], x: np.ndarray) -> np.ndarray:
    """Evalúa una función de pertenencia sobre un vector numérico x."""
    if kind == "trap":
        return trapmf(x, params)
    elif kind == "tri":
        return trimf(x, params)
    return np.zeros_like(x)


def plot_membership_comparison(
    var_name: str,
    tuned_parts: dict,
    unit: str,
    output_file: Path,
) -> None:
    """Genera la comparativa gráfica de funciones de pertenencia antes vs. después para una variable."""
    nom_parts = FUZZY_PARTITIONS[var_name]
    tun_var_parts = tuned_parts[var_name]

    # Determinar rango x
    all_vals = []
    for l, (_, p) in nom_parts.items():
        all_vals.extend(p)
    x_min = min(all_vals)
    x_max = max(all_vals)
    x = np.linspace(x_min, x_max, 500)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    # Nominal
    for i, (label, (kind, p)) in enumerate(nom_parts.items()):
        if label == "no_aplica":
            continue
        y = _eval_mf(kind, p, x)
        color = colors[i % len(colors)]
        ax1.plot(x, y, label=label.replace("_", " ").title(), color=color, linewidth=2.0)
        ax1.fill_between(x, y, alpha=0.1, color=color)

    ax1.set_ylabel("Pertenencia μ", fontsize=11, fontweight="bold")
    ax1.set_title(f"Funciones de Pertenencia Iniciales (Nominales) - '{var_name}'", fontsize=12, fontweight="bold")
    ax1.set_ylim(-0.05, 1.05)
    ax1.grid(True)
    ax1.legend(loc="upper right", framealpha=0.9)

    # Sintonizadas
    for i, (label, (kind, p)) in enumerate(tun_var_parts.items()):
        if label == "no_aplica":
            continue
        y = _eval_mf(kind, p, x)
        color = colors[i % len(colors)]
        ax2.plot(x, y, label=label.replace("_", " ").title(), color=color, linewidth=2.0)
        ax2.fill_between(x, y, alpha=0.15, color=color)

    ax2.set_xlabel(f"{var_name.replace('_', ' ').title()} ({unit})", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Pertenencia μ", fontsize=11, fontweight="bold")
    ax2.set_title(f"Funciones de Pertenencia Sintonizadas con AG - '{var_name}'", fontsize=12, fontweight="bold")
    ax2.set_ylim(-0.05, 1.05)
    ax2.grid(True)
    ax2.legend(loc="upper right", framealpha=0.9)

    plt.tight_layout()
    fig.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[Graficado] Comparación de pertenencia para '{var_name}' guardada en: {output_file}")


def plot_all_memberships_grid(tuned_parts: dict, output_file: Path) -> None:
    """Genera una cuadrícula 4x2 con las funciones de pertenencia antes vs. después para las 8 variables."""
    var_units = [
        ("cement", "kg/m³"),
        ("blast_furnace_slag", "kg/m³"),
        ("fly_ash", "kg/m³"),
        ("water", "kg/m³"),
        ("superplasticizer", "kg/m³"),
        ("coarse_aggregate", "kg/m³"),
        ("fine_aggregate", "kg/m³"),
        ("age", "días"),
    ]

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

    fig, axes = plt.subplots(4, 2, figsize=(16, 16))
    axes = axes.flatten()

    for idx, (var_name, unit) in enumerate(var_units):
        ax = axes[idx]
        nom_parts = FUZZY_PARTITIONS[var_name]
        tun_var_parts = tuned_parts[var_name]

        all_vals = []
        for _, (_, p) in nom_parts.items():
            all_vals.extend(p)
        x_min = min(all_vals)
        x_max = max(all_vals)
        x = np.linspace(x_min, x_max, 400)

        # Graficar cada etiqueta
        lbl_idx = 0
        for label, (kind, p_nom) in nom_parts.items():
            if label == "no_aplica":
                continue
            color = colors[lbl_idx % len(colors)]
            lbl_name = label.replace("_", " ").title()

            # Curva inicial (Línea Base: punteada)
            y_nom = _eval_mf(kind, p_nom, x)
            ax.plot(x, y_nom, color=color, linestyle="--", linewidth=1.5, alpha=0.45)

            # Curva sintonizada (AG: continua)
            _, p_tun = tun_var_parts[label]
            y_tun = _eval_mf(kind, p_tun, x)
            ax.plot(x, y_tun, color=color, linestyle="-", linewidth=2.2, label=f"{lbl_name}")
            ax.fill_between(x, y_tun, alpha=0.10, color=color)

            lbl_idx += 1

        ax.set_title(f"{var_name.replace('_', ' ').title()} ({unit})", fontsize=11, fontweight="bold", pad=8)
        ax.set_ylim(-0.05, 1.05)
        ax.set_ylabel("μ(x)", fontsize=10)
        ax.grid(True)
        ax.legend(loc="upper right", fontsize=8, framealpha=0.85)

    # Subtítulo explicativo
    fig.suptitle(
        "Funciones de Pertenencia Iniciales (Líneas Punteadas) vs. Sintonizadas con AG (Líneas Continuas)",
        fontsize=14,
        fontweight="bold",
        y=0.995,
    )
    plt.tight_layout()
    fig.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[Graficado] Cuadrícula integral de 8 variables guardada en: {output_file}")


def generate_all_plots() -> None:
    """Ejecuta la generación completa de las figuras de la evaluación final."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    history_csv = TABLES_DIR / "ga_convergence_history.csv"
    tuned_csv = TABLES_DIR / "tuned_parameters_summary.csv"

    if not history_csv.exists() or not tuned_csv.exists():
        raise FileNotFoundError("Debe ejecutar primero el algoritmo genético (python -m src.genetic) antes de graficar.")

    # Cargar cromosoma óptimo desde tuned_parameters_summary.csv
    tuned_df = pd.read_csv(tuned_csv)
    tuned_chrom = tuned_df["Valor_Sintonizado"].values
    tun_parts, _ = decode_chromosome(tuned_chrom)

    print("\n" + "=" * 80)
    print("GENERACIÓN DE FIGURAS Y REPORTES VISUALES (PASO 4 / FASE 8)")
    print("=" * 80)

    # 1. Curva de convergencia
    plot_ga_convergence(history_csv, FIGURES_DIR / "ga_convergence_curve.png")

    # 2. Scatter Real vs Predicho en Test
    plot_actual_vs_predicted_test(tuned_chrom, FIGURES_DIR / "scatter_actual_vs_predicted_test.png")

    # 3. Comparativa de funciones de pertenencia para variables clave
    plot_membership_comparison("age", tun_parts, "días", FIGURES_DIR / "fuzzy_membership_comparison_age.png")
    plot_membership_comparison("cement", tun_parts, "kg/m³", FIGURES_DIR / "fuzzy_membership_comparison_cement.png")
    plot_membership_comparison("water", tun_parts, "kg/m³", FIGURES_DIR / "fuzzy_membership_comparison_water.png")

    # 4. Cuadrícula completa de las 8 variables de entrada
    plot_all_memberships_grid(tun_parts, FIGURES_DIR / "fuzzy_membership_comparison_all_variables.png")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    generate_all_plots()
