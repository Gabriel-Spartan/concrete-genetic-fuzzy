# Análisis exploratorio del dataset Concrete Compressive Strength

## 1. Estado general del dataset

El dataset contiene 1030 observaciones, 8 variables de entrada y una variable objetivo (`compressive_strength`). No se detectaron valores faltantes en ninguna columna.

Las escalas originales son físicamente interpretables:

- componentes de la mezcla: kg/m³;
- edad: días;
- resistencia: MPa.

Por esta razón, para la futura construcción del sistema difuso no conviene transformar automáticamente todas las variables a valores estandarizados o normalizados.

## 2. Estadística descriptiva relevante

| Variable | Mínimo | Mediana | Máximo | Asimetría |
|---|---:|---:|---:|---:|
| Cement | 102.0 | 272.9 | 540.0 | 0.510 |
| Blast furnace slag | 0.0 | 22.0 | 359.4 | 0.801 |
| Fly ash | 0.0 | 0.0 | 200.1 | 0.537 |
| Water | 121.8 | 185.0 | 247.0 | 0.075 |
| Superplasticizer | 0.0 | 6.4 | 32.2 | 0.907 |
| Coarse aggregate | 801.0 | 968.0 | 1145.0 | -0.040 |
| Fine aggregate | 594.0 | 779.5 | 992.6 | -0.253 |
| Age | 1 | 28 | 365 | 3.269 |
| Compressive strength | 2.33 | 34.445 | 82.6 | 0.417 |

## 3. Variables con concentración en cero

La concentración en cero no debe interpretarse como un problema de escala.

| Variable | Valores exactamente 0 | Porcentaje |
|---|---:|---:|
| Blast furnace slag | 471 | 45.73 % |
| Fly ash | 566 | 54.95 % |
| Superplasticizer | 379 | 36.80 % |

En estas variables, cero tiene significado físico: el componente no forma parte de la mezcla. Por tanto, sustituir, eliminar o suavizar automáticamente estos ceros sería incorrecto.

Además, al analizar solamente los valores mayores que cero:

- `blast_furnace_slag` deja de estar fuertemente sesgada;
- `fly_ash` presenta una distribución relativamente equilibrada dentro de sus valores positivos;
- `superplasticizer` todavía presenta una cola hacia valores altos.

Esto indica que la gran barra observada alrededor de cero en los histogramas representa principalmente ausencia del componente, no un error de medición.

## 4. Edad

`age` es la variable más claramente no normal:

- asimetría: 3.269;
- solo existen 14 edades diferentes;
- 425 de las 1030 observaciones corresponden a 28 días;
- los valores más frecuentes son 28, 3, 7, 56 y 14 días.

La distribución discreta responde a edades de ensayo utilizadas en concreto y no debe corregirse como si fuera un defecto del dataset.

La correlación con la resistencia es:

- Pearson: 0.329;
- Spearman: 0.596.

La diferencia muestra una relación monotónica importante, pero no lineal. Como comprobación adicional, `log(1 + age)` aumenta la correlación lineal de Pearson hasta aproximadamente 0.549.

Esto no implica que deba reemplazarse la edad original por su logaritmo dentro del sistema difuso. Los días reales conservan mucha más interpretación. La transformación logarítmica es útil como evidencia de la no linealidad.

## 5. Correlación con la resistencia

### Pearson

| Variable | Correlación |
|---|---:|
| Cement | 0.498 |
| Superplasticizer | 0.366 |
| Age | 0.329 |
| Blast furnace slag | 0.135 |
| Fly ash | -0.106 |
| Coarse aggregate | -0.165 |
| Fine aggregate | -0.167 |
| Water | -0.290 |

### Spearman

| Variable | Correlación |
|---|---:|
| Age | 0.596 |
| Cement | 0.478 |
| Superplasticizer | 0.348 |
| Blast furnace slag | 0.164 |
| Fly ash | -0.078 |
| Fine aggregate | -0.180 |
| Coarse aggregate | -0.184 |
| Water | -0.308 |

No debe descartarse una variable solo porque su correlación individual sea baja. El problema es multivariable y las propiedades del concreto dependen de interacciones entre componentes.

Entre predictores, la relación lineal de mayor magnitud encontrada fue `water` frente a `superplasticizer`, con aproximadamente -0.658. No se observan correlaciones cercanas a ±1 que obliguen a eliminar alguna variable por redundancia lineal extrema.

## 6. Relación agua/cemento

La relación:

`water_cement_ratio = water / cement`

presenta:

- Pearson con resistencia: aproximadamente -0.501;
- Spearman con resistencia: aproximadamente -0.522.

La relación negativa es más clara que la observada con `water` por sí sola. Esto confirma que la interacción entre agua y cemento contiene información importante.

Por ahora conviene mantenerla como variable derivada de análisis. Más adelante se puede evaluar si usarla como antecedente de reglas o incluso sustituir parcialmente la combinación `water + cement`, evitando introducir redundancia innecesaria.

## 7. Outliers

Los outliers detectados mediante la regla 1.5×IQR fueron aproximadamente:

- slag: 2;
- water: 9;
- superplasticizer: 10;
- fine aggregate: 5;
- age: 59;
- compressive strength: 4.

No deben eliminarse automáticamente.

En especial, los valores altos de `age` (180, 270, 360 y 365 días) son ensayos de curado prolongado y tienen sentido físico. El hecho de que un boxplot los marque como outliers responde a la distribución concentrada en edades tempranas, no necesariamente a datos erróneos.

## 8. Duplicados

Se encontraron:

- 25 filas completamente duplicadas;
- 38 filas cuyo vector de 8 entradas aparece repetido;
- 19 grupos de combinaciones de entrada repetidas;
- 9 de esos grupos tienen resistencias distintas para exactamente las mismas entradas.

Las filas completamente idénticas no añaden nueva información y pueden producir fuga de información si una copia cae en entrenamiento y otra en prueba. Se recomienda eliminarlas antes de dividir el dataset.

Las combinaciones con las mismas entradas pero diferente resistencia no deberían eliminarse automáticamente, porque pueden representar variabilidad experimental.

Para una evaluación rigurosa, cuando se haga la división entrenamiento/validación/prueba, conviene mantener juntas las observaciones con exactamente el mismo vector de entrada.

## 9. Decisión sobre normalización y estandarización

### Sistema difuso

**No normalizar ni estandarizar el dataset de entrada de forma global.**

Motivos:

1. las unidades físicas son interpretables;
2. los ceros de slag, fly ash y superplasticizer significan ausencia;
3. las distribuciones no son homogéneas;
4. las funciones de pertenencia pueden construirse directamente sobre los dominios físicos;
5. aplicar z-score dificultaría interpretar reglas como “agua alta” o “cemento bajo”.

### Algoritmo genético

Más adelante sí es recomendable representar internamente los parámetros que optimice el algoritmo genético en un intervalo común, por ejemplo `[0, 1]`.

Esto facilita:

- mutación;
- cruce;
- límites;
- comparación de magnitudes.

Después esos genes pueden transformarse nuevamente a unidades reales antes de evaluar las funciones de pertenencia.

### Estandarización z-score

No se recomienda como transformación principal para este sistema genético-difuso.

### Min-Max

Puede resultar útil como representación interna del cromosoma del GA, pero no es necesario reemplazar los datos físicos originales.

## 10. Tratamiento recomendado por variable

| Variable | Tratamiento actual recomendado |
|---|---|
| Cement | Mantener escala original |
| Blast furnace slag | Mantener escala; tratar 0 como ausencia real |
| Fly ash | Mantener escala; tratar 0 como ausencia real |
| Water | Mantener escala original |
| Superplasticizer | Mantener escala; tratar 0 como ausencia real |
| Coarse aggregate | Mantener escala original |
| Fine aggregate | Mantener escala original |
| Age | Mantener días; considerar funciones de pertenencia no uniformes |
| Compressive strength | Mantener MPa |
| Water/Cement ratio | Mantener como variable derivada para análisis por ahora |

## 11. Preparación recomendada antes del sistema difuso

La versión procesada inicial debería realizar únicamente limpieza conservadora:

1. cargar `dataset.csv`;
2. renombrar columnas;
3. eliminar duplicados completamente idénticos;
4. conservar ceros reales;
5. conservar outliers plausibles;
6. conservar las unidades originales;
7. guardar el resultado como `data/processed/dataset_clean.csv`.

Todavía no conviene generar una versión normalizada o estandarizada.

La siguiente etapa debe concentrarse en estudiar los dominios de cada variable para definir funciones de pertenencia coherentes con:

- distribución de los datos;
- significado físico;
- concentración de valores en cero;
- comportamiento no lineal;
- relación con la resistencia.
