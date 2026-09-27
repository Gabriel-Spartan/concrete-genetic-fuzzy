"""
Módulo de Definición y Codificación del Cromosoma para el Algoritmo Genético.

Estructura del Cromosoma:
Vector de números reales de dimensión fija (69 genes):
- 65 genes: Vértices ajustables de las funciones de pertenencia de las 8 variables de entrada.
- 4 genes: Centroides continuos en MPa de las 4 clases de resistencia (y_baja, y_media_baja, y_media_alta, y_alta).

Invariantes Físicos Fijos (No codificados en el cromosoma):
- Singletons de ausencia física en cero ([0, 0, 0, delta]) para slag, ash y superplasticizer.
- Extremos rígidos del dominio físico (x_min y x_max) para hombros izquierdo y derecho.
"""

from typing import Any
import numpy as np

from src.fuzzy.membership import FUZZY_PARTITIONS
from src.fuzzy.inference import DEFAULT_CLASS_CENTROIDS, CENTROID_BOUNDS


def _build_gene_spec() -> list[dict[str, Any]]:
    """
    Construye la especificación estricta de cada gen en el cromosoma:
    nombre de variable, etiqueta, índice de parámetro, nombre ('a', 'b', 'c', 'd'),
    valor nominal y límites físicos [lb, ub].
    """
    specs = []

    # 1. Variables de entrada (8 variables)
    for var, partitions in FUZZY_PARTITIONS.items():
        if var == "compressive_strength":
            continue

        # Obtener los límites globales observados de la variable
        all_vals = []
        for _, (_, p) in partitions.items():
            all_vals.extend(p)
        var_min = float(min(all_vals))
        var_max = float(max(all_vals))
        var_range = var_max - var_min

        for label, (kind, params) in partitions.items():
            if label == "no_aplica":
                # Invariante físico: la ausencia de material no se sintoniza
                continue

            if kind == "trap":
                # Hombro izquierdo: params[0] y params[1] son fijos en x_min
                if params[0] == params[1]:
                    specs.append({
                        "type": "input",
                        "var": var,
                        "label": label,
                        "kind": "trap",
                        "param_idx": 2,
                        "param_name": "c",
                        "nominal": float(params[2]),
                        "lb": var_min,
                        "ub": var_max,
                        "var_range": var_range,
                    })
                    specs.append({
                        "type": "input",
                        "var": var,
                        "label": label,
                        "kind": "trap",
                        "param_idx": 3,
                        "param_name": "d",
                        "nominal": float(params[3]),
                        "lb": var_min,
                        "ub": var_max,
                        "var_range": var_range,
                    })
                # Hombro derecho: params[2] y params[3] son fijos en x_max
                elif params[2] == params[3]:
                    specs.append({
                        "type": "input",
                        "var": var,
                        "label": label,
                        "kind": "trap",
                        "param_idx": 0,
                        "param_name": "a",
                        "nominal": float(params[0]),
                        "lb": var_min,
                        "ub": var_max,
                        "var_range": var_range,
                    })
                    specs.append({
                        "type": "input",
                        "var": var,
                        "label": label,
                        "kind": "trap",
                        "param_idx": 1,
                        "param_name": "b",
                        "nominal": float(params[1]),
                        "lb": var_min,
                        "ub": var_max,
                        "var_range": var_range,
                    })
                else:
                    for i, p_name in enumerate(["a", "b", "c", "d"]):
                        specs.append({
                            "type": "input",
                            "var": var,
                            "label": label,
                            "kind": "trap",
                            "param_idx": i,
                            "param_name": p_name,
                            "nominal": float(params[i]),
                            "lb": var_min,
                            "ub": var_max,
                            "var_range": var_range,
                        })

            elif kind == "tri":
                for i, p_name in enumerate(["a", "b", "c"]):
                    specs.append({
                        "type": "input",
                        "var": var,
                        "label": label,
                        "kind": "tri",
                        "param_idx": i,
                        "param_name": p_name,
                        "nominal": float(params[i]),
                        "lb": var_min,
                        "ub": var_max,
                        "var_range": var_range,
                    })

    # 2. Consecuentes de salida (4 centroides de clases en MPa)
    class_order = ["baja", "media_baja", "media_alta", "alta"]
    for c in class_order:
        lb, ub = CENTROID_BOUNDS[c]
        nominal = DEFAULT_CLASS_CENTROIDS[c]
        specs.append({
            "type": "centroid",
            "var": "compressive_strength",
            "label": c,
            "kind": "centroid",
            "param_idx": 0,
            "param_name": "y_star",
            "nominal": float(nominal),
            "lb": float(lb),
            "ub": float(ub),
            "var_range": float(ub - lb),
        })

    return specs


GENE_SPECS: list[dict[str, Any]] = _build_gene_spec()
CHROMOSOME_LENGTH: int = len(GENE_SPECS)


def get_nominal_chromosome() -> np.ndarray:
    """
    Retorna el cromosoma de partida con los valores nominales de la línea base (dimensión 69).
    """
    return np.array([g["nominal"] for g in GENE_SPECS], dtype=float)


def get_bounds() -> tuple[np.ndarray, np.ndarray]:
    """
    Retorna dos arreglos (lower_bounds, upper_bounds) de longitud 69 con los límites permitidos.
    """
    lb = np.array([g["lb"] for g in GENE_SPECS], dtype=float)
    ub = np.array([g["ub"] for g in GENE_SPECS], dtype=float)
    return lb, ub


def decode_chromosome(chrom: np.ndarray) -> tuple[dict, dict]:
    """
    Decodifica el vector real de 69 genes en:
    1. partitions_dict: diccionario con la estructura completa de FUZZY_PARTITIONS para las 8 variables.
    2. centroids_dict: diccionario con los valores continuos en MPa {'baja': ..., 'media_baja': ..., ...}.
    """
    if len(chrom) != CHROMOSOME_LENGTH:
        raise ValueError(f"Longitud de cromosoma incorrecta: {len(chrom)} != {CHROMOSOME_LENGTH}")

    # Inicializar copia profunda de las particiones base
    partitions = {}
    for var, p_dict in FUZZY_PARTITIONS.items():
        if var == "compressive_strength":
            continue
        partitions[var] = {}
        for label, (kind, p_list) in p_dict.items():
            partitions[var][label] = (kind, list(p_list))

    centroids = DEFAULT_CLASS_CENTROIDS.copy()

    # Reemplazar los parámetros con los genes del cromosoma
    for gene_val, spec in zip(chrom, GENE_SPECS):
        if spec["type"] == "input":
            var = spec["var"]
            label = spec["label"]
            param_idx = spec["param_idx"]
            partitions[var][label][1][param_idx] = float(gene_val)
        elif spec["type"] == "centroid":
            label = spec["label"]
            centroids[label] = float(gene_val)

    return partitions, centroids


def encode_chromosome(partitions: dict, centroids: dict) -> np.ndarray:
    """
    Codifica un diccionario de particiones y centroides en el vector real de 69 genes.
    """
    chrom = np.zeros(CHROMOSOME_LENGTH, dtype=float)
    for i, spec in enumerate(GENE_SPECS):
        if spec["type"] == "input":
            var = spec["var"]
            label = spec["label"]
            param_idx = spec["param_idx"]
            chrom[i] = partitions[var][label][1][param_idx]
        elif spec["type"] == "centroid":
            label = spec["label"]
            chrom[i] = centroids[label]
    return chrom
