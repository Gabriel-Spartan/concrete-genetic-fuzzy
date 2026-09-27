"""
Módulo de Operadores Genéticos para Fuzzy Tuning:
- Operador de Reparación Activa (repair_chromosome): Garantiza orden a <= b <= c <= d,
  solapamiento mínimo lingüístico y límites normativos.
- Cruce BLX-alpha (Blend Crossover).
- Mutación Gaussiana Acotada.
- Selección por Torneo.
"""

import numpy as np

from src.genetic.chromosome import (
    decode_chromosome,
    encode_chromosome,
    get_bounds,
    CHROMOSOME_LENGTH,
)
from src.fuzzy.inference import CENTROID_BOUNDS


VARIABLE_LABEL_ORDER = {
    "blast_furnace_slag": ["poco", "medio", "alto"],
    "fly_ash": ["poco", "medio", "alto"],
    "superplasticizer": ["poco", "medio", "alto"],
    "age": ["muy_temprana", "estandar", "madura", "largo_plazo"],
    "cement": ["poco", "medio", "alto"],
    "water": ["poco", "medio", "alto"],
    "coarse_aggregate": ["poco", "medio", "alto"],
    "fine_aggregate": ["poco", "medio", "alto"],
}


def _enforce_order_bounds(points: list[float] | np.ndarray, lb: float, ub: float, delta: float) -> list[float]:
    """
    Garantiza que una lista de puntos mantenga orden estricto lb <= p0 <= p1 ... <= ub
    con separación mínima delta mediante un doble barrido (Forward-Backward pass).
    """
    pts = np.clip(np.sort(points), lb, ub)
    n = len(pts)

    # Forward pass: asegurar espaciado mínimo
    for i in range(1, n):
        if pts[i] < pts[i - 1] + delta:
            pts[i] = pts[i - 1] + delta

    # Backward pass: corregir si el extremo derecho sobrepasó ub
    if pts[-1] > ub:
        pts[-1] = ub
        for i in range(n - 2, -1, -1):
            if pts[i] > pts[i + 1] - delta:
                pts[i] = pts[i + 1] - delta

    return [float(p) for p in pts]


def repair_chromosome(chrom: np.ndarray) -> np.ndarray:
    """
    Operador de Reparación Activa:
    Toma un cromosoma real (posiblemente alterado por cruce o mutación) y lo transforma
    en un individuo 100% viable, garantizando:
    1. Truncamiento estricto a límites físicos [lb, ub].
    2. Orden monótono interno de cada conjunto: a <= b <= c <= d.
    3. Ancho mínimo de conjunto (delta_min) para evitar divisiones por cero en pendientes.
    4. Solapamiento mínimo garantizado entre etiquetas adyacentes (delta_overlap).
    5. Orden y límites normativos de los 4 centroides de resistencia en MPa:
       y_baja < y_media_baja < y_media_alta < y_alta.
    """
    lb, ub = get_bounds()
    clipped_chrom = np.clip(chrom, lb, ub)
    partitions, centroids = decode_chromosome(clipped_chrom)

    # 1. Reparar conjuntos difusos de cada variable de entrada
    for var, labels in VARIABLE_LABEL_ORDER.items():
        all_vals = []
        for l in labels:
            all_vals.extend(partitions[var][l][1])
        var_min = float(min(all_vals))
        var_max = float(max(all_vals))
        var_range = max(var_max - var_min, 1.0)

        delta_min = max(0.015 * var_range, 1e-3)       # Ancho mínimo: 1.5% del rango
        delta_overlap = max(0.010 * var_range, 1e-3)   # Solapamiento mínimo: 1.0% del rango

        # A. Orden interno de cada etiqueta individual
        for l in labels:
            kind, p = partitions[var][l]
            if kind == "trap":
                if p[0] == p[1]:
                    # Hombro izquierdo: p[0], p[1] fijos en var_min
                    c, d = _enforce_order_bounds([p[2], p[3]], var_min, var_max, delta_min)
                    partitions[var][l] = (kind, [var_min, var_min, c, d])
                elif p[2] == p[3]:
                    # Hombro derecho: p[2], p[3] fijos en var_max
                    a, b = _enforce_order_bounds([p[0], p[1]], var_min, var_max, delta_min)
                    partitions[var][l] = (kind, [a, b, var_max, var_max])
                else:
                    a, b, c, d = _enforce_order_bounds(p, var_min, var_max, delta_min)
                    partitions[var][l] = (kind, [a, b, c, d])

            elif kind == "tri":
                a, b, c = _enforce_order_bounds(p, var_min, var_max, delta_min)
                partitions[var][l] = (kind, [a, b, c])

        # B. Solapamiento Lingüístico entre etiquetas adyacentes
        for i in range(len(labels) - 1):
            curr_label = labels[i]
            next_label = labels[i + 1]

            kind_curr, p_curr = partitions[var][curr_label]
            kind_next, p_next = partitions[var][next_label]

            curr_right_foot = p_curr[3] if kind_curr == "trap" else p_curr[2]
            next_left_foot = p_next[0]

            # Si hay un hueco (curr_right_foot < next_left_foot + delta_overlap)
            if curr_right_foot < next_left_foot + delta_overlap:
                midpoint = (curr_right_foot + next_left_foot) / 2.0
                new_right = min(var_max, midpoint + delta_overlap / 2.0)
                new_left = max(var_min, midpoint - delta_overlap / 2.0)

                if kind_curr == "trap":
                    p_curr[3] = float(new_right)
                    p_curr[2] = min(p_curr[2], p_curr[3] - delta_min)
                else:
                    p_curr[2] = float(new_right)
                    p_curr[1] = min(p_curr[1], p_curr[2] - delta_min)

                if kind_next == "trap":
                    p_next[0] = float(new_left)
                    p_next[1] = max(p_next[1], p_next[0] + delta_min)
                else:
                    p_next[0] = float(new_left)
                    p_next[1] = max(p_next[1], p_next[0] + delta_min)

    # 2. Reparar centroides consecuentes de resistencia (y_baja < y_media_baja < y_media_alta < y_alta)
    class_order = ["baja", "media_baja", "media_alta", "alta"]
    for c in class_order:
        b_min, b_max = CENTROID_BOUNDS[c]
        centroids[c] = float(np.clip(centroids[c], b_min, b_max))

    # Asegurar orden monótono estricto con separación mínima de 2.0 MPa
    min_separation = 2.0
    centroids["baja"] = min(centroids["baja"], centroids["media_baja"] - min_separation)
    centroids["media_baja"] = max(centroids["media_baja"], centroids["baja"] + min_separation)
    centroids["media_baja"] = min(centroids["media_baja"], centroids["media_alta"] - min_separation)
    centroids["media_alta"] = max(centroids["media_alta"], centroids["media_baja"] + min_separation)
    centroids["media_alta"] = min(centroids["media_alta"], centroids["alta"] - min_separation)
    centroids["alta"] = max(centroids["alta"], centroids["media_alta"] + min_separation)

    re_encoded = encode_chromosome(partitions, centroids)
    # Clip final de seguridad
    return np.clip(re_encoded, lb, ub)


def crossover_blx_alpha(
    parent1: np.ndarray,
    parent2: np.ndarray,
    alpha: float = 0.3,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Cruce BLX-alpha (Blend Crossover) para parámetros continuos con reparación inmediata.
    """
    d = np.abs(parent1 - parent2)
    min_val = np.minimum(parent1, parent2) - alpha * d
    max_val = np.maximum(parent1, parent2) + alpha * d

    child1 = np.random.uniform(min_val, max_val)
    child2 = np.random.uniform(min_val, max_val)

    child1 = repair_chromosome(child1)
    child2 = repair_chromosome(child2)

    return child1, child2


def mutate_gaussian(
    chrom: np.ndarray,
    mutation_rate: float = 0.15,
    sigma_scale: float = 0.05,
) -> np.ndarray:
    """
    Mutación Gaussiana acotada con reparación activa.
    Aplica una perturbación normal proporcional al rango de cada gen con probabilidad mutation_rate.
    """
    lb, ub = get_bounds()
    gene_ranges = ub - lb
    mutated = chrom.copy()

    mask = np.random.rand(len(chrom)) < mutation_rate
    if np.any(mask):
        sigmas = gene_ranges * sigma_scale
        perturbations = np.random.normal(0.0, sigmas)
        mutated[mask] += perturbations[mask]

    return repair_chromosome(mutated)


def tournament_selection(
    population: list[np.ndarray],
    fitness_scores: np.ndarray,
    tournament_size: int = 3,
) -> np.ndarray:
    """
    Selección por torneo (menor valor de score objetivo = mejor, ya que minimizamos RMSE).
    """
    pop_size = len(population)
    selected_indices = np.random.choice(pop_size, size=tournament_size, replace=False)
    best_idx = selected_indices[np.argmin(fitness_scores[selected_indices])]
    return population[best_idx].copy()
