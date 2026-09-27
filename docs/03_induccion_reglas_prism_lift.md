# Inducción de Reglas con PRISM y Validación con Métrica LIFT

Este documento registra los resultados de la **Fase 4**: particionamiento estratificado del dataset (70% Train / 15% Val / 15% Test) y la extracción modular de reglas mediante el algoritmo **PRISM (Cendrowska, 1987)** bajo diferentes restricciones de **Confianza**, **Soporte** y **LIFT > 1.0**.

---

## 1. Particionamiento Estratificado (70% / 15% / 15%)

Para evitar cualquier filtración de datos (*data leakage*) y asegurar la reproducibilidad (`random_state=42`), el dataset procesado (1005 filas) se dividió en tres subconjuntos conservando idéntica proporción de las 4 clases de resistencia:

| Partición | N.° Filas | Proporción | Rol en el Sistema |
|---|:---:|:---:|---|
| **Entrenamiento (`train`)** | **703** | **70.0 %** | Inducción de reglas con PRISM y entrenamiento/fitness del Algoritmo Genético. |
| **Validación (`val`)** | **151** | **15.0 %** | Evaluación externa de reglas con LIFT y control de sobreajuste del GA. |
| **Prueba (`test`)** | **151** | **15.0 %** | Conjunto ciego para evaluación final del sistema genético-difuso sintonizado. |

### Distribución de Clases por Partición (`results/tables/splits_summary.csv`)
* `media_baja`: ~30.7 % (Train: 216, Val: 47, Test: 46)
* `media_alta`: ~27.7 % (Train: 195, Val: 42, Test: 42)
* `baja`: ~21.0 % (Train: 148, Val: 31, Test: 32)
* `alta`: ~20.5 % (Train: 144, Val: 31, Test: 31)

---

## 2. Definición Matemática de Métricas de Regla

Para una regla del tipo $R: \text{IF } A \text{ THEN } C$ (donde $A$ es la conjunción de condiciones y $C$ es la clase de resistencia):

1. **Soporte del Antecedente ($\text{Supp}_A$):** Número de observaciones en el dataset que cumplen la condición $A$.
2. **Soporte de la Regla ($\text{Supp}_{A \cap C}$):** Número de observaciones que cumplen simultáneamente $A$ y $C$.
3. **Confianza ($\text{Conf}$):** Precisión condicional de la regla:
   $$\text{Conf}(R) = P(C \mid A) = \frac{\text{Supp}_{A \cap C}}{\text{Supp}_A}$$
4. **Métrica LIFT:** Fuerza de asociación respecto a la probabilidad basal a priori $P(C)$:
   $$\text{Lift}(R) = \frac{P(C \mid A)}{P(C)} = \frac{\text{Conf}(R)}{P(C)}$$
   * $\text{Lift} > 1.0$: Asociación positiva y regla de valor explicativo real.
   * $\text{Lift} \le 1.0$: Independencia estadística o asociación negativa (descartada).

---

## 3. Resultados de los 8 Casos Experimentales Consolidados

Se evaluaron los 8 escenarios sobre el conjunto de entrenamiento (703 muestras) con validación externa en el conjunto de validación (151 muestras), exigiendo $\text{LIFT} > 1.0$:

| Caso | Confianza Mínima | Soporte Mínimo | N.° Reglas | Train Conf Media | Train Lift Medio | Val Conf Media | Val Lift Medio | Archivo CSV |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Caso 1** | **$\ge 50\%$** | **$\ge 50$** | **3 reglas** | **54.95 %** | **2.36** | **45.88 %** | **1.99** | [rules_caso_1_conf50_supp50.csv](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/rules_caso_1_conf50_supp50.csv) |
| **Caso 2** | **$\ge 80\%$** | **$\ge 50$** | **0 reglas** | - | - | - | - | [rules_caso_2_conf80_supp50.csv](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/rules_caso_2_conf80_supp50.csv) |
| **Caso 3** | **$\ge 50\%$** | **$\ge 80$** | **1 regla** | **50.43 %** | **2.40** | **51.02 %** | **2.48** | [rules_caso_3_conf50_supp80.csv](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/rules_caso_3_conf50_supp80.csv) |
| **Caso 4** | **$\ge 80\%$** | **$\ge 80$** | **0 reglas** | - | - | - | - | [rules_caso_4_conf80_supp80.csv](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/rules_caso_4_conf80_supp80.csv) |
| **Caso 5** | **$\ge 50\%$** | **$\ge 25$** | **15 reglas** | **56.87 %** | **2.40** | **51.09 %** | **2.13** | [rules_caso_5_conf50_supp25.csv](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/rules_caso_5_conf50_supp25.csv) |
| **Caso 6** | **$\ge 50\%$** | **$\ge 50$** | **3 reglas** | **54.95 %** | **2.36** | **45.88 %** | **1.99** | [rules_caso_6_conf50_supp50.csv](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/rules_caso_6_conf50_supp50.csv) |
| **Caso 7** | **$\ge 25\%$** | **$\ge 50$** | **21 reglas** | **35.48 %** | **1.44** | **37.27 %** | **1.49** | [rules_caso_7_conf25_supp50.csv](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/rules_caso_7_conf25_supp50.csv) |
| **Caso 8** | **$\ge 25\%$** | **$\ge 25$** | **21 reglas** | **35.48 %** | **1.44** | **37.27 %** | **1.49** | [rules_caso_8_conf25_supp25.csv](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/rules_caso_8_conf25_supp25.csv) |

*El resumen general consolidado se almacena en:* [results/tables/rules_cases_summary.csv](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/rules_cases_summary.csv).

---

## 4. Detalle de las Reglas Inducidas y Significado Físico

### Reglas del Caso 1 (Conf $\ge 50\%$, Supp $\ge 50$, Lift > 1.0):

#### Regla 1 (Clase Alta):
$$\text{IF superplasticizer == 'alto' AND fly_ash == 'no_aplica' THEN compressive_strength == 'alta'}$$
* **Train:** Soporte = 61 muestras | Confianza = 59.02 % | **Lift = 2.88**
* **Validación:** Soporte = 14 muestras | Confianza = 42.86 % | **Lift = 2.09**
* **Interpretación de Ingeniería:** Mezclas con dosis elevadas de superplastificante (que reducen drásticamente la relación agua/cemento) y sin ceniza volante alcanzan resistencias de alta exigencia estructural ($\ge 50\ MPa$).

#### Regla 2 (Clase Baja):
$$\text{IF age == 'muy_temprana' THEN compressive_strength == 'baja'}$$
* **Train:** Soporte = 230 muestras | Confianza = 50.43 % | **Lift = 2.40**
* **Validación:** Soporte = 49 muestras | Confianza = 51.02 % | **Lift = 2.48**
* **Interpretación de Ingeniería:** En edades tempranas de curado (1 a 7 días), el proceso de hidratación del cemento aún no se completa; la resistencia se mantiene mayoritariamente por debajo de los $20\ MPa$. *(Esta es la única regla que también supera el umbral de soporte $\ge 80$ del Caso 3)*.

#### Regla 3 (Clase Media-Baja):
$$\text{IF age == 'estandar' AND superplasticizer == 'no_aplica' THEN compressive_strength == 'media_baja'}$$
* **Train:** Soporte = 74 muestras | Confianza = 55.41 % | **Lift = 1.80**
* **Validación:** Soporte = 16 muestras | Confianza = 43.75 % | **Lift = 1.41**
* **Interpretación de Ingeniería:** A la edad estándar de 28 días, un concreto convencional sin aditivo químico superplastificante produce resistencias típicas de diseño residencial/comercial ($20 - 35\ MPa$).

---

## 5. Análisis de Sensibilidad: ¿Por qué los Casos 2 y 4 obtuvieron 0 reglas?

En un conjunto de entrenamiento de 703 muestras distribuidas en 4 clases (~144 a 216 muestras por clase):
* Para alcanzar una **confianza muy alta ($\ge 80\%$)**, PRISM debe añadir 2 o 3 antecedentes especializados (ej. combinar edad madura, cemento alto y aditivo medio).
* Cada condición adicional reduce el tamaño de la intersección. En nuestros datos, las reglas con $\text{Conf} \ge 80\%$ alcanzan un soporte máximo de **36 observaciones**.
* Exigir simultáneamente un soporte $\ge 50$ u $\ge 80$ elimina todas las reglas de alta confianza.

### Tabla de Sensibilidad Confianza vs. Soporte (`results/tables/rules_sensitivity_grid.csv`):

| Confianza Mínima | Soporte Mínimo | N.° Reglas | Confianza Media (Train) | Lift Medio (Train) | Confianza Media (Val) | Lift Medio (Val) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **80%** | **15** | **10** | **87.53 %** | **3.98** | **91.59 %** | **4.29** |
| **80%** | **20** | **8** | **85.93 %** | **3.97** | **89.49 %** | **4.31** |
| **80%** | **25** | **3** | **86.70 %** | **4.16** | **96.97 %** | **4.72** |
| **80%** | **30** | **3** | **86.70 %** | **4.16** | **96.97 %** | **4.72** |
| **80%** | **50** | **0** | - | - | - | - |
| **70%** | **20** | **6** | **79.26 %** | **3.82** | **92.06 %** | **4.48** |
| **70%** | **50** | **2** | **72.64 %** | **3.45** | **76.19 %** | **3.71** |
| **60%** | **20** | **12** | **72.59 %** | **3.43** | **79.70 %** | **3.84** |
| **50%** | **50** | **3** | **54.95 %** | **2.36** | **45.88 %** | **1.99** |

---

## 6. Conclusión y Recomendación para la Base de Reglas Difusas

1. **Los 4 casos solicitados están completamente ejecutados y guardados en `results/tables/`.**
2. **Recomendación para enriquecer la base de reglas del Sistema Difuso:**
   * Si se desea un conjunto de reglas robusto y de alta precisión para el Algoritmo Genético, una combinación de **Confianza $\ge 70\%$ o $\ge 80\%$ con Soporte $\ge 20$** produce entre 6 y 10 reglas con altísimo poder explicativo ($\text{Lift} \approx 4.0$ y confianza $> 85\%$).
