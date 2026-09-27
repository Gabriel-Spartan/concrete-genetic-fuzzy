import numpy as np

# ------------------------------------------------------------
# FUNCIONES DE PERTENENCIA VECTORIZADAS
# ------------------------------------------------------------

def trapmf(x: np.ndarray, params: list[float]) -> np.ndarray:
    """
    Función de pertenencia trapezoidal vectorizada [a, b, c, d].
    Soporta hombro izquierdo (a == b) y hombro derecho (c == d).
    """
    a, b, c, d = params
    x = np.asarray(x, dtype=float)
    y = np.zeros_like(x)

    # Rampa izquierda
    if a != b:
        idx1 = (x >= a) & (x < b)
        y[idx1] = (x[idx1] - a) / (b - a)
    else:
        idx1 = (x <= b)
        y[idx1] = 1.0

    # Meseta central (núcleo)
    idx2 = (x >= b) & (x <= c)
    y[idx2] = 1.0

    # Rampa derecha
    if c != d:
        idx3 = (x > c) & (x <= d)
        y[idx3] = (d - x[idx3]) / (d - c)
    else:
        idx3 = (x >= c)
        y[idx3] = 1.0

    return np.clip(y, 0.0, 1.0)


def trimf(x: np.ndarray, params: list[float]) -> np.ndarray:
    """
    Función de pertenencia triangular vectorizada [a, b, c].
    """
    a, b, c = params
    x = np.asarray(x, dtype=float)
    y = np.zeros_like(x)

    # Rampa ascendente
    if a != b:
        idx1 = (x >= a) & (x <= b)
        y[idx1] = (x[idx1] - a) / (b - a)
    else:
        idx1 = (x == a)
        y[idx1] = 1.0

    # Rampa descendente
    if b != c:
        idx2 = (x > b) & (x <= c)
        y[idx2] = (c - x[idx2]) / (c - b)

    return np.clip(y, 0.0, 1.0)


# ------------------------------------------------------------
# DEFINICIÓN FORMAL DE CONJUNTOS DIFUSOS Y PARTICIONES
# ------------------------------------------------------------

FUZZY_PARTITIONS = {
    # Grupo 1: Variables con ceros estructurales (4 etiquetas)
    "blast_furnace_slag": {
        "no_aplica": ("trap", [0.0, 0.0, 0.0, 5.0]),
        "poco": ("trap", [0.0, 11.0, 106.3, 135.7]),
        "medio": ("tri", [106.3, 135.7, 170.0]),
        "alto": ("trap", [135.7, 170.0, 360.0, 360.0]),
    },
    "fly_ash": {
        "no_aplica": ("trap", [0.0, 0.0, 0.0, 10.0]),
        "poco": ("trap", [0.0, 24.5, 100.5, 121.4]),
        "medio": ("tri", [100.5, 121.4, 140.0]),
        "alto": ("trap", [121.4, 140.0, 200.1, 200.1]),
    },
    "superplasticizer": {
        "no_aplica": ("trap", [0.0, 0.0, 0.0, 0.8]),
        "poco": ("trap", [0.0, 1.7, 7.8, 9.4]),
        "medio": ("tri", [7.8, 9.4, 11.0]),
        "alto": ("trap", [9.4, 11.0, 32.2, 32.2]),
    },

    # Grupo 2: Variable con alta dispersión temporal (4 etiquetas)
    "age": {
        "muy_temprana": ("trap", [1.0, 1.0, 7.0, 28.0]),
        "estandar": ("tri", [7.0, 28.0, 56.0]),
        "madura": ("tri", [28.0, 56.0, 90.0]),
        "largo_plazo": ("trap", [56.0, 90.0, 365.0, 365.0]),
    },

    # Grupo 3: Componentes obligatorios sin ceros (3 etiquetas)
    "cement": {
        "poco": ("trap", [102.0, 102.0, 200.0, 272.9]),
        "medio": ("tri", [200.0, 272.9, 350.0]),
        "alto": ("trap", [272.9, 350.0, 540.0, 540.0]),
    },
    "water": {
        "poco": ("trap", [121.8, 121.8, 165.0, 185.0]),
        "medio": ("tri", [165.0, 185.0, 200.0]),
        "alto": ("trap", [185.0, 200.0, 247.0, 247.0]),
    },
    "coarse_aggregate": {
        "poco": ("trap", [801.0, 801.0, 930.0, 968.0]),
        "medio": ("tri", [930.0, 968.0, 1030.0]),
        "alto": ("trap", [968.0, 1030.0, 1145.0, 1145.0]),
    },
    "fine_aggregate": {
        "poco": ("trap", [594.0, 594.0, 730.0, 779.5]),
        "medio": ("tri", [730.0, 779.5, 825.0]),
        "alto": ("trap", [779.5, 825.0, 992.6, 992.6]),
    },

    # Salida: Resistencia a compresión bajo ACI 318, ACI 363R y EN 206 (4 etiquetas)
    "compressive_strength": {
        "baja": ("trap", [2.33, 2.33, 15.0, 27.5]),
        "media_baja": ("tri", [15.0, 27.5, 42.5]),
        "media_alta": ("tri", [27.5, 42.5, 55.0]),
        "alta": ("trap", [42.5, 55.0, 82.6, 82.6]),
    }
}
