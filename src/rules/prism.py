import numpy as np
import pandas as pd

from src.config import (
    TRAIN_DISCRETIZED_PATH,
    VAL_DISCRETIZED_PATH,
    TABLES_DIR,
    TARGET_COLUMN,
)


class PrismRuleMiner:
    """
    Implementación del algoritmo PRISM (Cendrowska, 1987) para inducción modular de reglas,
    con soporte para restricciones de confianza mínima, soporte mínimo y filtrado por LIFT.
    """

    def __init__(self, target_column: str = TARGET_COLUMN):
        self.target_column = target_column

    def fit(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame | None = None,
        min_confidence: float = 0.50,
        min_support: int = 50,
        support_type: str = "antecedent",  # "antecedent" (count(A)) o "rule" (count(A y C))
        min_lift: float = 1.0,
    ) -> pd.DataFrame:
        """
        Ejecuta PRISM clase por clase sobre el dataset de entrenamiento.

        Parameters
        ----------
        train_df : pd.DataFrame
            Dataset discretizado de entrenamiento.
        val_df : pd.DataFrame, optional
            Dataset discretizado de validación para calcular métricas de generalización.
        min_confidence : float
            Umbral mínimo de confianza (ej. 0.50 o 0.80).
        min_support : int
            Umbral mínimo de observaciones cubiertas (ej. 50 u 80).
        support_type : str
            'antecedent' (count(A) >= min_support) o 'rule' (count(A & C) >= min_support).
        min_lift : float
            Umbral mínimo de Lift (por defecto > 1.0).

        Returns
        -------
        pd.DataFrame
            Conjunto de reglas inducidas con sus métricas.
        """
        feature_cols = [c for c in train_df.columns if c != self.target_column]
        classes = sorted(train_df[self.target_column].unique())
        n_train = len(train_df)
        n_val = len(val_df) if val_df is not None else 0

        rules = []

        for target_class in classes:
            p_class_train = (train_df[self.target_column] == target_class).mean()
            p_class_val = (val_df[self.target_column] == target_class).mean() if val_df is not None else 0.0

            # Copia de trabajo para cubrir instancias de esta clase
            current_data = train_df.copy()

            while True:
                # Instancias no cubiertas de la clase objetivo
                remaining_class_instances = current_data[current_data[self.target_column] == target_class]
                if len(remaining_class_instances) == 0:
                    break

                rule_terms = {}
                subset = current_data.copy()
                available_attrs = list(feature_cols)

                rule_valid = False

                while available_attrs:
                    best_pair = None
                    best_prob = -1.0
                    best_support = 0

                    for attr in available_attrs:
                        for val in subset[attr].unique():
                            sub_val = subset[subset[attr] == val]
                            tot_sub = len(sub_val)
                            if tot_sub == 0:
                                continue
                            pos_sub = len(sub_val[sub_val[self.target_column] == target_class])
                            prob = pos_sub / tot_sub

                            # Criterio PRISM: mayor probabilidad, luego mayor soporte
                            if (prob > best_prob) or (prob == best_prob and pos_sub > best_support):
                                best_prob = prob
                                best_support = pos_sub
                                best_pair = (attr, val)

                    if best_pair is None or best_prob <= 0:
                        break

                    attr, val = best_pair
                    rule_terms[attr] = val
                    available_attrs.remove(attr)
                    subset = subset[subset[attr] == val]

                    # Evaluar la regla candidata sobre todo el conjunto de entrenamiento
                    mask_train_ant = pd.Series(True, index=train_df.index)
                    for a, v in rule_terms.items():
                        mask_train_ant &= (train_df[a] == v)

                    ant_supp_train = int(mask_train_ant.sum())
                    rule_supp_train = int((mask_train_ant & (train_df[self.target_column] == target_class)).sum())
                    conf_train = rule_supp_train / ant_supp_train if ant_supp_train > 0 else 0.0
                    lift_train = conf_train / p_class_train if p_class_train > 0 else 0.0

                    check_supp = ant_supp_train if support_type == "antecedent" else rule_supp_train

                    # Verificar condiciones
                    if conf_train >= min_confidence:
                        if check_supp >= min_support and lift_train > min_lift:
                            # Calcular métricas en validación si está disponible
                            if val_df is not None:
                                mask_val_ant = pd.Series(True, index=val_df.index)
                                for a, v in rule_terms.items():
                                    mask_val_ant &= (val_df[a] == v)
                                ant_supp_val = int(mask_val_ant.sum())
                                rule_supp_val = int((mask_val_ant & (val_df[self.target_column] == target_class)).sum())
                                conf_val = rule_supp_val / ant_supp_val if ant_supp_val > 0 else 0.0
                                lift_val = conf_val / p_class_val if (p_class_val > 0 and ant_supp_val > 0) else 0.0
                            else:
                                ant_supp_val, rule_supp_val, conf_val, lift_val = 0, 0, 0.0, 0.0

                            rule_str = "IF " + " AND ".join([f"{a} == '{v}'" for a, v in rule_terms.items()]) + f" THEN {self.target_column} == '{target_class}'"

                            rules.append({
                                "consequent": target_class,
                                "n_terms": len(rule_terms),
                                "rule": rule_str,
                                "train_ant_supp": ant_supp_train,
                                "train_rule_supp": rule_supp_train,
                                "train_supp_pct": round(rule_supp_train / n_train * 100, 2),
                                "train_conf": round(conf_train, 4),
                                "train_lift": round(lift_train, 3),
                                "val_ant_supp": ant_supp_val,
                                "val_rule_supp": rule_supp_val,
                                "val_conf": round(conf_val, 4),
                                "val_lift": round(lift_val, 3),
                            })
                            rule_valid = True
                        break

                # Eliminar del dataset de trabajo las instancias de la clase cubiertas
                if rule_terms:
                    mask_rem = pd.Series(True, index=current_data.index)
                    for a, v in rule_terms.items():
                        mask_rem &= (current_data[a] == v)
                    covered_idx = current_data[mask_rem & (current_data[self.target_column] == target_class)].index
                    if len(covered_idx) == 0:
                        break
                    current_data = current_data.drop(covered_idx)
                else:
                    break

        if not rules:
            return pd.DataFrame(columns=[
                "consequent", "n_terms", "rule",
                "train_ant_supp", "train_rule_supp", "train_supp_pct",
                "train_conf", "train_lift",
                "val_ant_supp", "val_rule_supp", "val_conf", "val_lift"
            ])

        rules_df = pd.DataFrame(rules).drop_duplicates(subset=["consequent", "rule"]).reset_index(drop=True)
        return rules_df


ALL_CASES = [
    {"case_num": 1, "conf": 0.50, "supp": 50, "desc": "Caso 1: Confianza 50% - Soporte 50"},
    {"case_num": 2, "conf": 0.80, "supp": 50, "desc": "Caso 2: Confianza 80% - Soporte 50"},
    {"case_num": 3, "conf": 0.50, "supp": 80, "desc": "Caso 3: Confianza 50% - Soporte 80"},
    {"case_num": 4, "conf": 0.80, "supp": 80, "desc": "Caso 4: Confianza 80% - Soporte 80"},
    {"case_num": 5, "conf": 0.50, "supp": 25, "desc": "Caso 5: Confianza 50% - Soporte 25"},
    {"case_num": 6, "conf": 0.50, "supp": 50, "desc": "Caso 6: Confianza 50% - Soporte 50"},
    {"case_num": 7, "conf": 0.25, "supp": 50, "desc": "Caso 7: Confianza 25% - Soporte 50"},
    {"case_num": 8, "conf": 0.25, "supp": 25, "desc": "Caso 8: Confianza 25% - Soporte 25"},
]


def evaluate_all_cases():
    """
    Ejecuta y compara los 8 casos experimentales estandarizados:
    Casos 1 a 4 (Pruebas iniciales) y Casos 5 a 8 (Nuevas pruebas de calibración).
    Todos los archivos siguen la nomenclatura estricta:
    rules_caso_#_conf#_supp#.csv
    y se resumen en rules_cases_summary.csv.
    """
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    train_df = pd.read_csv(TRAIN_DISCRETIZED_PATH)
    val_df = pd.read_csv(VAL_DISCRETIZED_PATH)

    miner = PrismRuleMiner()
    summary_rows = []

    print("\n" + "=" * 75)
    print("INDUCCIÓN DE REGLAS CON PRISM Y FILTRADO POR LIFT (> 1.0) - CASOS 1 A 8")
    print("=" * 75)
    print(f"Dataset de Entrenamiento: {len(train_df)} muestras")
    print(f"Dataset de Validación:    {len(val_df)} muestras")
    print("-" * 75)

    for c in ALL_CASES:
        num = c["case_num"]
        conf_int = int(c["conf"] * 100)
        supp_int = c["supp"]
        case_id = f"caso_{num}"
        out_filename = f"rules_{case_id}_conf{conf_int}_supp{supp_int}.csv"
        out_path = TABLES_DIR / out_filename

        print(f"\nEjecutando {c['desc']} (min_conf={conf_int}%, min_supp={supp_int}, lift > 1.0)...")

        rules_df = miner.fit(
            train_df=train_df,
            val_df=val_df,
            min_confidence=c["conf"],
            min_support=c["supp"],
            support_type="antecedent",
            min_lift=1.0,
        )

        rules_df.to_csv(out_path, index=False)

        num_rules = len(rules_df)
        avg_conf_train = rules_df["train_conf"].mean() if num_rules > 0 else 0.0
        avg_lift_train = rules_df["train_lift"].mean() if num_rules > 0 else 0.0
        avg_conf_val = rules_df["val_conf"].mean() if num_rules > 0 else 0.0
        avg_lift_val = rules_df["val_lift"].mean() if num_rules > 0 else 0.0

        print(f"  -> Reglas generadas: {num_rules}")
        print(f"  -> Archivo guardado: {out_path}")

        summary_rows.append({
            "Caso": case_id,
            "Descripción": c["desc"],
            "Conf_Min": f"{conf_int}%",
            "Supp_Min": supp_int,
            "Num_Reglas": num_rules,
            "Train_Conf_Media": round(avg_conf_train, 4),
            "Train_Lift_Medio": round(avg_lift_train, 3),
            "Val_Conf_Media": round(avg_conf_val, 4),
            "Val_Lift_Medio": round(avg_lift_val, 3),
            "Archivo_CSV": out_filename,
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_path = TABLES_DIR / "rules_cases_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    print("\n" + "=" * 75)
    print("RESUMEN GENERAL CONSOLIDADO DE LOS 8 CASOS:")
    print("=" * 75)
    print(summary_df[["Caso", "Conf_Min", "Supp_Min", "Num_Reglas", "Train_Conf_Media", "Train_Lift_Medio", "Val_Conf_Media", "Val_Lift_Medio"]].to_string(index=False))
    print(f"\nResumen global consolidado guardado en: {summary_path}")
    print("=" * 75)
    return summary_df


if __name__ == "__main__":
    evaluate_all_cases()
