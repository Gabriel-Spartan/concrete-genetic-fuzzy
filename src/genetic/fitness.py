"""
Módulo de Evaluación de Fitness para Fuzzy Tuning.

Evalúa el rendimiento de los individuos (cromosomas) utilizando directamente el
Motor de Inferencia Difuso (FuzzyInferenceSystem). La función objetivo a minimizar
es el RMSE sobre el conjunto de entrenamiento (70%), monitoreando simultáneamente
el error en el conjunto de validación (15%) para el control de sobreajuste.
"""

from typing import Literal
import numpy as np
import pandas as pd

from src.config import TRAIN_CLEAN_PATH, VAL_CLEAN_PATH, TEST_CLEAN_PATH
from src.fuzzy.inference import FuzzyInferenceSystem
from src.genetic.chromosome import decode_chromosome


class FuzzyFitnessEvaluator:
    """
    Evaluador optimizado de fitness para el Algoritmo Genético.
    Mantiene en memoria el motor difuso y los datasets de Train y Validación.
    """

    def __init__(
        self,
        fis: FuzzyInferenceSystem | None = None,
        train_df: pd.DataFrame | None = None,
        val_df: pd.DataFrame | None = None,
        test_df: pd.DataFrame | None = None,
    ):
        self.fis = fis if fis is not None else FuzzyInferenceSystem()
        self.train_df = train_df if train_df is not None else pd.read_csv(TRAIN_CLEAN_PATH)
        self.val_df = val_df if val_df is not None else pd.read_csv(VAL_CLEAN_PATH)
        self.test_df = test_df if test_df is not None else pd.read_csv(TEST_CLEAN_PATH)

    def evaluate_rmse(
        self,
        chrom: np.ndarray,
        dataset: Literal["train", "val", "test"] = "train",
    ) -> float:
        """
        Evalúa el error RMSE continuo en MPa para un cromosoma.
        Objetivo del AG: Minimizar este valor.
        """
        partitions, centroids = decode_chromosome(chrom)

        if dataset == "train":
            df = self.train_df
        elif dataset == "val":
            df = self.val_df
        elif dataset == "test":
            df = self.test_df
        else:
            raise ValueError(f"Dataset no reconocido: {dataset}")

        metrics = self.fis.evaluate(df, partitions=partitions, centroids=centroids)
        return float(metrics["rmse"])

    def evaluate_population(
        self,
        population: list[np.ndarray],
        dataset: Literal["train", "val"] = "train",
    ) -> np.ndarray:
        """
        Evalúa secuencialmente toda una población y retorna un vector de RMSEs.
        """
        scores = np.zeros(len(population), dtype=float)
        for i, chrom in enumerate(population):
            scores[i] = self.evaluate_rmse(chrom, dataset=dataset)
        return scores

    def get_full_metrics(
        self,
        chrom: np.ndarray,
        dataset: Literal["train", "val", "test"] = "train",
    ) -> dict[str, float]:
        """
        Retorna todas las métricas de rendimiento (RMSE, MAE, R², MAPE, Cobertura).
        """
        partitions, centroids = decode_chromosome(chrom)
        if dataset == "train":
            df = self.train_df
        elif dataset == "val":
            df = self.val_df
        else:
            df = self.test_df

        return self.fis.evaluate(df, partitions=partitions, centroids=centroids)
