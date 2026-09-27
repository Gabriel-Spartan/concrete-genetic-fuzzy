import os
from pathlib import Path
import pandas as pd

from src.config import TABLES_DIR


def clean_and_consolidate_rules(
    min_confidence: float = 0.50,
    min_support_pct: float = 1.0,
    min_val_lift: float = 1.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fase 1: Limpieza y Consolidación de la Base de Reglas (Filtro Manual / Lógico).
    
    Aplica:
    1. Eliminación de redundancias y duplicados exactos generados a través de los casos.
    2. Detección y eliminación de reglas contradictorias (mismo antecedente, consecuente distinto).
    3. Poda por umbrales de calidad (confianza mínima >= 50%, cobertura mínima >= 1% y Val Lift > 1.0).
    
    Genera:
    - results/tables/rules_consolidated.csv: Base de reglas final, limpia y libre de conflictos.
    - results/tables/rules_cleaning_audit.csv: Auditoría detallada de todas las reglas del pool y su motivo de descarte/aprobación.
    """
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    rule_files = sorted(TABLES_DIR.glob("rules_caso_*.csv"))

    if not rule_files:
        raise FileNotFoundError("No se encontraron archivos rules_caso_*.csv en results/tables/")

    # 1. Cargar todas las reglas de todos los casos
    all_records = []
    for f in rule_files:
        if f.stat().st_size > 150:
            df = pd.read_csv(f)
            for _, row in df.iterrows():
                rec = row.to_dict()
                rec["source_file"] = f.name
                rec["antecedent"] = rec["rule"].split(" THEN ")[0].strip()
                all_records.append(rec)

    pool_df = pd.DataFrame(all_records)
    total_raw_rules = len(pool_df)

    # 2. Deduplicar identificando casos de origen
    unique_rules = []
    for (cons, ant, rule_str), group in pool_df.groupby(["consequent", "antecedent", "rule"]):
        sources = sorted(list(group["source_file"].unique()))
        best_row = group.iloc[0].to_dict()
        best_row["source_files"] = ", ".join(sources)
        best_row["n_appearances"] = len(group)
        unique_rules.append(best_row)

    unique_df = pd.DataFrame(unique_rules)
    total_unique_rules = len(unique_df)
    n_duplicates_removed = total_raw_rules - total_unique_rules

    # 3. Detectar antecedentes contradictorios en el pool
    ant_consequents = unique_df.groupby("antecedent")["consequent"].unique()
    contradictory_ants = ant_consequents[ant_consequents.apply(len) > 1].to_dict()

    # 4. Proceso de auditoría y poda por calidad y consistencia lógica
    audit = []
    for _, r in unique_df.iterrows():
        ant = r["antecedent"]
        cons = r["consequent"]
        conf = r["train_conf"]
        supp_pct = r["train_supp_pct"]
        val_lift = r["val_lift"]
        is_contradictory = ant in contradictory_ants

        reasons = []
        if is_contradictory:
            reasons.append(f"Contradictoria (Conflicto con clases: {list(contradictory_ants[ant])})")
        if conf < min_confidence:
            reasons.append(f"Baja_Confianza ({conf * 100:.1f}% < {min_confidence * 100:.0f}%)")
        if supp_pct < min_support_pct:
            reasons.append(f"Bajo_Soporte ({supp_pct:.2f}% < {min_support_pct:.1f}%)")
        if val_lift <= min_val_lift:
            reasons.append(f"Bajo_Val_Lift ({val_lift:.2f} <= {min_val_lift:.1f})")

        status = "CONSOLIDADA" if len(reasons) == 0 else "DESCARTADA"
        audit.append({
            "rule": r["rule"],
            "consequent": cons,
            "antecedent": ant,
            "train_conf": conf,
            "train_lift": r["train_lift"],
            "train_rule_supp": r["train_rule_supp"],
            "train_supp_pct": supp_pct,
            "val_conf": r["val_conf"],
            "val_lift": val_lift,
            "status": status,
            "discard_reasons": "; ".join(reasons) if reasons else "Ninguna (Aprobada)",
            "source_files": r["source_files"],
            "n_appearances": r["n_appearances"],
        })

    audit_df = pd.DataFrame(audit)

    # 5. Filtrar el conjunto de reglas consolidadas
    consolidated_df = (
        audit_df[audit_df["status"] == "CONSOLIDADA"]
        .sort_values(by=["consequent", "train_conf"], ascending=[True, False])
        .reset_index(drop=True)
    )

    # Validar que no existan contradicciones en el conjunto consolidado
    cons_ant_counts = consolidated_df.groupby("antecedent")["consequent"].nunique()
    remaining_contras = cons_ant_counts[cons_ant_counts > 1]
    if len(remaining_contras) > 0:
        raise ValueError(f"Error crítico: persisten contradicciones tras la consolidación: {remaining_contras.to_dict()}")

    # 6. Guardar archivos de salida
    consolidated_path = TABLES_DIR / "rules_consolidated.csv"
    audit_path = TABLES_DIR / "rules_cleaning_audit.csv"

    # Seleccionar columnas limpias para el archivo maestro de reglas consolidadas
    output_cols = [
        "consequent",
        "rule",
        "train_conf",
        "train_lift",
        "train_rule_supp",
        "train_supp_pct",
        "val_conf",
        "val_lift",
        "source_files",
    ]
    consolidated_df[output_cols].to_csv(consolidated_path, index=False)
    audit_df.to_csv(audit_path, index=False)

    print("\n" + "=" * 80)
    print("FASE 1: LIMPIEZA Y CONSOLIDACIÓN DE REGLAS (FILTRO MANUAL / LÓGICO)")
    print("=" * 80)
    print(f"Total de reglas extraídas (Pool bruto de los 8 casos): {total_raw_rules}")
    print(f"Redundancias y duplicados exactos eliminados:        {n_duplicates_removed}")
    print(f"Reglas únicas evaluadas:                             {total_unique_rules}")
    print(f"Antecedentes con contradicciones lógicas detectadas: {len(contradictory_ants)}")
    print(f"Reglas descartadas por calidad/contradicción:        {(audit_df['status'] == 'DESCARTADA').sum()}")
    print(f"Reglas aprobadas y consolidadas:                     {len(consolidated_df)}")
    print("-" * 80)
    print("DISTRIBUCIÓN DE REGLAS CONSOLIDADAS POR CLASE OBJETIVO:")
    class_counts = consolidated_df["consequent"].value_counts()
    for c, count in class_counts.items():
        print(f"  -> {c:12}: {count:2d} reglas")
    print("-" * 80)
    print(f"Archivo de reglas consolidadas guardado en: {consolidated_path}")
    print(f"Archivo de auditoría completa guardado en:  {audit_path}")
    print("=" * 80 + "\n")

    return consolidated_df, audit_df


if __name__ == "__main__":
    clean_and_consolidate_rules()
