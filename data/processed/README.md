# Datos Procesados y Particiones

En este directorio se almacenan los datasets generados por las etapas de limpieza, fuzificación y división estratificada:

## Archivos Principales
* `dataset_clean.csv`: Dataset UCI filtrado (1005 observaciones) tras eliminar 25 filas duplicadas exactas.
* `fuzzy_matrix.csv`: Matriz difusa continua ($1005 \times 32$ columnas) con los grados de pertenencia $\mu(x) \in [0, 1]$ evaluados con las funciones Ruspini iniciales.
* `dataset_discretized.csv`: Dataset con etiquetas lingüísticas discretas asignadas por máxima pertenencia ($\operatorname{argmax} \mu_i$), insumo directo para el algoritmo PRISM.

## Subdirectorio `splits/`
Partición estratificada 70% Train / 15% Val / 15% Test manteniendo la distribución de las 4 clases de resistencia:
* `train_clean.csv`, `val_clean.csv`, `test_clean.csv`: Muestras con valores continuos originales en unidades físicas ($kg/m^3$, días, $MPa$).
* `train_discretized.csv`, `val_discretized.csv`, `test_discretized.csv`: Muestras con etiquetas lingüísticas para inducción y validación de reglas PRISM.
* `train_fuzzy.csv`, `val_fuzzy.csv`, `test_fuzzy.csv`: Matrices difusas correspondientes a cada partición.
