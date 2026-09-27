# Catálogo de Tablas y Modelos Exportados

En este directorio se almacenan los resultados tabulares, auditorías y modelos exportados a lo largo de las distintas etapas del proyecto:

## 1. Análisis Exploratorio y Particionamiento
* `data_quality.csv`: Auditoría de calidad de datos, tipos, nulos y duplicados.
* `descriptive_statistics.csv`: Estadísticas descriptivas completas (media, desv., cuartiles, IQR, asimetría, curtosis, ceros).
* `correlation_pearson.csv`: Matriz de correlación lineal paramétrica de Pearson.
* `correlation_spearman.csv`: Matriz de correlación monótona no paramétrica de Spearman.
* `splits_summary.csv`: Resumen del particionamiento estratificado 70% Train / 15% Val / 15% Test.

## 2. Inducción y Limpieza de Reglas (PRISM)
* `rules_cases_summary.csv`: Métricas de reglas generadas para los 8 escenarios experimentales de soporte y confianza.
* `rules_caso_1_conf50_supp50.csv` a `rules_caso_8_conf25_supp25.csv`: Reglas detalladas para cada caso experimental estandarizado.
* `rules_sensitivity_grid.csv`: Matriz de sensibilidad exploratoria variando combinaciones de confianza y soporte.
* `rules_cleaning_audit.csv`: Registro de auditoría del descarte de reglas duplicadas, contradictorias y de baja calidad.
* `rules_consolidated.csv`: **Base de reglas aprobada (15 reglas consolidadas)** con $\text{Lift} > 1.0$, sin contradicciones.

## 3. Inferencia y Línea Base (Baseline)
* `baseline_inference_summary.csv`: Métricas iniciales del FIS antes del tuning en Train, Val y Test.

## 4. Sintonización con Algoritmo Genético (Tuning)
* `ga_convergence_history.csv`: Registro generacional completo (Generación, RMSE Train/Val, R² Val, MAE, Cobertura).
* `ga_tuning_comparison.csv`: Comparativa formal: FIS Inicial vs. FIS Sintonizado con AG en las 3 particiones.
* `tuned_parameters_summary.csv`: Resumen de los 69 genes sintonizados (valor nominal, óptimo y delta).
* `best_individual_fis.json`: **Modelo autocontenido del mejor individuo** (funciones de pertenencia y centroides en formato JSON) para inferencia directa vía `FuzzyInferenceSystem.from_tuned()`.

## 5. Evaluación Ciega Final (Test 15% - 151 Muestras)
* `final_test_evaluation.csv`: Tabla definitiva de evaluación formal en conjunto ciego (RMSE = 9.79 MPa, R² = 0.6434, Cobertura = 99.34%).
* `test_predictions_detailed.csv`: Predicciones y residuos muestra a muestra para las 151 probetas del conjunto ciego de Test.
