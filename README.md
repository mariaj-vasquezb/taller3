# Taller de ordenamiento y búsqueda

Comparación experimental de 6 algoritmos de ordenamiento y 6 de búsqueda, implementados con la
misma estructura en **Java 21** (compilado, JIT HotSpot) y **Python 3.13** (interpretado, CPython).

## Estructura

```
generar_datos.py               Genera TODOS los datos de prueba con semilla fija (2026)
datos/                         (se genera con generar_datos.py, no está en el repositorio)
  n_<n>/aleatorio.txt          n enteros aleatorios de 8 dígitos (n = 1.000 … 1.000.000)
  n_<n>/ascendente.txt         los mismos datos ordenados ascendentemente
  n_<n>/descendente.txt        los mismos datos ordenados descendentemente
  n_<n>/claves.txt             1.000 claves de búsqueda (500 presentes, 500 ausentes)
  n_<n>/claves_posicion.txt    claves al inicio, centro y final del arreglo ascendente
  extra/                       datos de los experimentos complementarios del Punto 3
java/src/taller/
  Ordenamiento.java            Insertion, Dual-Pivot QuickSort, Merge, Heap, Radix, Bucket
  Busqueda.java                Lineal, Binaria, Ternaria, Saltos, Interpolación, Exponencial
  Benchmark.java               Mide UNA configuración e imprime una línea JSON
python/
  ordenamiento.py, busqueda.py Misma implementación en Python
  benchmark.py                 Misma interfaz que Benchmark.java
orquestador/
  ejecutar_mediciones.py       Recorre todas las configuraciones (un proceso por configuración),
                               aplica la regla de los 5 minutos y guarda resultados/crudo/*.jsonl
analisis/
  consolidar.py                Genera los CSV/JSON finales y calcula los valores estimados
  punto3.py                    Cálculo del punto de equilibrio k (Punto 3.2)
  conteo_accesos.py            Cuenta cuántos elementos revisa cada búsqueda (apoya el Punto 2)
  graficas.py                  Genera todas las gráficas (graficas/*.png)
resultados/
  ordenamiento.csv / .json     Punto 1: un registro por algoritmo, lenguaje, variante y n
  busqueda.csv / .json         Punto 2: tiempo por búsqueda (incluye posición de la clave)
  conteo_accesos.json          Punto 2: elementos revisados por cada algoritmo de búsqueda
  experimentos_extra.csv/.json Punto 3.1: Radix con 16 dígitos, Bucket con datos concentrados
  punto3_k.json                Punto 3.2
  entorno.txt                  Máquina, sistema y versiones usadas
  crudo/                       Salida sin procesar de cada medición y registros de ejecución
graficas/                      Gráficas de resultados (PNG)
```

## Cómo reproducir

Requisitos: JDK 21+ y Python 3.10+ con `matplotlib`.

```bash
python3 generar_datos.py                                  # 1. datos (semilla fija, ~46 MB)
javac -d java/build java/src/taller/*.java                # 2. compilar Java
taskset -c 0 python3 orquestador/ejecutar_mediciones.py java    # 3. medir (Linux; sin taskset en otros SO)
taskset -c 1 python3 orquestador/ejecutar_mediciones.py python
python3 analisis/consolidar.py                            # 4. resultados finales + estimaciones
python3 analisis/punto3.py
python3 analisis/conteo_accesos.py
python3 analisis/graficas.py                              # 5. gráficas
```

La medición completa tarda cerca de una hora (los casos más largos son Insertion Sort con
n = 1.000.000 en Java y con n = 100.000 en Python). El orquestador puede interrumpirse y
reanudarse: no repite las configuraciones ya registradas.

## Formato de los resultados

Cada fila de `resultados/ordenamiento.csv` contiene: `algoritmo, lenguaje, variante, n,
rep1_ns … rep5_ns, promedio_ns, desviacion_ns, tipo (medido|estimado), estado, observacion`.
En `busqueda.csv` los tiempos son **por búsqueda** (tiempo total de las 1.000 búsquedas ÷ 1.000).
Cuando `tipo = estimado`, la columna `observacion` explica por qué no se midió (predicción de más de
5 minutos o error de ejecución) y cómo se calculó la estimación.

## Fuentes de los algoritmos

GeeksforGeeks: [Insertion Sort](https://www.geeksforgeeks.org/insertion-sort-algorithm/),
[Dual-Pivot QuickSort](https://www.geeksforgeeks.org/dual-pivot-quicksort/),
[Merge Sort](https://www.geeksforgeeks.org/merge-sort/),
[Heap Sort](https://www.geeksforgeeks.org/heap-sort/),
[Radix Sort](https://www.geeksforgeeks.org/radix-sort/),
[Bucket Sort](https://www.geeksforgeeks.org/bucket-sort-2/),
[Linear Search](https://www.geeksforgeeks.org/linear-search/),
[Binary Search](https://www.geeksforgeeks.org/binary-search/),
[Ternary Search](https://www.geeksforgeeks.org/ternary-search/),
[Jump Search](https://www.geeksforgeeks.org/jump-search/),
[Interpolation Search](https://www.geeksforgeeks.org/interpolation-search/),
[Exponential Search](https://www.geeksforgeeks.org/exponential-search/).
Las adaptaciones (Bucket Sort para enteros, fórmula de interpolación) están documentadas en el código.
