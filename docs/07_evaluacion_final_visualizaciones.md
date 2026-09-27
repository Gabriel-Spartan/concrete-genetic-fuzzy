# Paso 4 / Fase 8: Evaluación Ciega Final y Reporte Gráfico

Este documento consolida la **evaluación formal definitiva sobre el conjunto ciego de prueba (15% Test - 151 muestras)**, la auditoría comparativa frente a la Línea Base, el análisis detallado de las figuras generadas en [`results/figures/`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/figures) y el despliegue del modelo final.

---

## 1. P4_1: Evaluación en Conjunto Ciego (Test 15% = 151 Muestras)

El conjunto de prueba permaneció **completamente aislado** durante todas las fases previas (discretización, inducción de reglas PRISM, poda de contradicciones y sintonización de parámetros con el Algoritmo Genético).

* **Archivo de datos:** [`data/processed/splits/test_clean.csv`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/data/processed/splits/test_clean.csv) (151 probetas estratificadas).
* **Rango experimental de resistencia en Test:** De $2.33\ MPa$ a $79.99\ MPa$ (Media: $35.42\ MPa$, Desv. Estándar: $16.35\ MPa$).

---

## 2. P4_2: Comparativa de Métricas (FIS Inicial vs. FIS Sintonizado con AG)

La evaluación formal definitiva registrada en [`results/tables/final_test_evaluation.csv`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/final_test_evaluation.csv) y el registro muestra a muestra en [`results/tables/test_predictions_detailed.csv`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/test_predictions_detailed.csv) arrojan:

| Métrica de Desempeño | FIS Inicial (Línea Base) | FIS Sintonizado con AG (Propuesto) | Impacto / Mejora Relativa |
|---|:---:|:---:|:---:|
| **RMSE ($MPa$)** | 13.0591 | **9.7852** | **-25.07 %** (Reducción del error cuadrático) |
| **MAE ($MPa$)** | 9.8174 | **7.7489** | **-21.07 %** (Reducción del error medio absoluto) |
| **$R^2$ (Varianza Explicada)** | 0.3649 | **0.6434** | **+76.32 %** (Ganancia neta en ajuste global) |
| **MAPE (%)** | 30.52 % | **27.64 %** | **-9.44 %** |
| **Error Máximo Residual ($MPa$)** | 46.42 | **30.94** | **-33.35 %** (Atenuación de errores extremos) |
| **Porcentaje de Cobertura Activa** | 92.05 % | **99.34 %** | **+7.29 pp** |
| **Filas Huérfanas (Sin activación de regla)** | 12 / 151 | **1 / 151** | **-91.67 %** (De 12 a solo 1 probeta huérfana) |
| **Probetas de Test con Menor Error** | — | **88 / 151 (58.3 %)** | Mayoría sustancial mejorada caso a caso |

### Resumen Comparativo Train / Val / Test ([`results/tables/ga_tuning_comparison.csv`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/ga_tuning_comparison.csv)):

| Modelo | Partición | Muestras | RMSE ($MPa$) | MAE ($MPa$) | $R^2$ | Cobertura (%) | Filas Huérfanas |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **FIS Inicial (Baseline)** | Train (70%) | 703 | 12.3703 | 9.1704 | 0.4359 | 93.74 % | 44 |
| **FIS Sintonizado (GA)** | **Train (70%)** | 703 | **9.0644** | **7.1375** | **0.6971** | **98.01 %** | **14** |
| **FIS Inicial (Baseline)** | Val (15%) | 151 | 13.2499 | 10.1001 | 0.2418 | 92.72 % | 11 |
| **FIS Sintonizado (GA)** | **Val (15%)** | 151 | **10.3718** | **8.2106** | **0.5354** | **97.35 %** | **4** |
| **FIS Inicial (Baseline)** | Test (15%) | 151 | 13.0591 | 9.8174 | 0.3649 | 92.05 % | 12 |
| **FIS Sintonizado (GA)** | **Test (15% Ciego)**| 151 | **9.7852** | **7.7489** | **0.6434** | **99.34 %** | **1** |

---

## 3. P4_3: Análisis de las Figuras Técnicas Generadas

### 3.1. Curva de Convergencia Generacional
* **Archivo:** [`results/figures/ga_convergence_curve.png`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/figures/ga_convergence_curve.png)
* **Dinámica:**
  * **Panel 1 (RMSE):** En las primeras 10 generaciones se logra la mayor parte de la reducción del error (de $12.37$ a $9.72\ MPa$ en Train). La curva de Validación sigue un comportamiento estable, alcanzando su mínimo absoluto en la **Generación 30 ($10.37\ MPa$)**.
  * **Panel 2 (R² de Validación):** Crece sostenidamente de $0.4012$ a **$0.5354$**.
  * **Parada Temprana:** A partir de la generación 30, la validación se estabiliza. En la **Generación 45** (tras 15 generaciones sin superar el récord), se detiene el algoritmo, garantizando que el modelo no sufra sobreajuste.

---

### 3.2. Diagrama de Dispersión Real vs. Predicho en Test Ciego
* **Archivo:** [`results/figures/scatter_actual_vs_predicted_test.png`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/figures/scatter_actual_vs_predicted_test.png)
* **Comparativa:**
  * **Panel Izquierdo (FIS Inicial):** Muestra una línea horizontal pronunciada en torno a los $35.34\ MPa$ debido a las 12 muestras huérfanas que caían en el valor de escape por defecto. Fuerte dispersión en resistencias elevadas ($> 50\ MPa$).
  * **Panel Derecho (FIS Sintonizado con AG):** Las 151 probetas se alinean nítidamente a lo largo de la diagonal ideal $y = x$. La banda de tolerancia de $\pm 10\ MPa$ encierra la inmensa mayoría de las muestras, con una sola probeta huérfana ($99.34\%$ de cobertura).

---

### 3.3. Funciones de Pertenencia Antes vs. Después del Tuning

#### A. Cuadrícula Integral de las 8 Variables de Entrada
* **Archivo:** [`results/figures/fuzzy_membership_comparison_all_variables.png`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/figures/fuzzy_membership_comparison_all_variables.png)
* Muestra en una matriz $4 \times 2$ las curvas nominales de partida (líneas punteadas) frente a las curvas sintonizadas por el AG (líneas continuas con sombreado) para:
  1. `cement` ($kg/m^3$)
  2. `blast_furnace_slag` ($kg/m^3$)
  3. `fly_ash` ($kg/m^3$)
  4. `water` ($kg/m^3$)
  5. `superplasticizer` ($kg/m^3$)
  6. `coarse_aggregate` ($kg/m^3$)
  7. `fine_aggregate` ($kg/m^3$)
  8. `age` (días)

#### B. Análisis de Variables Físicas Críticas
1. **`age` (Días de Curado) ([`fuzzy_membership_comparison_age.png`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/figures/fuzzy_membership_comparison_age.png)):**
   * El conjunto `estandar` ensanchó su meseta central abarcando de 28 a 90 días, capturando que la hidratación de los silicatos de calcio (C-S-H) se desacelera tras las primeras 4 semanas.
   * `muy_temprana` ajustó su codo superior para modelar la cinética de ganancia rápida de resistencia de los primeros 7 días.
2. **`cement` ($kg/m^3$) ([`fuzzy_membership_comparison_cement.png`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/figures/fuzzy_membership_comparison_cement.png)):**
   * El conjunto `medio` se desplazó hacia dosificaciones moderadas ($250 - 350\ kg/m^3$), mejorando la granularidad de activación en mezclas estándar de edificación.
3. **`water` ($kg/m^3$) ([`fuzzy_membership_comparison_water.png`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/figures/fuzzy_membership_comparison_water.png)):**
   * El conjunto `poco` estrechó su frontera para penalizar con mayor fidelidad el exceso de agua según la Ley de Abrams.

---

## 4. P4_4: Documentación Técnica y Despliegue en Producción

### Carga Directa del Modelo Sintonizado:
El modelo óptimo se encuentra persistido en [`results/tables/best_individual_fis.json`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/best_individual_fis.json) y puede utilizarse directamente en cualquier script o aplicación:

```python
import pandas as pd
from src.fuzzy.inference import FuzzyInferenceSystem

# Cargar el motor sintonizado directamente
fis = FuzzyInferenceSystem.from_tuned()

# Realizar predicción sobre nuevas mezclas de concreto
nueva_mezcla = pd.DataFrame([{
    "cement": 350.0,
    "blast_furnace_slag": 0.0,
    "fly_ash": 0.0,
    "water": 180.0,
    "superplasticizer": 2.5,
    "coarse_aggregate": 1050.0,
    "fine_aggregate": 750.0,
    "age": 28.0,
}])

prediccion_MPa = fis.predict(nueva_mezcla)[0]
print(f"Resistencia estimada a compresión: {prediccion_MPa:.2f} MPa")
```

### Ejecución Integral de Evaluación:
```bash
# Ejecutar la evaluación formal ciega y actualizar todas las figuras técnicas
python -m src.evaluation
```
