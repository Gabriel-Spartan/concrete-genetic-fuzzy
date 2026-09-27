from pathlib import Path

# ------------------------------------------------------------
# RUTAS PRINCIPALES DEL PROYECTO
# ------------------------------------------------------------

# Archivo actual:
# concrete-genetic-fuzzy/src/config.py
#
# parents[1] permite subir desde src/ hasta la raíz del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_DIR = RESULTS_DIR / "tables"

DOCS_DIR = PROJECT_ROOT / "docs"

# Dataset original descargado.
DATASET_PATH = RAW_DATA_DIR / "dataset.csv"

# Datasets procesados.
CLEAN_DATASET_PATH = PROCESSED_DATA_DIR / "dataset_clean.csv"
FUZZY_MATRIX_PATH = PROCESSED_DATA_DIR / "fuzzy_matrix.csv"
DISCRETIZED_DATASET_PATH = PROCESSED_DATA_DIR / "dataset_discretized.csv"

# Particiones Train (70%) / Val (15%) / Test (15%).
SPLITS_DIR = PROCESSED_DATA_DIR / "splits"
TRAIN_DISCRETIZED_PATH = SPLITS_DIR / "train_discretized.csv"
VAL_DISCRETIZED_PATH = SPLITS_DIR / "val_discretized.csv"
TEST_DISCRETIZED_PATH = SPLITS_DIR / "test_discretized.csv"

TRAIN_CLEAN_PATH = SPLITS_DIR / "train_clean.csv"
VAL_CLEAN_PATH = SPLITS_DIR / "val_clean.csv"
TEST_CLEAN_PATH = SPLITS_DIR / "test_clean.csv"

TRAIN_FUZZY_PATH = SPLITS_DIR / "train_fuzzy.csv"
VAL_FUZZY_PATH = SPLITS_DIR / "val_fuzzy.csv"
TEST_FUZZY_PATH = SPLITS_DIR / "test_fuzzy.csv"


# ------------------------------------------------------------
# NOMBRES INTERNOS DE LAS COLUMNAS
# ------------------------------------------------------------

# El dataset original contiene nombres largos.
# Para trabajar con código más claro se renombran a snake_case.
COLUMN_NAMES = [
    "cement",
    "blast_furnace_slag",
    "fly_ash",
    "water",
    "superplasticizer",
    "coarse_aggregate",
    "fine_aggregate",
    "age",
    "compressive_strength",
]

# Variables de entrada del problema.
INPUT_COLUMNS = COLUMN_NAMES[:-1]

# Variable objetivo.
TARGET_COLUMN = "compressive_strength"
