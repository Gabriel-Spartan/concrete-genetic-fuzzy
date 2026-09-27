# Definición de Funciones de Pertenencia y Conjuntos Difusos

Este documento establece la arquitectura formal de las **funciones de pertenencia (membership functions)** para el sistema difuso del dataset *Concrete Compressive Strength*. 

El diseño se estructura como la etapa previa y fundamental para la inducción de reglas mediante el algoritmo **PRISM (evaluado con LIFT)** y la posterior **Sintonización Paramétrica (Tuning)** mediante **Algoritmos Genéticos (GA)**.

---

## 1. Tipos de Funciones de Pertenencia Empleadas

Para garantizar alta interpretabilidad física, bajo coste computacional durante las iteraciones del algoritmo genético y un ajuste paramétrico estable, se seleccionan cuatro geometrías estándar:

1. **Singleton / Semitrapecio Rígido de Ausencia ($\delta_0$)**:
   * **Uso:** Etiqueta `No aplica / No se ocupó` en variables con ceros estructurales (`blast_furnace_slag`, `fly_ash`, `superplasticizer`).
   * **Comportamiento:** $\mu(0) = 1.0$. Si $x > 0$, decae abruptamente a $0$ antes de alcanzar la primera dosis mínima real.
   * **En el Tuning Genético:** **Inmutable**. No consume genes en el cromosoma, asegurando que el cero conserve siempre su significado físico de ausencia de material.

2. **Hombro Trapezoidal Izquierdo (Función $L$)**:
   * **Uso:** Etiqueta inferior (`Poco`, `Muy Temprana`, `Baja`).
   * **Parámetros:** $[a, b, c, d]$ con $a = b = \text{límite inferior}$.
   * **Comportamiento:** Vale $1.0$ para cualquier valor menor o igual a $c$, y decae linealmente hasta $0.0$ en $d$.

3. **Triangular (Función $\Lambda$)**:
   * **Uso:** Etiquetas intermedias (`Medio`, `Estándar`, `Maduro`, `Media-Baja`, `Media-Alta`).
   * **Parámetros:** $[a, b, c]$ donde $a$ es el pie izquierdo, $b$ es el vértice central ($\mu(b) = 1.0$) y $c$ es el pie derecho.
   * **Comportamiento:** Permite modelar con máxima eficiencia la zona de mayor densidad de datos. Es la forma ideal para sintonización genética porque solo requiere ajustar 3 puntos (o desplazar el centro $b$ y la apertura).

4. **Hombro Trapezoidal Derecho (Función $\Gamma$)**:
   * **Uso:** Etiqueta superior (`Alto`, `Largo Plazo`, `Alta`).
   * **Parámetros:** $[a, b, c, d]$ con $c = d = \text{límite superior}$.
   * **Comportamiento:** Crece linealmente desde $a$ hasta $b$, y permanece en $1.0$ para cualquier valor $\ge b$.

---

## 2. Definición Detallada por Variable de Entrada

### Grupo 1: Variables con Ceros Estructurales (4 Etiquetas)
*Componentes suplementarios que pueden o no estar presentes en la mezcla.*

#### 1. Escoria de Alto Horno (`blast_furnace_slag`)
* **Unidad:** $kg/m^3$ | **Rango:** $[0.0, 359.4]$ | **Ceros:** 471 (45.73 %) | **Positivos:** $[11.0, 359.4]$
* **Etiquetas y Funciones:**
  * `No aplica`: Singleton / Semitrapecio $[0.0, 0.0, 0.0, 5.0]$ (Cero físico inmutable).
  * `Poco`: Hombro Izquierdo / Triangular $[5.0, 11.0, 106.0, 135.0]$ (Valores bajos de escoria).
  * `Medio`: Triangular $[106.0, 135.0, 170.0]$ (Centrado en la mediana de positivos: $135.7\ kg/m^3$).
  * `Alto`: Hombro Derecho $[135.0, 170.0, 360.0, 360.0]$ (Altas dosis para concretos de bajo calor de hidratación).

#### 2. Ceniza Volante (`fly_ash`)
* **Unidad:** $kg/m^3$ | **Rango:** $[0.0, 200.1]$ | **Ceros:** 566 (54.95 %) | **Positivos:** $[24.5, 200.1]$
* **Etiquetas y Funciones:**
  * `No aplica`: Singleton / Semitrapecio $[0.0, 0.0, 0.0, 10.0]$.
  * `Poco`: Hombro Izquierdo / Triangular $[10.0, 24.5, 100.0, 121.0]$.
  * `Medio`: Triangular $[100.0, 121.0, 140.0]$ (Centrado en la mediana de positivos: $121.4\ kg/m^3$).
  * `Alto`: Hombro Derecho $[121.0, 140.0, 200.0, 200.0]$.

#### 3. Superplastificante (`superplasticizer`)
* **Unidad:** $kg/m^3$ | **Rango:** $[0.0, 32.2]$ | **Ceros:** 379 (36.80 %) | **Positivos:** $[1.7, 32.2]$
* **Etiquetas y Funciones:**
  * `No aplica`: Singleton / Semitrapecio $[0.0, 0.0, 0.0, 0.8]$.
  * `Poco`: Hombro Izquierdo / Triangular $[0.8, 1.7, 7.8, 9.4]$.
  * `Medio`: Triangular $[7.8, 9.4, 11.5]$ (Centrado en la mediana de positivos: $9.4\ kg/m^3$).
  * `Alto`: Hombro Derecho $[9.4, 12.0, 32.2, 32.2]$ (Dosis elevadas para reducción extrema de agua).

---

### Grupo 2: Variable con Alta Dispersión Temporal (4 Etiquetas)
*Curado del concreto con comportamiento monótono logarítmico y fuerte concentración en 28 días.*

#### 4. Edad de Curado (`age`)
* **Unidad:** días | **Rango:** $[1, 365]$ | **Dispersión:** $CV = 138.3\%$ | **Moda:** 28 días (41.3 % de los datos)
* **Etiquetas y Funciones (Espaciadas no linealmente según hitos de la ingeniería civil):**
  * `Muy Temprana` (1 a 7 días): Hombro Izquierdo $[1.0, 1.0, 7.0, 28.0]$ (Desencofrado rápido y resistencia inicial).
  * `Estándar` (14 a 28 días): Triangular $[7.0, 28.0, 56.0]$ (Vértice en 28 días, norma universal de control de calidad).
  * `Madura` (56 a 90 días): Triangular $[28.0, 56.0, 90.0]$ (Curado secundario y ganancia asintótica).
  * `Largo Plazo` (90 a 365 días): Hombro Derecho $[56.0, 90.0, 365.0, 365.0]$ (Resistencia límite a largo plazo).

---

### Grupo 3: Componentes Obligatorios de Baja y Media Dispersión (3 Etiquetas)
*Materiales básicos presentes en el 100 % de las muestras.*

#### 5. Cemento (`cement`)
* **Unidad:** $kg/m^3$ | **Rango:** $[102.0, 540.0]$ | **Asimetría:** 0.51 (moderada)
* **Etiquetas y Funciones:**
  * `Poco`: Hombro Izquierdo $[102.0, 102.0, 200.0, 272.9]$.
  * `Medio`: Triangular $[200.0, 272.9, 350.0]$ (Centrado en la mediana: $272.9\ kg/m^3$).
  * `Alto`: Hombro Derecho $[272.9, 350.0, 540.0, 540.0]$.

#### 6. Agua (`water`)
* **Unidad:** $kg/m^3$ | **Rango:** $[121.8, 247.0]$ | **Dispersión:** $CV = 11.8\%$ (baja, distribución simétrica)
* **Etiquetas y Funciones:**
  * `Poco`: Hombro Izquierdo $[121.8, 121.8, 165.0, 185.0]$ (Mezclas secas o con aditivo).
  * `Medio`: Triangular $[165.0, 185.0, 200.0]$ (Centrado en la mediana: $185.0\ kg/m^3$).
  * `Alto`: Hombro Derecho $[185.0, 200.0, 247.0, 247.0]$ (Mezclas fluidas con alta relación a/c).

#### 7. Agregado Grueso / Grava (`coarse_aggregate`)
* **Unidad:** $kg/m^3$ | **Rango:** $[801.0, 1145.0]$ | **Dispersión:** $CV = 8.0\%$ (mínima)
* **Etiquetas y Funciones:**
  * `Poco`: Hombro Izquierdo $[801.0, 801.0, 930.0, 968.0]$.
  * `Medio`: Triangular $[930.0, 968.0, 1030.0]$ (Centrado en la mediana: $968.0\ kg/m^3$).
  * `Alto`: Hombro Derecho $[968.0, 1030.0, 1145.0, 1145.0]$.

#### 8. Agregado Fino / Arena (`fine_aggregate`)
* **Unidad:** $kg/m^3$ | **Rango:** $[594.0, 992.6]$ | **Dispersión:** $CV = 10.4\%$ (mínima)
* **Etiquetas y Funciones:**
  * `Poco`: Hombro Izquierdo $[594.0, 594.0, 730.0, 779.5]$.
  * `Medio`: Triangular $[730.0, 779.5, 825.0]$ (Centrado en la mediana: $779.5\ kg/m^3$).
  * `Alto`: Hombro Derecho $[779.5, 825.0, 992.6, 992.6]$.

---

## 3. Variable Objetivo: Resistencia a la Compresión (Salida)

#### 9. Resistencia (`compressive_strength`)
*Fundamentada bajo los códigos internacionales **ACI 318**, **ACI 363R** y **Eurocódigo EN 206 / EN 1992**.*
* **Unidad:** $MPa$ | **Rango real:** $[2.33, 82.60]$
* **Etiquetas y Funciones:**
  * `Baja` ($< 20\ MPa$ - No estructural / Concreto pobre):
    * Hombro Izquierdo: $[2.33, 2.33, 15.0, 27.5]$.
  * `Media-Baja` ($20 - 35\ MPa$ - Estructural convencional ACI 318):
    * Triangular: $[15.0, 27.5, 42.5]$ (Cubre 21, 24 y 28 MPa).
  * `Media-Alta` ($35 - 50\ MPa$ - Concreto presforzado y puentes):
    * Triangular: $[27.5, 42.5, 55.0]$ (Cubre 35 a 45 MPa).
  * `Alta` ($\ge 50\ MPa$ - Alta resistencia ACI 363R / HSC):
    * Hombro Derecho: $[42.5, 55.0, 82.6, 82.6]$ (Cubre hasta 82.6 MPa).

---

## 4. Tabla Resumen de Geometrías y Grados de Libertad para el GA

| Variable | Rol | N.° Etiquetas | Tipos de Funciones | Parámetros Ajustables por el GA | Parámetros Fijos (Invariantes) |
|---|:---:|:---:|---|:---:|:---:|
| `blast_furnace_slag` | Entrada | 4 | Singleton + Trap. Izq + Triang + Trap. Der | 7 puntos ($b_{poco}, c_{poco}, a_{med}, b_{med}, c_{med}, a_{alto}, b_{alto}$) | Singleton en 0, extremos min/max |
| `fly_ash` | Entrada | 4 | Singleton + Trap. Izq + Triang + Trap. Der | 7 puntos | Singleton en 0, extremos min/max |
| `superplasticizer` | Entrada | 4 | Singleton + Trap. Izq + Triang + Trap. Der | 7 puntos | Singleton en 0, extremos min/max |
| `age` | Entrada | 4 | Trap. Izq + 2 Triangulares + Trap. Der | 8 puntos | Extremos min=1, max=365 |
| `cement` | Entrada | 3 | Trap. Izq + Triangular + Trap. Der | 5 puntos ($c_{poco}, a_{med}, b_{med}, c_{med}, a_{alto}$) | Extremos min=102, max=540 |
| `water` | Entrada | 3 | Trap. Izq + Triangular + Trap. Der | 5 puntos | Extremos min=121.8, max=247 |
| `coarse_aggregate` | Entrada | 3 | Trap. Izq + Triangular + Trap. Der | 5 puntos | Extremos min=801, max=1145 |
| `fine_aggregate` | Entrada | 3 | Trap. Izq + Triangular + Trap. Der | 5 puntos | Extremos min=594, max=992.6 |
| `compressive_strength` | Salida | 4 | Trap. Izq + 2 Triangulares + Trap. Der | 8 puntos *(o fijos según ACI)* | Umbrales normativos 20, 35, 50 MPa |

---

## 5. Estrategia de Sintonización Paramétrica (*Fuzzy Tuning*)

1. **Longitud del Cromosoma:**
   * Al fijar los ceros y los extremos físicos del dominio, el algoritmo genético solo optimiza los puntos de solape y los centros de los conjuntos difusos.
   * La longitud total del cromosoma oscila entre **49 y 57 genes reales**, un tamaño óptimo para convergencia genética sin dispersión exploratoria.
2. **Restricción de Orden (*Semantic Integrity*):**
   * Para evitar que una función "Poco" se cruce a la derecha de "Medio", el GA utiliza codificación de desplazamientos o penalización de orden ($a \le b \le c$).
3. **Intersección Inicial y Solape (*Ruspini Partition*):**
   * Las funciones se inicializan con un nivel de solape a altura $\alpha = 0.5$ ($\mu_A(x) + \mu_B(x) \approx 1$), garantizando que ningún punto del espacio de entrada quede sin activación de reglas.
