from pathlib import Path
import numpy as np
import pandas as pd

from src.config import (
    TRAIN_CLEAN_PATH,
    VAL_CLEAN_PATH,
    TEST_CLEAN_PATH,
    TABLES_DIR,
    TARGET_COLUMN,
)
from src.fuzzy.membership import trapmf, trimf, FUZZY_PARTITIONS


# ---------------------------------------------------------------------------
# CENTROIDES POR DEFECTO PARA CONSECUENTES (VALORES EN MPa)
# ---------------------------------------------------------------------------
# Basados en las medias empíricas de cada clase en el set de entrenamiento
# (también calibrados con las normas ACI 318 / EN 206).
DEFAULT_CLASS_CENTROIDS = {
    "baja": 13.90,        # < 20 MPa (Media en train: 13.90 MPa)
    "media_baja": 28.47,  # 20 - 35 MPa (Media en train: 28.47 MPa)
    "media_alta": 41.02,  # 35 - 50 MPa (Media en train: 41.02 MPa)
    "alta": 59.97,        # > 50 MPa (Media en train: 59.97 MPa)
}

# Límites normativos estrictos para sintonización con Algoritmos Genéticos
CENTROID_BOUNDS = {
    "baja": (5.0, 20.0),
    "media_baja": (20.0, 35.0),
    "media_alta": (35.0, 50.0),
    "alta": (50.0, 75.0),
}


class FuzzyInferenceSystem:
    """
    Motor de Inferencia Difuso (FIS) tipo Mamdani / TSK de orden cero para la predicción
    continua de la resistencia a la compresión del concreto (MPa).

    Características de robustez y diseño:
    1. Evaluación vectorizada de antecedentes con operadores T-norma ('min' o 'prod').
    2. Mecanismo de escape para 'filas huérfanas': si sum(w_k) <= epsilon, asigna
       el valor default_y (media global en Train), evitando NaN y división por cero.
    3. Centroides de consecuentes (y_k*) completamente parametrizables e integrables
       con el Algoritmo Genético.
    4. Cálculo de métricas de cobertura y error continuo (RMSE, MAE, R², MAPE).
    """

    def __init__(
        self,
        rules_path: str | Path | None = None,
        fuzzy_partitions: dict | None = None,
        class_centroids: dict | None = None,
        default_y: float = 35.335,  # Media global de compressive_strength en train
        t_norm: str = "min",
        epsilon: float = 1e-6,
    ):
        if rules_path is None:
            rules_path = TABLES_DIR / "rules_consolidated.csv"
        self.rules_path = Path(rules_path)

        if not self.rules_path.exists():
            raise FileNotFoundError(f"Archivo de reglas no encontrado en: {self.rules_path}")

        self.rules_df = pd.read_csv(self.rules_path)
        self.rules = self._parse_rules(self.rules_df)

        self.fuzzy_partitions = fuzzy_partitions if fuzzy_partitions is not None else FUZZY_PARTITIONS
        self.class_centroids = class_centroids if class_centroids is not None else DEFAULT_CLASS_CENTROIDS.copy()
        self.default_y = float(default_y)
        self.t_norm = t_norm.lower()
        self.epsilon = float(epsilon)

        if self.t_norm not in ["min", "prod"]:
            raise ValueError(f"T-norma no soportada: {t_norm}. Opciones: 'min' o 'prod'.")

    @classmethod
    def from_tuned(cls, json_path: str | Path | None = None, **kwargs) -> "FuzzyInferenceSystem":
        """
        Instancia el Motor de Inferencia cargando los parámetros sintonizados del mejor
        individuo producido por el Algoritmo Genético (Fase 7 / Paso 3).
        """
        import json
        if json_path is None:
            json_path = TABLES_DIR / "best_individual_fis.json"
        json_path = Path(json_path)

        if not json_path.exists():
            raise FileNotFoundError(
                f"Archivo de modelo sintonizado no encontrado en: {json_path}. "
                "Ejecute primero 'python -m src.genetic' para generar el individuo óptimo."
            )

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        fuzzy_partitions = {}
        for var, lbl_dict in data["fuzzy_partitions"].items():
            fuzzy_partitions[var] = {}
            for lbl, info in lbl_dict.items():
                fuzzy_partitions[var][lbl] = (info["type"], info["params"])

        class_centroids = data["class_centroids"]
        return cls(fuzzy_partitions=fuzzy_partitions, class_centroids=class_centroids, **kwargs)

    @staticmethod
    def _parse_rules(rules_df: pd.DataFrame) -> list[tuple[str, list[tuple[str, str]]]]:
        """
        Parsea las reglas textuales en una estructura tabular de tuplas:
        [(consecuente, [(variable, etiqueta), ...]), ...]
        """
        parsed_rules = []
        for _, row in rules_df.iterrows():
            consequent = str(row["consequent"]).strip()
            rule_str = str(row["rule"]).strip()

            # Extraer antecedente antes de THEN
            ant_part = rule_str.split(" THEN ")[0].replace("IF ", "").strip()
            terms = []
            for term in ant_part.split(" AND "):
                parts = term.split(" == ")
                attr = parts[0].strip()
                val = parts[1].strip().replace("'", "").replace('"', "")
                terms.append((attr, val))

            parsed_rules.append((consequent, terms))
        return parsed_rules

    def fuzzify_inputs(self, df: pd.DataFrame, partitions: dict | None = None) -> dict[tuple[str, str], np.ndarray]:
        """
        Calcula vectorialmente los grados de pertenencia mu(x) para todas las combinaciones
        (variable, etiqueta) requeridas por las reglas.
        """
        active_partitions = partitions if partitions is not None else self.fuzzy_partitions
        memberships = {}

        # Identificar solo las variables y etiquetas presentes en las reglas
        required_pairs = set()
        for _, terms in self.rules:
            for attr, label in terms:
                required_pairs.add((attr, label))

        for attr, label in required_pairs:
            if attr not in df.columns:
                raise KeyError(f"La columna requerida '{attr}' no existe en el DataFrame proporcionado.")

            x = df[attr].to_numpy(dtype=float)
            fn_type, params = active_partitions[attr][label]

            if fn_type == "trap":
                mu = trapmf(x, params)
            elif fn_type == "tri":
                mu = trimf(x, params)
            else:
                raise ValueError(f"Tipo de función no reconocido: {fn_type}")

            memberships[(attr, label)] = mu

        return memberships

    def compute_activation_matrix(
        self,
        df: pd.DataFrame,
        partitions: dict | None = None,
        t_norm: str | None = None,
    ) -> np.ndarray:
        """
        Calcula la matriz de activación W de dimensión (N, K), donde:
        W[i, k] es la fuerza de disparo de la regla k sobre la muestra i.
        """
        active_t_norm = t_norm.lower() if t_norm is not None else self.t_norm
        memberships = self.fuzzify_inputs(df, partitions=partitions)

        n_samples = len(df)
        n_rules = len(self.rules)
        W = np.zeros((n_samples, n_rules), dtype=float)

        for k, (_, terms) in enumerate(self.rules):
            # 1. Obtiene los grados de verdad mu de cada condición de la regla k
            term_mus = [memberships[(attr, label)] for attr, label in terms] # Matriz de (N_muestras x N_condiciones)
            stacked = np.column_stack(term_mus)  # (N, n_terms)

            # 2. Aplica la T-norma para obtener el peso de la regla k: w_k
            if active_t_norm == "min":
                W[:, k] = np.min(stacked, axis=1) # se obtiene el peso w_k
            elif active_t_norm == "prod":
                W[:, k] = np.prod(stacked, axis=1)

        return W

    def predict(
        self,
        df: pd.DataFrame,
        partitions: dict | None = None,
        centroids: dict | None = None,
        return_details: bool = False,
    ) -> np.ndarray | tuple[np.ndarray, dict]:
        """
        Genera la predicción numérica continua (en MPa) para cada fila del DataFrame.
        Aplica el mecanismo de escape si sum(w_k) <= epsilon.
        """
        active_centroids = centroids if centroids is not None else self.class_centroids
        n_samples = len(df)

        if n_samples == 0:
            empty_arr = np.array([], dtype=float)
            return (empty_arr, {}) if return_details else empty_arr

        # 1. Matriz de activación (N, K)
        W = self.compute_activation_matrix(df, partitions=partitions)

        # 2. Vector de consecuentes y_k* según la clase asignada a cada regla
        y_star = np.array([active_centroids[cons] for cons, _ in self.rules], dtype=float)

        # 3. Suma de pesos de activación
        sum_w = np.sum(W, axis=1)
        valid_mask = sum_w > self.epsilon

        # 4. Defuzzificación ponderada con escape por defecto
        y_pred = np.full(n_samples, self.default_y, dtype=float)
        if np.any(valid_mask):
            numerator = np.sum(W[valid_mask] * y_star, axis=1) # sum(w_k * y_k*)
            y_pred[valid_mask] = numerator / sum_w[valid_mask] # dividido para sum(w_k)

        if return_details:
            orphan_count = int((~valid_mask).sum())
            details = {
                "orphan_count": orphan_count,
                "coverage_pct": round((n_samples - orphan_count) / n_samples * 100, 2),
                "activation_matrix": W,
                "sum_weights": sum_w,
                "valid_mask": valid_mask,
            }
            return y_pred, details

        return y_pred

    def evaluate(
        self,
        df: pd.DataFrame,
        target_col: str = TARGET_COLUMN,
        partitions: dict | None = None,
        centroids: dict | None = None,
    ) -> dict[str, float]:
        """
        Evalúa el sistema difuso sobre un DataFrame con valores objetivo reales.
        Calcula métricas estándar de regresión y cobertura.
        """
        if target_col not in df.columns:
            raise KeyError(f"Columna objetivo '{target_col}' no presente en el DataFrame.")

        y_true = df[target_col].to_numpy(dtype=float)
        y_pred, details = self.predict(df, partitions=partitions, centroids=centroids, return_details=True)

        n_samples = len(y_true)
        errors = y_true - y_pred

        rmse = float(np.sqrt(np.mean(errors ** 2)))
        mae = float(np.mean(np.abs(errors)))

        ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
        ss_res = float(np.sum(errors ** 2))
        r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

        # MAPE (Mean Absolute Percentage Error) evitando divisiones por valores casi cero
        safe_y_true = np.where(y_true < 1e-3, 1e-3, y_true)
        mape = float(np.mean(np.abs(errors / safe_y_true)) * 100.0)

        return {
            "n_samples": n_samples,
            "n_orphans": details["orphan_count"],
            "coverage_pct": details["coverage_pct"],
            "rmse": round(rmse, 4),
            "mae": round(mae, 4),
            "r2": round(r2, 4),
            "mape": round(mape, 2),
        }


def run_baseline_evaluation() -> pd.DataFrame:
    """
    Ejecuta y registra la evaluación de la Línea Base (Baseline inicial) del Motor Difuso
    sobre las particiones Train, Val y Test, guardando el reporte en results/tables/.
    """
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    train_df = pd.read_csv(TRAIN_CLEAN_PATH)
    val_df = pd.read_csv(VAL_CLEAN_PATH)
    test_df = pd.read_csv(TEST_CLEAN_PATH)

    default_mean = float(train_df[TARGET_COLUMN].mean())
    fis = FuzzyInferenceSystem(default_y=default_mean, t_norm="min")

    print("\n" + "=" * 80)
    print("EVALUACIÓN DE LÍNEA BASE (BASELINE INICIAL) - MOTOR DE INFERENCIA DIFUSO (FIS)")
    print("=" * 80)
    print(f"Reglas Consolidadas Activas: {len(fis.rules)}")
    print(f"Operador T-norma:            {fis.t_norm.upper()}")
    print(f"Valor de Escape por Defecto: {fis.default_y:.2f} MPa (Media global Train)")
    print("Centroides Iniciales (y_k*):")
    for c, val in fis.class_centroids.items():
        print(f"  -> {c:12}: {val:.2f} MPa")
    print("-" * 80)

    train_metrics = fis.evaluate(train_df)
    val_metrics = fis.evaluate(val_df)
    test_metrics = fis.evaluate(test_df)

    results = [
        {"Partición": "Train (70%)", **train_metrics},
        {"Partición": "Val (15%)", **val_metrics},
        {"Partición": "Test (15%)", **test_metrics},
    ]

    summary_df = pd.DataFrame(results)

    # Imprimir tabla formateada
    print(summary_df[["Partición", "n_samples", "coverage_pct", "rmse", "mae", "r2", "mape"]].to_string(index=False))
    print("-" * 80)

    out_path = TABLES_DIR / "baseline_inference_summary.csv"
    summary_df.to_csv(out_path, index=False)
    print(f"Resumen de Línea Base guardado en: {out_path}")
    print("=" * 80 + "\n")

    return summary_df


if __name__ == "__main__":
    run_baseline_evaluation()
