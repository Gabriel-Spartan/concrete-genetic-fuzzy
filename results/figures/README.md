# Figuras y Gráficos del Proyecto

En este directorio se almacenan los gráficos y figuras generadas automáticamente durante el desarrollo y evaluación del sistema difuso-genético:

## 1. Análisis Exploratorio de Datos (EDA - Fase 1)
Generados mediante: `python -m src.eda`
* `histogram_*.png`: Distribuciones de frecuencia para cada una de las 9 variables.
* `boxplot_*.png`: Identificación de valores atípicos y dispersión por variable.
* `scatter_*_vs_strength.png`: Relaciones bivariadas con la resistencia a la compresión ($MPa$).
* `correlation_matrix_pearson.png`: Matriz de correlación lineal bivariada.

## 2. Evaluación Visual del Sistema Difuso-Genético (Fase 8)
Generados mediante: `python -m src.visualization`
* `ga_convergence_curve.png`: Curva generacional de convergencia del Algoritmo Genético (Evolución de RMSE en Train y Val, junto con $R^2$ en validación, marcando el óptimo en Gen 30 y Early Stopping en Gen 45).
* `scatter_actual_vs_predicted_test.png`: Diagrama de dispersión Real vs. Predicho en el conjunto ciego de Prueba (15% Test - 151 muestras), contrastando el desempeño del FIS Inicial ($R^2 = 0.3649$) frente al FIS Sintonizado con AG ($R^2 = 0.6434$) con banda de tolerancia de $\pm 10\ MPa$.
* `fuzzy_membership_comparison_age.png`: Comparativa geométrica de las funciones de pertenencia antes vs. después del tuning para la variable `age` (días).
* `fuzzy_membership_comparison_cement.png`: Comparativa geométrica antes vs. después para la variable `cement` ($kg/m^3$).
* `fuzzy_membership_comparison_water.png`: Comparativa geométrica antes vs. después para la variable `water` ($kg/m^3$).
* `fuzzy_membership_comparison_all_variables.png`: Cuadrícula integral 4x2 con las curvas de pertenencia antes vs. después para las 8 variables de entrada.
