# Documentación Técnica del Proyecto

En este directorio se reúnen los documentos de diseño, justificación estadística, normativa de ingeniería civil y arquitectura difusa del sistema:

1. [01_analisis_eda.md](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/docs/01_analisis_eda.md):
   * Conclusiones del análisis exploratorio (EDA).
   * Justificación del comportamiento de los ceros estructurales como ausencia física.
   * Análisis de la distribución de la edad, duplicados, outliers y relación agua/cemento.
   * Criterios de no normalización global.

2. [02_definicion_funciones_pertenencia.md](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/docs/02_definicion_funciones_pertenencia.md):
   * Especificación geométrica de los conjuntos difusos (Singletons, Hombros Trapezoidales y Triangulares).
   * Parámetros iniciales de cada etiqueta lingüística para las 8 variables de entrada y la variable objetivo.
   * Fundamentación normativa bajo los estándares **ACI 318**, **ACI 363R** y **Eurocódigo EN 206 / EN 1992**.
   * Estructura de invariantes y grados de libertad para la sintonización con Algoritmos Genéticos (Fuzzy Tuning).

3. [03_induccion_reglas_prism_lift.md](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/docs/03_induccion_reglas_prism_lift.md):
   * Particionamiento estratificado 70% Train / 15% Val / 15% Test.
   * Inducción de reglas modulares con el algoritmo PRISM.
   * Resultados de los 8 casos de soporte y confianza con filtrado LIFT > 1.0.
   * Análisis de sensibilidad (Confianza vs. Soporte).

4. [04_limpieza_consolidacion_reglas.md](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/docs/04_limpieza_consolidacion_reglas.md):
   * Fase 1: Limpieza y Consolidación de la Base de Reglas (Filtro Manual / Lógico).
   * Deduplicación exacta de reglas (de 64 a 35 reglas únicas).
   * Análisis y eliminación de las 5 contradicciones lógicas detectadas.
   * Poda por umbrales de calidad (Confianza >= 50%, Soporte >= 1%, Val Lift > 1.0).
   * Base de reglas consolidada (15 reglas) y tabla de auditoría completa.

5. [05_motor_inferencia_fis_baseline.md](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/docs/05_motor_inferencia_fis_baseline.md):
   * Fase 6: Motor de Inferencia Difuso (FIS) tipo Mamdani/TSK continuo.
   * Manejo robusto de filas huérfanas mediante regla de escape a la media (35.34 MPa).
   * Parametrización de los consecuentes de las 4 clases de resistencia (y_k*).
   * Métricas de Línea Base Inicial (Train RMSE: 12.37 MPa, Val RMSE: 13.25 MPa, R²: 0.4359).

6. [06_algoritmo_genetico_tuning.md](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/docs/06_algoritmo_genetico_tuning.md):
   * Fase 7: Sintonización Paramétrica mediante Algoritmo Genético (Fuzzy Tuning).
   * Estructura del cromosoma real de 69 genes (65 vértices difusos + 4 centroides normativos).
   * Operador de reparación activa de restricciones monótonas y solapamiento lingüístico.
   * Resultados optimizados (Train RMSE: 9.06 MPa, Test RMSE: 9.79 MPa, R²: 0.6971).

7. [07_evaluacion_final_visualizaciones.md](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/docs/07_evaluacion_final_visualizaciones.md):
   * Fase 8: Evaluación final visual y cuantitativa del sistema difuso-genético.
   * Curva de convergencia generacional del AG y activación de Early Stopping.
   * Diagrama de dispersión Real vs. Predicho en el conjunto ciego de Test (151 muestras).
   * Análisis del comportamiento cinético adaptado en las funciones de pertenencia (`age`, `cement`, `water`).



