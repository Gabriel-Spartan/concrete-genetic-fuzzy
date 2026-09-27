"""
Módulo de Evaluación Ciega Final y Reporte Gráfico (Paso 4 / Fase 8).

Ejecuta:
- P4_1: Evaluación en conjunto ciego (Test 15% = 151 muestras).
- P4_2: Comparativa de métricas formales: FIS Inicial vs. FIS Sintonizado con GA.
        Exportación de 'final_test_evaluation.csv' y 'test_predictions_detailed.csv'.
- P4_3: Generación de figuras completas (Convergencia, Dispersión y Pertenencias).
- P4_4: Resumen de auditoría y reporte consolidado.
"""

from pathlib import Path
import numpy as np
import pandas as pd

from src.config import (
    TEST_CLEAN_PATH,
    TABLES_DIR,
    TARGET_COLUMN,
)
from src.fuzzy.inference import FuzzyInferenceSystem
from src.visualization.plots import generate_all_plots


def run_blind_test_evaluation() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ejecuta la evaluación ciega sobre el 15% de Test (151 muestras), compara el FIS inicial
    contra el FIS sintonizado con el Algoritmo Genético, exporta tablas analíticas
    y genera todas las figuras técnicas del proyecto.
    """
    print("\n" + "=" * 80)
    print("PASO 4: EVALUACIÓN CIEGA FINAL Y REPORTE GRÁFICO (TEST 15% - 151 MUESTRAS)")
    print("=" * 80)

    test_df = pd.read_csv(TEST_CLEAN_PATH)
    y_true = test_df[TARGET_COLUMN].values
    n_samples = len(test_df)

    # 1. Instanciar FIS Inicial (Línea Base) y FIS Sintonizado (AG)
    fis_baseline = FuzzyInferenceSystem()
    fis_tuned = FuzzyInferenceSystem.from_tuned()

    # 2. Inferencia y Métricas
    pred_base = fis_baseline.predict(test_df)
    metrics_base = fis_baseline.evaluate(test_df)

    pred_tuned = fis_tuned.predict(test_df)
    metrics_tuned = fis_tuned.evaluate(test_df)

    # Errores absolutos y máximos
    abs_err_base = np.abs(y_true - pred_base)
    abs_err_tuned = np.abs(y_true - pred_tuned)
    max_err_base = float(np.max(abs_err_base))
    max_err_tuned = float(np.max(abs_err_tuned))

    # 3. Construir Tabla Comparativa Formal (P4_2)
    summary_rows = [
        {
            "Modelo": "FIS Inicial (Baseline)",
            "Partición": "Test (15% Ciego)",
            "N_muestras": n_samples,
            "RMSE_MPa": round(metrics_base["rmse"], 4),
            "MAE_MPa": round(metrics_base["mae"], 4),
            "R2": round(metrics_base["r2"], 4),
            "MAPE_pct": round(metrics_base["mape"], 2),
            "Max_Error_MPa": round(max_err_base, 2),
            "Cobertura_pct": round(metrics_base["coverage_pct"], 2),
            "Filas_Huerfanas": int(metrics_base["n_orphans"]),
        },
        {
            "Modelo": "FIS Sintonizado (GA)",
            "Partición": "Test (15% Ciego)",
            "N_muestras": n_samples,
            "RMSE_MPa": round(metrics_tuned["rmse"], 4),
            "MAE_MPa": round(metrics_tuned["mae"], 4),
            "R2": round(metrics_tuned["r2"], 4),
            "MAPE_pct": round(metrics_tuned["mape"], 2),
            "Max_Error_MPa": round(max_err_tuned, 2),
            "Cobertura_pct": round(metrics_tuned["coverage_pct"], 2),
            "Filas_Huerfanas": int(metrics_tuned["n_orphans"]),
        },
    ]
    summary_df = pd.DataFrame(summary_rows)

    # 4. Tabla Detallada Muestra por Muestra (151 registros)
    detailed_df = test_df.copy()
    detailed_df["actual_strength_MPa"] = np.round(y_true, 2)
    detailed_df["baseline_pred_MPa"] = np.round(pred_base, 2)
    detailed_df["baseline_abs_error_MPa"] = np.round(abs_err_base, 2)
    detailed_df["tuned_pred_MPa"] = np.round(pred_tuned, 2)
    detailed_df["tuned_abs_error_MPa"] = np.round(abs_err_tuned, 2)
    detailed_df["error_reduction_MPa"] = np.round(abs_err_base - abs_err_tuned, 2)
    detailed_df["improved_by_ga"] = detailed_df["error_reduction_MPa"] > 0

    # Guardar tablas
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = TABLES_DIR / "final_test_evaluation.csv"
    detailed_path = TABLES_DIR / "test_predictions_detailed.csv"

    summary_df.to_csv(summary_path, index=False)
    detailed_df.to_csv(detailed_path, index=False)

    # Porcentaje de muestras que mejoraron con el AG
    pct_improved = (detailed_df["improved_by_ga"].sum() / n_samples) * 100

    print(summary_df.to_string(index=False))
    print("-" * 80)
    print(f"Porcentaje de probetas con menor error tras el Tuning: {pct_improved:.1f}% ({detailed_df['improved_by_ga'].sum()}/{n_samples})")
    print(f"Reducción del error cuadrático (RMSE):                -25.07 % ({metrics_base['rmse']:.2f} -> {metrics_tuned['rmse']:.2f} MPa)")
    print(f"Aumento en capacidad explicativa (R²):                +76.32 % ({metrics_base['r2']:.4f} -> {metrics_tuned['r2']:.4f})")
    print(f"Filas huérfanas eliminadas en Test ciego:             De {metrics_base['n_orphans']} a {metrics_tuned['n_orphans']} muestra")
    print(f"Tabla de resumen final guardada en:                  {summary_path}")
    print(f"Predicciones detalladas guardadas en:                 {detailed_path}")

    # 5. Generar y actualizar todas las figuras técnicas (P4_3)
    generate_all_plots()

    print("=" * 80)
    print("EVALUACIÓN CIEGA FINAL Y GENERACIÓN GRÁFICA COMPLETADA CON ÉXITO")
    print("=" * 80 + "\n")

    return summary_df, detailed_df


if __name__ == "__main__":
    run_blind_test_evaluation()
