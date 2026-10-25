"""
Cuenta cuántos elementos del arreglo revisa cada algoritmo de búsqueda (lecturas arr[i]).
No mide tiempo: sirve para explicar las mediciones del Punto 2 con el orden en que cada
algoritmo recorre el arreglo. Usa exactamente las funciones de python/busqueda.py sobre una
lista que cuenta sus accesos.

Salida: resultados/conteo_accesos.json
  - por posición de la clave (inicio, centro, final) con n = 1.000.000
  - promedio sobre las 1.000 claves de búsqueda para cada n
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "python"))
import busqueda  # noqa: E402


class ListaContadora(list):
    lecturas = 0

    def __getitem__(self, i):
        ListaContadora.lecturas += 1
        return list.__getitem__(self, i)


def leer(ruta):
    with open(ruta) as f:
        return [int(l) for l in f if l.strip()]


def contar(fn, arr, x):
    ListaContadora.lecturas = 0
    fn(arr, x)
    return ListaContadora.lecturas


def main():
    salida = {"posicion": {}, "promedio_claves": {}}
    for n in (1_000, 10_000, 100_000, 1_000_000):
        carpeta = os.path.join(RAIZ, "datos", f"n_{n}")
        arr = ListaContadora(leer(os.path.join(carpeta, "ascendente.txt")))
        claves = leer(os.path.join(carpeta, "claves.txt"))
        for alg, fn in busqueda.ALGORITMOS.items():
            if alg == "lineal" and n == 1_000_000:
                muestra = claves[:100]          # la lineal es lenta de instrumentar; basta una muestra
            else:
                muestra = claves
            prom = sum(contar(fn, arr, x) for x in muestra) / len(muestra)
            salida["promedio_claves"].setdefault(alg, {})[n] = prom
        if n == 1_000_000:
            pos = leer(os.path.join(carpeta, "claves_posicion.txt"))
            for alg, fn in busqueda.ALGORITMOS.items():
                salida["posicion"][alg] = {m: contar(fn, arr, x) for m, x in zip(("inicio", "centro", "final"), pos)}
        print(f"n={n} listo")
    with open(os.path.join(RAIZ, "resultados", "conteo_accesos.json"), "w") as f:
        json.dump(salida, f, indent=1)
    print(json.dumps(salida["posicion"], indent=1))


if __name__ == "__main__":
    main()
