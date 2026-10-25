"""
Ejecuta UNA configuración de medición en Python y escribe el resultado como una línea JSON.
Misma interfaz que java/src/taller/Benchmark.java:

  python3 benchmark.py sort   <datos> <algoritmo> <variante> <n> <repeticiones> <limite_s>
  python3 benchmark.py search <datos> <algoritmo> <modo> <n> <repeticiones> <limite_s>
  python3 benchmark.py extra  <datos> <experimento> <n> <repeticiones> <limite_s>

Tiempos en nanosegundos con time.perf_counter_ns(). CPython no tiene compilación JIT
activada por defecto, por lo que no se hace calentamiento. La lectura de archivos,
la copia del arreglo y la verificación quedan por fuera del tiempo medido.
El límite de recursión se deja en su valor por defecto (sys.getrecursionlimit()).
"""
import json
import os
import sys
import time
from bisect import bisect_left

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ordenamiento  # noqa: E402
import busqueda  # noqa: E402


def leer(ruta):
    with open(ruta) as f:
        return [int(linea) for linea in f if linea.strip()]


def salida(estado, tiempos, error="", detalle=""):
    print(json.dumps({"estado": estado, "error": error, "detalle": detalle,
                      "calentamiento_runs": 0, "tiempos_ns": tiempos,
                      "limite_recursion": sys.getrecursionlimit()}))


def medir_ordenamiento(funcion, original, esperado, reps, limite_ns):
    tiempos = []
    for r in range(reps):
        copia = original.copy()                 # copia nueva, fuera del tiempo
        try:
            t0 = time.perf_counter_ns()
            funcion(copia)
            t1 = time.perf_counter_ns()
        except RecursionError as e:
            salida("error", tiempos, "RecursionError",
                   f"se superó el límite de recursión ({sys.getrecursionlimit()}): {e}")
            return
        if copia != esperado:                   # verificación, fuera del tiempo
            salida("error", tiempos, "VerificacionFallida",
                   f"el arreglo no quedó ordenado en la repetición {r + 1}")
            return
        tiempos.append(t1 - t0)
        if t1 - t0 > limite_ns:
            salida("limite", tiempos, detalle=f"la repetición {r + 1} superó el límite de tiempo")
            return
    salida("ok", tiempos)


def sort(datos, alg, variante, n, reps, limite_s):
    carpeta = os.path.join(datos, f"n_{n}")
    original = leer(os.path.join(carpeta, f"{variante}.txt"))
    esperado = leer(os.path.join(carpeta, "ascendente.txt"))
    medir_ordenamiento(ordenamiento.ALGORITMOS[alg], original, esperado, reps, int(limite_s * 1e9))


def search(datos, alg, modo, n, reps, limite_s):
    carpeta = os.path.join(datos, f"n_{n}")
    ordenado = leer(os.path.join(carpeta, "ascendente.txt"))
    arr = leer(os.path.join(carpeta, "aleatorio.txt")) if modo == "claves_desordenado" else ordenado
    if modo in ("claves", "claves_desordenado"):
        claves = leer(os.path.join(carpeta, "claves.txt"))
    else:
        pos = leer(os.path.join(carpeta, "claves_posicion.txt"))
        c = {"inicio": pos[0], "centro": pos[1], "final": pos[2]}[modo]
        claves = [c] * 1000
    buscar = busqueda.ALGORITMOS[alg]

    # Verificación (fuera del tiempo)
    for x in claves:
        r = buscar(arr, x)
        i = bisect_left(ordenado, x)
        presente = i < len(ordenado) and ordenado[i] == x
        if (r == -1 and presente) or (r != -1 and arr[r] != x):
            salida("error", [], "VerificacionFallida", f"resultado incorrecto para la clave {x}")
            return

    limite_ns = int(limite_s * 1e9)
    tiempos = []
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        for x in claves:
            buscar(arr, x)
        t1 = time.perf_counter_ns()
        tiempos.append(t1 - t0)                 # tiempo TOTAL de las 1.000 búsquedas
        if t1 - t0 > limite_ns:
            salida("limite", tiempos)
            return
    salida("ok", tiempos)


def extra(datos, exp, n, reps, limite_s):
    if exp == "radix16":
        original = leer(os.path.join(datos, "extra", f"16digitos_{n}.txt"))
        funcion = ordenamiento.radix_sort
    elif exp == "bucket_concentrado":
        original = leer(os.path.join(datos, "extra", f"concentrado_{n}.txt"))
        funcion = ordenamiento.bucket_sort
    elif exp == "bucket_rango_pequeno":
        original = leer(os.path.join(datos, "extra", f"rango_pequeno_{n}.txt"))
        funcion = ordenamiento.bucket_sort
    else:
        raise ValueError(exp)
    medir_ordenamiento(funcion, original, sorted(original), reps, int(limite_s * 1e9))


def main():
    modo = sys.argv[1]
    datos = sys.argv[2]
    a = sys.argv[3:]
    if modo == "sort":
        sort(datos, a[0], a[1], int(a[2]), int(a[3]), float(a[4]))
    elif modo == "search":
        search(datos, a[0], a[1], int(a[2]), int(a[3]), float(a[4]))
    elif modo == "extra":
        extra(datos, a[0], int(a[1]), int(a[2]), float(a[3]))
    else:
        raise ValueError(modo)


if __name__ == "__main__":
    main()
