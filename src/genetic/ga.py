"""
Módulo Principal del Algoritmo Genético para Fuzzy Tuning (Sintonización Paramétrica).

Implementa:
- Población real con individuo semilla nominal (garantía de no degradación).
- Cruce BLX-alpha y mutación Gaussiana acotada con operador de reparación activa.
- Selección por torneo y elitismo estricto.
- Monitoreo en Validación (15%) y Early Stopping para control de sobreajuste.
- Exportación de curvas de convergencia y comparación formal Baseline vs Sintonizado.
"""

from pathlib import Path
import json
import time
import numpy as np
import pandas as pd

from src.config import TABLES_DIR
from src.genetic.chromosome import (
    get_nominal_chromosome,
    decode_chromosome,
    GENE_SPECS,
)
from src.genetic.operators import (
    repair_chromosome,
    crossover_blx_alpha,
    mutate_gaussian,
    tournament_selection,
)
from src.genetic.fitness import FuzzyFitnessEvaluator


class GeneticFuzzyTuner:
    """
    Optimizador evolutivo para funciones de pertenencia y consecuentes continuos.
    """

    def __init__(
        self,
        population_size: int = 50,
        n_generations: int = 50,
        crossover_prob: float = 0.85,
        mutation_prob: float = 0.20,
        mutation_rate: float = 0.15,
        sigma_scale: float = 0.05,
        alpha: float = 0.3,
        tournament_size: int = 3,
        elite_size: int = 2,
        early_stopping_patience: int = 15,
        random_state: int = 42,
    ):
        self.population_size = population_size
        self.n_generations = n_generations
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.mutation_rate = mutation_rate
        self.sigma_scale = sigma_scale
        self.alpha = alpha
        self.tournament_size = tournament_size
        self.elite_size = elite_size
        self.early_stopping_patience = early_stopping_patience
        self.random_state = random_state

        self.evaluator = FuzzyFitnessEvaluator()

    def _initialize_population(self) -> list[np.ndarray]:
        """
        Inicializa la población incluyendo el individuo nominal (línea base)
        y variantes perturbadas con reparación activa.
        """
        nominal = get_nominal_chromosome()
        population = [nominal.copy()]

        for _ in range(self.population_size - 1):
            noise = np.random.normal(0.0, 0.08 * (nominal + 1.0))
            candidate = nominal + noise
            repaired = repair_chromosome(candidate)
            population.append(repaired)

        return population

    def run(self) -> tuple[np.ndarray, pd.DataFrame, pd.DataFrame]:
        """
        Ejecuta el bucle evolutivo completo.

        Returns
        -------
        best_chromosome : np.ndarray
            El mejor cromosoma sintonizado (con menor error en validación).
        history_df : pd.DataFrame
            Registro generacional de convergencia.
        comparison_df : pd.DataFrame
            Comparación de métricas: Línea Base Inicial vs. Sistema Sintonizado con AG.
        """
        np.random.seed(self.random_state)
        t_start = time.time()

        print("\n" + "=" * 80)
        print("ALGORITMO GENÉTICO - SINTONIZACIÓN DE FUNCIONES DIFUSAS (FUZZY TUNING)")
        print("=" * 80)
        print(f"Población:           {self.population_size} individuos")
        print(f"Generaciones Máx:    {self.n_generations}")
        print(f"Prob. Cruce (BLX-a): {self.crossover_prob} (alpha={self.alpha})")
        print(f"Prob. Mutación:      {self.mutation_prob} (tasa={self.mutation_rate}, sigma={self.sigma_scale})")
        print(f"Elitismo:            {self.elite_size} individuos")
        print(f"Paciencia Early Stop:{self.early_stopping_patience} generaciones")
        print("-" * 80)

        population = self._initialize_population()

        nominal_chrom = get_nominal_chromosome()
        baseline_train_rmse = self.evaluator.evaluate_rmse(nominal_chrom, "train")
        baseline_val_rmse = self.evaluator.evaluate_rmse(nominal_chrom, "val")
        print(f"Línea Base Inicial: Train RMSE = {baseline_train_rmse:.4f} MPa | Val RMSE = {baseline_val_rmse:.4f} MPa")
        print("-" * 80)

        best_overall_chrom = nominal_chrom.copy()
        best_overall_val_rmse = baseline_val_rmse
        best_overall_gen = 0
        patience_counter = 0
        history = []

        for gen in range(self.n_generations):
            # 1. Evaluar población en Train
            train_scores = self.evaluator.evaluate_population(population, "train")

            # 2. Identificar el mejor de la generación
            best_gen_idx = int(np.argmin(train_scores))
            best_gen_train_rmse = float(train_scores[best_gen_idx])
            best_gen_chrom = population[best_gen_idx]

            # 3. Evaluar el mejor de la generación en Validación
            best_gen_val_rmse = self.evaluator.evaluate_rmse(best_gen_chrom, "val")
            val_metrics = self.evaluator.get_full_metrics(best_gen_chrom, "val")

            history.append({
                "generation": gen + 1,
                "train_rmse_best": round(best_gen_train_rmse, 4),
                "train_rmse_mean": round(float(np.mean(train_scores)), 4),
                "val_rmse": round(best_gen_val_rmse, 4),
                "val_r2": round(val_metrics["r2"], 4),
                "val_mae": round(val_metrics["mae"], 4),
                "val_coverage_pct": val_metrics["coverage_pct"],
            })

            # Monitoreo de mejora en Validación
            if best_gen_val_rmse < best_overall_val_rmse:
                best_overall_val_rmse = best_gen_val_rmse
                best_overall_chrom = best_gen_chrom.copy()
                best_overall_gen = gen + 1
                patience_counter = 0
                improvement_flag = "(*)"
            else:
                patience_counter += 1
                improvement_flag = "   "

            if (gen + 1) % 5 == 0 or gen == 0 or improvement_flag.strip():
                print(f"Gen {gen + 1:2d}/{self.n_generations} | "
                      f"Train RMSE: {best_gen_train_rmse:.4f} MPa | "
                      f"Val RMSE: {best_gen_val_rmse:.4f} MPa {improvement_flag}| "
                      f"Val R²: {val_metrics['r2']:.4f} | "
                      f"Paciencia: {patience_counter}/{self.early_stopping_patience}")

            # Control de parada temprana
            if patience_counter >= self.early_stopping_patience:
                print(f"\n[Early Stopping] Detenido en generación {gen + 1}. "
                      f"Mejor desempeño en Validación alcanzado en generación {best_overall_gen} (Val RMSE: {best_overall_val_rmse:.4f} MPa).")
                break

            # 4. Elitismo: conservar los mejores individuos
            sorted_indices = np.argsort(train_scores)
            new_population = [population[i].copy() for i in sorted_indices[: self.elite_size]]

            # 5. Generar nueva descendencia
            while len(new_population) < self.population_size:
                p1 = tournament_selection(population, train_scores, self.tournament_size)
                p2 = tournament_selection(population, train_scores, self.tournament_size)

                # Cruce
                if np.random.rand() < self.crossover_prob:
                    c1, c2 = crossover_blx_alpha(p1, p2, alpha=self.alpha)
                else:
                    c1, c2 = p1.copy(), p2.copy()

                # Mutación
                if np.random.rand() < self.mutation_prob:
                    c1 = mutate_gaussian(c1, self.mutation_rate, self.sigma_scale)
                if np.random.rand() < self.mutation_prob:
                    c2 = mutate_gaussian(c2, self.mutation_rate, self.sigma_scale)

                new_population.append(c1)
                if len(new_population) < self.population_size:
                    new_population.append(c2)

            population = new_population

        elapsed = time.time() - t_start

        # 6. Evaluación final comparativa (Línea Base vs. Optimizado con AG)
        print("\n" + "=" * 80)
        print("COMPARACIÓN FINAL: LÍNEA BASE INICIAL vs. SISTEMA SINTONIZADO CON AG")
        print("=" * 80)

        # Baseline metrics
        b_train = self.evaluator.get_full_metrics(nominal_chrom, "train")
        b_val = self.evaluator.get_full_metrics(nominal_chrom, "val")
        b_test = self.evaluator.get_full_metrics(nominal_chrom, "test")

        # Tuned metrics
        t_train = self.evaluator.get_full_metrics(best_overall_chrom, "train")
        t_val = self.evaluator.get_full_metrics(best_overall_chrom, "val")
        t_test = self.evaluator.get_full_metrics(best_overall_chrom, "test")

        comparison_rows = [
            {"Modelo": "FIS Inicial (Baseline)", "Partición": "Train (70%)", **b_train},
            {"Modelo": "FIS Sintonizado (GA)",   "Partición": "Train (70%)", **t_train},
            {"Modelo": "FIS Inicial (Baseline)", "Partición": "Val (15%)",   **b_val},
            {"Modelo": "FIS Sintonizado (GA)",   "Partición": "Val (15%)",   **t_val},
            {"Modelo": "FIS Inicial (Baseline)", "Partición": "Test (15%)",  **b_test},
            {"Modelo": "FIS Sintonizado (GA)",   "Partición": "Test (15%)",  **t_test},
        ]
        comparison_df = pd.DataFrame(comparison_rows)

        print(comparison_df[["Modelo", "Partición", "rmse", "mae", "r2", "coverage_pct"]].to_string(index=False))
        print("-" * 80)
        print(f"Tiempo total de evolución: {elapsed:.2f} s (Generación óptima: {best_overall_gen})")

        # 7. Guardar tablas
        TABLES_DIR.mkdir(parents=True, exist_ok=True)
        history_df = pd.DataFrame(history)
        history_path = TABLES_DIR / "ga_convergence_history.csv"
        comparison_path = TABLES_DIR / "ga_tuning_comparison.csv"
        history_df.to_csv(history_path, index=False)
        comparison_df.to_csv(comparison_path, index=False)

        # Guardar diccionario de parámetros sintonizados
        best_parts, best_cents = decode_chromosome(best_overall_chrom)
        tuned_summary = []
        for i, spec in enumerate(GENE_SPECS):
            nominal_val = spec["nominal"]
            tuned_val = best_overall_chrom[i]
            delta = tuned_val - nominal_val
            tuned_summary.append({
                "Tipo": spec["type"],
                "Variable": spec["var"],
                "Etiqueta": spec["label"],
                "Parámetro": spec["param_name"],
                "Valor_Nominal": round(nominal_val, 4),
                "Valor_Sintonizado": round(tuned_val, 4),
                "Diferencia": round(delta, 4),
            })
        tuned_df = pd.DataFrame(tuned_summary)
        tuned_path = TABLES_DIR / "tuned_parameters_summary.csv"
        tuned_df.to_csv(tuned_path, index=False)

        # Exportar mejor individuo completo en JSON para inferencia directa
        json_path = TABLES_DIR / "best_individual_fis.json"
        best_model_data = {
            "metadata": {
                "description": "Mejor individuo sintonizado mediante Algoritmo Genético (Fuzzy Tuning)",
                "optimal_generation": int(best_overall_gen),
                "total_generations_run": int(len(history)),
                "elapsed_seconds": round(elapsed, 2),
                "population_size": self.population_size,
                "early_stopping_patience": self.early_stopping_patience,
                "dataset_samples": {
                    "train": int(len(self.evaluator.train_df)),
                    "val": int(len(self.evaluator.val_df)),
                    "test": int(len(self.evaluator.test_df)),
                },
            },
            "performance_metrics": {
                "train": {k: round(float(v), 4) for k, v in t_train.items()},
                "val": {k: round(float(v), 4) for k, v in t_val.items()},
                "test": {k: round(float(v), 4) for k, v in t_test.items()},
            },
            "class_centroids": {k: round(float(v), 4) for k, v in best_cents.items()},
            "fuzzy_partitions": {
                var: {
                    lbl: {
                        "type": kind,
                        "params": [round(float(p), 4) for p in params],
                    }
                    for lbl, (kind, params) in var_dict.items()
                }
                for var, var_dict in best_parts.items()
            },
            "raw_chromosome": [round(float(g), 6) for g in best_overall_chrom],
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(best_model_data, f, indent=2, ensure_ascii=False)

        print(f"Historial de convergencia guardado en: {history_path}")
        print(f"Comparación de métricas guardada en:    {comparison_path}")
        print(f"Parámetros sintonizados guardados en:   {tuned_path}")
        print(f"Modelo JSON del mejor individuo en:     {json_path}")
        print("=" * 80 + "\n")

        return best_overall_chrom, history_df, comparison_df


def main():
    tuner = GeneticFuzzyTuner(
        population_size=60,
        n_generations=60,
        crossover_prob=0.85,
        mutation_prob=0.25,
        mutation_rate=0.15,
        sigma_scale=0.06,
        alpha=0.3,
        tournament_size=3,
        elite_size=2,
        early_stopping_patience=15,
        random_state=42,
    )
    tuner.run()


if __name__ == "__main__":
    main()
