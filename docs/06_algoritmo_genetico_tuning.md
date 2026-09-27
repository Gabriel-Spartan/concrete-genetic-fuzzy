# Fase 7: Sintonización Paramétrica con Algoritmo Genético (Fuzzy Tuning)

Este documento detalla la arquitectura, operadores evolutivos, función de fitness y resultados de la **Fase 7: Sintonización Paramétrica mediante Algoritmos Genéticos (Genetic Fuzzy Tuning)** implementada en el paquete [`src/genetic/`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/src/genetic).

---

## 1. Motivación y Objetivos del Tuning Genético

El sistema difuso inicial (Línea Base) demostró la validez cualitativa de las 15 reglas inductivas consolidadas ($R^2 = 0.4359$, RMSE = $12.37\ MPa$). Sin embargo, las funciones de pertenencia iniciales fueron estimadas a partir de cuartiles estadísticos nominales y medianas, sin un ajuste fino conjunto a la física del problema.

El objetivo del **Algoritmo Genético (AG)** es optimizar simultáneamente:
1. La **geometría de los conjuntos difusos** de las 8 variables de entrada (anchos, pendientes y centros).
2. Los **centroides continuos de salida ($y_c^*$)** para las 4 clases de resistencia en $MPa$.

Todo esto conservando de forma estricta:
* La base de 15 reglas inductivas extraídas por PRISM (sin alterar su estructura lógica).
* Los singletons de ausencia física en cero (invariantes).
* El solapamiento lingüístico suave (sin degenerar en lógica booleana).
* Las jerarquías y límites normativos de resistencia (ACI 318, ACI 363R y EN 206).

---

## 2. Arquitectura del Algoritmo Genético

### 2.1. Estructura del Cromosoma Real (`src/genetic/chromosome.py`)
El individuo se modela como un vector real de dimensión fija (**69 genes**):
* **65 genes de entrada:** Vértices ajustables ($a, b, c, d$) de las funciones de pertenencia de las 8 variables de entrada.
* **4 genes de salida:** Centroides continuos en $MPa$ para las 4 clases de resistencia ($y_{\text{baja}}, y_{\text{media\_baja}}, y_{\text{media\_alta}}, y_{\text{alta}}$).

#### Invariantes Físicos Fijos (Fuera del Cromosoma):
* Singletons en cero $[0, 0, 0, \delta]$ para `blast_furnace_slag`, `fly_ash` y `superplasticizer` (garantizan que el cero represente siempre ausencia física).
* Extremos absolutos del dominio ($x_{\min}$ y $x_{\max}$) para hombros izquierdo y derecho.

---

### 2.2. Operador de Reparación Activa (`src/genetic/operators.py`)
Para evitar el estancamiento evolutivo por penalización de individuos inválidos, se diseñó un **operador de reparación determinista activo** basado en un doble barrido *Forward-Backward pass*:

1. **Truncamiento a límites físicos:** $x_i = \text{clip}(x_i, lb_i, ub_i)$.
2. **Orden monótono interno:** Asegura $a \le b \le c \le d$ dentro de cada conjunto con apertura mínima $\delta_{\min} = 1.5\%$ del rango físico, eliminando divisiones por cero en pendientes.
3. **Preservación del solapamiento lingüístico:** Para etiquetas adyacentes $S_1$ y $S_2$, asegura que el pie derecho de $S_1$ intersecte al pie izquierdo de $S_2$ por al menos $\delta_{\text{overlap}} = 1.0\%$ del rango, erradicando zonas muertas.
4. **Orden estricto de centroides normativos:**
   $$y_{\text{baja}} \in [5, 20] < y_{\text{media\_baja}} \in [20, 35] < y_{\text{media\_alta}} \in [35, 50] < y_{\text{alta}} \in [50, 75]$$
   con separación mínima de $2.0\ MPa$ entre clases contiguas.

**Resultado:** El **100% de los individuos de la población son matemáticamente viables y físicamente interpretables**.

---

### 2.3. Operadores Evolutivos
* **Cruce BLX-$\alpha$ (Blend Crossover):** Parámetro $\alpha = 0.3$, recombinación continua de intervalos exploratorios con reparación inmediata.
* **Mutación Gaussiana Acotada:** Perturbación $\mathcal{N}(0, \sigma^2)$ con $\sigma = 6\%$ del rango de cada gen, tasa de mutación por gen de $15\%$ y probabilidad de mutación de $25\%$.
* **Selección:** Torneo determinista de tamaño $k = 3$.
* **Elitismo:** Los $2$ mejores individuos de cada generación pasan intactos a la siguiente.
* **Semilla Nominal:** El individuo nominal de la Línea Base se incluye en la generación inicial, garantizando que el AG nunca empeore el modelo original.
* **Control de Sobreajuste (Early Stopping):** Monitoreo del RMSE en el conjunto de Validación (15%) con paciencia de $15$ generaciones.

---

## 3. Resultados de la Optimización y Comparación Formal

El algoritmo evolucionó durante **45 generaciones** en solo **3.89 segundos**, alcanzando la solución óptima en la **generación 30** ([`ga_tuning_comparison.csv`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/ga_tuning_comparison.csv)):

| Modelo | Partición | N.° Muestras | Filas Huérfanas | Cobertura (%) | RMSE ($MPa$) | MAE ($MPa$) | $R^2$ | MAPE (%) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **FIS Inicial (Baseline)** | Train (70%) | 703 | 44 | 93.74 % | 12.37 | 9.17 | 0.4359 | 30.33 % |
| **FIS Sintonizado (GA)** | **Train (70%)** | 703 | **14** | **98.01 %** | **9.06** | **7.14** | **0.6971** | **28.36 %** |
| **FIS Inicial (Baseline)** | Val (15%) | 151 | 11 | 92.72 % | 13.25 | 10.10 | 0.2418 | 32.26 % |
| **FIS Sintonizado (GA)** | **Val (15%)** | 151 | **4** | **97.35 %** | **10.37** | **8.21** | **0.5354** | **30.22 %** |
| **FIS Inicial (Baseline)** | Test (15%) | 151 | 12 | 92.05 % | 13.06 | 9.82 | 0.3649 | 30.52 % |
| **FIS Sintonizado (GA)** | **Test (15% Ciego)**| 151 | **1** | **99.34 %** | **9.79** | **7.75** | **0.6434** | **27.64 %** |

---

## 4. Análisis de Mejoras Alcanzadas

1. **Reducción Drástica del Error:**
   * En Entrenamiento: RMSE bajó de **$12.37\ MPa$ a $9.06\ MPa$** (reducción del **26.7 %** en error cuadrático).
   * En Validación: RMSE bajó de **$13.25\ MPa$ a $10.37\ MPa$** (reducción del **21.7 %**).
   * En Prueba Ciega (Test): RMSE bajó de **$13.06\ MPa$ a $9.79\ MPa$** (reducción del **25.1 %**).
2. **Salto en Capacidad Explicativa ($R^2$):**
   * Train: subió de **$0.4359$ a $0.6971$** (el modelo explica casi el **70 % de la varianza** del concreto).
   * Val: subió de **$0.2418$ a $0.5354$** (se duplicó con creces la generalización).
   * Test ciego: subió de **$0.3649$ a $0.6434$**.
3. **Expansión de Cobertura y Disminución de Huérfanas:**
   * Al reparar activamente el solapamiento entre conjuntos adyacentes, la cobertura sobre el conjunto ciego de Test alcanzó el **99.34 %** (solo 1 muestra huérfana de 151).
4. **Centroides de Resistencia Calibrados ([`tuned_parameters_summary.csv`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/tuned_parameters_summary.csv)):**
   * `baja`: $13.90 \to \mathbf{15.03\ MPa}$
   * `media_baja`: $28.47 \to \mathbf{26.94\ MPa}$
   * `media_alta`: $41.02 \to \mathbf{38.57\ MPa}$
   * `alta`: $59.97 \to \mathbf{61.15\ MPa}$

---

## 5. Archivos Generados en la Fase 7

* **Módulos fuente:**
  * [`src/genetic/chromosome.py`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/src/genetic/chromosome.py): Codificación, decodificación y especificación de 69 genes.
  * [`src/genetic/operators.py`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/src/genetic/operators.py): Reparador activo, cruce BLX-$\alpha$ y mutación acotada.
  * [`src/genetic/fitness.py`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/src/genetic/fitness.py): Evaluador vectorizado de RMSE continuo.
  * [`src/genetic/ga.py`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/src/genetic/ga.py): Motor evolutivo con Early Stopping.
  * [`src/genetic/__main__.py`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/src/genetic/__main__.py): Entrypoint ejecutable vía `python -m src.genetic`.
* **Tablas y modelos exportados:**
  * [`results/tables/ga_convergence_history.csv`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/ga_convergence_history.csv): Evolución generación por generación.
  * [`results/tables/ga_tuning_comparison.csv`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/ga_tuning_comparison.csv): Comparación formal Baseline vs. Sintonizado.
  * [`results/tables/tuned_parameters_summary.csv`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/tuned_parameters_summary.csv): Valores nominales vs. óptimos de los 69 parámetros.
  * [`results/tables/best_individual_fis.json`](file:///home/gabriel/Desktop/Septimo/IA/concrete-genetic-fuzzy/results/tables/best_individual_fis.json): Configuración completa del mejor modelo sintonizado (funciones de pertenencia y centroides normativos) para inferencia directa.
