"""
Punto 3.2 — ¿Ordenar o no ordenar?

Con n = 1.000.000 y k búsquedas sobre un arreglo DESORDENADO:
  Estrategia A: k búsquedas lineales               costo_A(k) = k * t_lineal
  Estrategia B: ordenar una vez + k binarias       costo_B(k) = t_orden + k * t_binaria
B conviene cuando t_orden + k*t_binaria < k*t_lineal, es decir, cuando
  k > k* = t_orden / (t_lineal - t_binaria).
Todos los tiempos son mediciones propias:
  t_orden   = mejor promedio MEDIDO entre los 6 algoritmos (entrada aleatoria, n = 1.000.000)
  t_lineal  = promedio por búsqueda de la búsqueda lineal sobre el arreglo aleatorio (sin ordenar)
  t_binaria = promedio por búsqueda de la búsqueda binaria sobre el arreglo ascendente
Salida: resultados/punto3_k.json
"""
import json
import math
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(RAIZ, "resultados")
NOM = {"insertion": "Insertion Sort", "quicksort_dual": "Dual-Pivot QuickSort", "merge": "Merge Sort",
       "heap": "Heap Sort", "radix": "Radix Sort", "bucket": "Bucket Sort"}


def main():
    sort = json.load(open(os.path.join(RES, "ordenamiento.json")))
    bus = json.load(open(os.path.join(RES, "busqueda.json")))
    salida = {}
    for lang in ("java", "python"):
        cands = [r for r in sort if r["lenguaje"] == lang and r["variante"] == "aleatorio"
                 and r["n"] == 1_000_000 and r["tipo"] == "medido"]
        mejor = min(cands, key=lambda r: r["promedio_ns"])
        t_lin = next(r for r in bus if r["lenguaje"] == lang and r["algoritmo"] == "lineal"
                     and r["variante"] == "claves_desordenado" and r["n"] == 1_000_000)["promedio_ns"]
        t_bin = next(r for r in bus if r["lenguaje"] == lang and r["algoritmo"] == "binaria"
                     and r["variante"] == "claves" and r["n"] == 1_000_000)["promedio_ns"]
        k_eq = mejor["promedio_ns"] / (t_lin - t_bin)
        salida[lang] = {
            "algoritmo_orden": mejor["algoritmo"], "nombre_orden": NOM[mejor["algoritmo"]],
            "t_orden_s": mejor["promedio_ns"] / 1e9, "t_lineal_s": t_lin / 1e9, "t_binaria_s": t_bin / 1e9,
            "k_equilibrio": k_eq, "k_min": math.floor(k_eq) + 1,
        }
        print(lang, salida[lang])
    json.dump(salida, open(os.path.join(RES, "punto3_k.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
