"""
Consolida las mediciones crudas (resultados/crudo/*.jsonl) en los archivos de resultados:

  resultados/ordenamiento.csv / .json   Punto 1
  resultados/busqueda.csv / .json       Punto 2 (incluye posiciones de clave y la lineal desordenada)
  resultados/experimentos_extra.csv     Punto 3.1 (Radix 16 dígitos, Bucket concentrado)

Para cada configuración que no se pudo medir (predicción > 5 min, repetición > 5 min o error
de ejecución) se calcula un tiempo ESTIMADO:
    T_est(n) = T_med(n_ref) * g(n) / g(n_ref)
donde n_ref es el mayor tamaño medido del mismo algoritmo, lenguaje y variante, y g es la
función de crecimiento teórica del caso (n, n log n o n^2). El registro queda marcado como
'estimado' y la columna 'observacion' explica el motivo y el cálculo.
"""
import csv
import json
import math
import os
import statistics
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "orquestador"))
from ejecutar_mediciones import g_ordenamiento, g_busqueda, lineal, cuadratica  # noqa: E402

RES = os.path.join(RAIZ, "resultados")
NOMBRE_G = {"lineal": "n", "n_log_n": "n log n", "cuadratica": "n²", "log2": "log n",
            "sqrt": "√n", "<lambda>": "log log n"}


def cargar():
    filas = []
    for lang in ("java", "python"):
        ruta = os.path.join(RES, "crudo", f"{lang}.jsonl")
        if not os.path.exists(ruta):
            continue
        with open(ruta) as f:
            vistos = {}
            for l in f:
                r = json.loads(l)
                vistos[r["clave"]] = r       # si una clave se repitió, vale la última
            filas.extend(vistos.values())
    return filas


def describir_error(r):
    if r["error"] == "StackOverflowError":
        return ("StackOverflowError: la recursión del QuickSort superó la pila del hilo principal de la JVM "
                "(tamaño por defecto)")
    if r["error"] == "RecursionError":
        return ("RecursionError: la profundidad de recursión superó el límite por defecto de Python "
                f"({r.get('limite_recursion', 1000)} marcos)")
    return f"{r['error']}: {r.get('detalle', '')}"


def procesar(filas, tipo, g_fn, factor=1.0):
    """factor: divisor aplicado a cada tiempo (1000 para pasar de total de 1.000 búsquedas a por búsqueda)."""
    grupos = {}
    for r in filas:
        if r["tipo"] != tipo:
            continue
        grupos.setdefault((r["lenguaje"], r["algoritmo"], r["modo"]), []).append(r)
    salida = []
    for (lang, alg, modo), rs in grupos.items():
        rs.sort(key=lambda r: r["n"])
        g = g_fn(alg, modo)
        medidos = {}
        for r in rs:
            t = [x / factor for x in r["tiempos_ns"]]
            reg = {"algoritmo": alg, "lenguaje": lang, "variante": modo, "n": r["n"],
                   "repeticiones_ns": t, "estado": r["estado"]}
            if r["estado"] == "ok":
                reg["promedio_ns"] = statistics.mean(t)
                reg["desviacion_ns"] = statistics.stdev(t) if len(t) > 1 else 0.0
                reg["tipo"] = "medido"
                reg["observacion"] = ""
                medidos[r["n"]] = reg["promedio_ns"]
            else:
                refs = [n for n in medidos if n < r["n"]]
                if refs:
                    n_ref = max(refs)
                    est = medidos[n_ref] * g(r["n"]) / g(n_ref)
                    calculo = (f"T({n_ref:,}) × g({r['n']:,})/g({n_ref:,}) con g = "
                               f"{NOMBRE_G.get(g.__name__, g.__name__)}").replace(",", ".")
                else:
                    est, calculo = float("nan"), "sin tamaño de referencia"
                if r["estado"] == "omitido_prediccion":
                    motivo = f"No ejecutado: se predijo {r['prediccion_s']:.0f} s por ejecución (> 300 s)."
                elif r["estado"] == "limite":
                    obs = r["tiempos_ns"][0] / factor / 1e9 if r["tiempos_ns"] else None
                    motivo = ("Detenido: una repetición superó 300 s"
                              + (f" (tardó {obs:.0f} s)." if obs else "."))
                else:
                    motivo = "Falló en ejecución. " + describir_error(r) + "."
                reg.update(promedio_ns=est, desviacion_ns=None, tipo="estimado",
                           observacion=f"{motivo} Estimado = {calculo}.")
            salida.append(reg)
    orden = {"java": 0, "python": 1}
    salida.sort(key=lambda r: (orden[r["lenguaje"]], r["algoritmo"], r["variante"], r["n"]))
    return salida


def escribir(registros, nombre, etiqueta_rep):
    ruta_csv = os.path.join(RES, f"{nombre}.csv")
    cab = ["algoritmo", "lenguaje", "variante", "n"] + [f"rep{i}_{etiqueta_rep}" for i in range(1, 6)] + \
          [f"promedio_{etiqueta_rep}", f"desviacion_{etiqueta_rep}", "tipo", "estado", "observacion"]
    with open(ruta_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cab)
        for r in registros:
            reps = r["repeticiones_ns"] if r["tipo"] == "medido" else []
            reps = [f"{x:.1f}" for x in reps] + [""] * (5 - len(reps))
            prom = "" if r["promedio_ns"] is None or math.isnan(r["promedio_ns"]) else f"{r['promedio_ns']:.1f}"
            desv = "" if r["desviacion_ns"] is None else f"{r['desviacion_ns']:.1f}"
            w.writerow([r["algoritmo"], r["lenguaje"], r["variante"], r["n"]] + reps +
                       [prom, desv, r["tipo"], r["estado"], r["observacion"]])
    with open(os.path.join(RES, f"{nombre}.json"), "w") as f:
        json.dump(registros, f, ensure_ascii=False, indent=1)
    print(f"{ruta_csv}: {len(registros)} registros")


def main():
    filas = cargar()
    sort = procesar(filas, "sort", g_ordenamiento)
    escribir(sort, "ordenamiento", "ns")
    busq = procesar(filas, "search", lambda alg, modo: g_busqueda(alg), factor=1000.0)
    escribir(busq, "busqueda", "ns_por_busqueda")
    extra = procesar(filas, "extra", lambda alg, modo: lineal if alg in ("radix16", "bucket_rango_pequeno") else cuadratica)
    escribir(extra, "experimentos_extra", "ns")


if __name__ == "__main__":
    main()
