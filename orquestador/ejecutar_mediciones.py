"""
Orquestador de mediciones. Ejecuta cada configuración en un proceso independiente
(un JVM o un intérprete de Python nuevo por configuración) y guarda una línea JSON por
configuración en resultados/crudo/<lenguaje>.jsonl.

Regla de los 5 minutos: antes de ejecutar un tamaño n se predice el tiempo de UNA ejecución
a partir de la medición del tamaño anterior y de la complejidad teórica del caso:
    T(n) ~= T(n_anterior) * g(n) / g(n_anterior)
Si la predicción supera 300 s, la configuración NO se ejecuta y queda para estimación.
Si una repetición real supera 300 s, el programa de medición se detiene y la configuración
también queda como estimada. Los errores (desbordamiento de pila, límite de recursión) se
registran tal cual.

Uso:
  taskset -c 0 python3 orquestador/ejecutar_mediciones.py java
  taskset -c 1 python3 orquestador/ejecutar_mediciones.py python
Se puede interrumpir y reanudar: las configuraciones ya registradas no se repiten.
"""
import json
import math
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, "datos")
CRUDO = os.path.join(RAIZ, "resultados", "crudo")

LIMITE_S = 300.0
REPS = 5
TAMANOS = [1_000, 10_000, 100_000, 1_000_000]
ORDENAMIENTO = ["insertion", "quicksort_dual", "merge", "heap", "radix", "bucket"]
VARIANTES = ["aleatorio", "ascendente", "descendente"]
BUSQUEDA = ["lineal", "binaria", "ternaria", "saltos", "interpolacion", "exponencial"]


def n_log_n(n):
    return n * math.log2(n)


def cuadratica(n):
    return float(n) * n


def lineal(n):
    return float(n)


def g_ordenamiento(alg, variante):
    """Función de crecimiento teórica del caso que corresponde a cada variante de entrada."""
    if alg == "insertion":
        return lineal if variante == "ascendente" else cuadratica
    if alg == "quicksort_dual":
        return n_log_n if variante == "aleatorio" else cuadratica
    if alg in ("merge", "heap"):
        return n_log_n
    return lineal  # radix (d fijo = 8 dígitos) y bucket (caso promedio)


def g_busqueda(alg):
    return {
        "lineal": lineal,
        "binaria": math.log2,
        "ternaria": math.log2,
        "exponencial": math.log2,
        "saltos": math.sqrt,
        "interpolacion": lambda n: math.log2(math.log2(n)),
    }[alg]


def comando(lenguaje, args):
    if lenguaje == "java":
        # Montículo fijo de 2 GB reservado desde el inicio: evita que el redimensionamiento del
        # heap y los fallos de página caigan dentro del tiempo medido.
        return ["java", "-Xms2g", "-Xmx2g", "-XX:+AlwaysPreTouch",
                "-cp", os.path.join(RAIZ, "java", "build"), "taller.Benchmark"] + args
    return [sys.executable, os.path.join(RAIZ, "python", "benchmark.py")] + args


def ejecutar(lenguaje, args, timeout):
    t0 = time.time()
    try:
        p = subprocess.run(comando(lenguaje, args), capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"estado": "limite", "error": "", "detalle": "el proceso superó el tiempo máximo del orquestador",
                "tiempos_ns": [], "calentamiento_runs": 0}
    lineas = [l for l in p.stdout.splitlines() if l.startswith("{")]
    if not lineas:
        err = p.stderr.strip().splitlines()
        return {"estado": "error", "error": "ProcesoFallido", "detalle": " | ".join(err[-3:]),
                "tiempos_ns": [], "calentamiento_runs": 0}
    r = json.loads(lineas[-1])
    r["duracion_proceso_s"] = round(time.time() - t0, 2)
    return r


def cargar(ruta):
    hechos = {}
    if os.path.exists(ruta):
        with open(ruta) as f:
            for l in f:
                r = json.loads(l)
                hechos[r["clave"]] = r
    return hechos


def main():
    lenguaje = sys.argv[1]
    os.makedirs(CRUDO, exist_ok=True)
    ruta = os.path.join(CRUDO, f"{lenguaje}.jsonl")
    hechos = cargar(ruta)
    salida = open(ruta, "a")

    def registrar(clave, base, r):
        r = dict(r)
        r.update(base)
        r["clave"] = clave
        r["lenguaje"] = lenguaje
        salida.write(json.dumps(r, ensure_ascii=False) + "\n")
        salida.flush()
        hechos[clave] = r
        media = (sum(r["tiempos_ns"]) / len(r["tiempos_ns"]) / 1e9) if r.get("tiempos_ns") else None
        print(f"[{time.strftime('%H:%M:%S')}] {lenguaje} {clave}: {r['estado']} "
              f"{r.get('error', '')} media={media}", flush=True)

    def serie(tipo, alg, modo, tamanos, g, args_fn, limite_total):
        ultimo_ok = None      # (n, media_s) del último tamaño medido correctamente
        ultimo_estado = None  # estado del tamaño anterior
        for n in tamanos:
            clave = f"{tipo}|{alg}|{modo}|{n}"
            base = {"tipo": tipo, "algoritmo": alg, "modo": modo, "n": n}
            if clave in hechos:
                r = hechos[clave]
            else:
                pred = None
                if ultimo_ok:
                    pred = ultimo_ok[1] * g(n) / g(ultimo_ok[0])
                # si el tamaño anterior falló (pila/recursión) se ejecuta igual para documentar el error
                previo_fallo = ultimo_estado == "error"
                if pred is not None and pred > LIMITE_S and not previo_fallo:
                    r = {"estado": "omitido_prediccion", "error": "", "tiempos_ns": [],
                         "detalle": f"predicción de una ejecución: {pred:.1f} s > {LIMITE_S:.0f} s",
                         "prediccion_s": pred}
                else:
                    r = ejecutar(lenguaje, args_fn(n, pred), limite_total)
                    if pred is not None:
                        r["prediccion_s"] = pred
                registrar(clave, base, r)
            if r["estado"] == "ok":
                ultimo_ok = (n, sum(r["tiempos_ns"]) / len(r["tiempos_ns"]) / 1e9)
            ultimo_estado = r["estado"]

    timeout_total = LIMITE_S * (REPS + 2) + 300

    # ---------------- Punto 1: ordenamiento
    for alg in ORDENAMIENTO:
        for var in VARIANTES:
            def args_sort(n, pred, alg=alg, var=var):
                a = ["sort", DATOS, alg, var, str(n), str(REPS), str(LIMITE_S)]
                if lenguaje == "java":
                    a.append("prefijo" if (pred is not None and pred > 20) else "completo")
                return a
            serie("sort", alg, var, TAMANOS, g_ordenamiento(alg, var), args_sort, timeout_total)

    # ---------------- Punto 2: búsqueda
    for alg in BUSQUEDA:
        def args_search(n, pred, alg=alg):
            return ["search", DATOS, alg, "claves", str(n), str(REPS), str(LIMITE_S)]
        serie("search", alg, "claves", TAMANOS, g_busqueda(alg), args_search, timeout_total)
    for modo in ["inicio", "centro", "final"]:
        for alg in BUSQUEDA:
            def args_pos(n, pred, alg=alg, modo=modo):
                return ["search", DATOS, alg, modo, str(n), str(REPS), str(LIMITE_S)]
            serie("search", alg, modo, [1_000_000], g_busqueda(alg), args_pos, timeout_total)
    # Búsqueda lineal sobre el arreglo DESORDENADO (Punto 3.2)
    serie("search", "lineal", "claves_desordenado", [1_000_000], lineal,
          lambda n, pred: ["search", DATOS, "lineal", "claves_desordenado", str(n), str(REPS), str(LIMITE_S)],
          timeout_total)

    # ---------------- Punto 3.1: experimentos complementarios
    serie("extra", "radix16", "16digitos", [1_000_000], lineal,
          lambda n, pred: ["extra", DATOS, "radix16", str(n), str(REPS), str(LIMITE_S)], timeout_total)
    serie("extra", "bucket_concentrado", "concentrado", [10_000, 100_000], cuadratica,
          lambda n, pred: ["extra", DATOS, "bucket_concentrado", str(n), str(REPS), str(LIMITE_S)],
          timeout_total)
    serie("extra", "bucket_rango_pequeno", "rango_pequeno", [100_000], lineal,
          lambda n, pred: ["extra", DATOS, "bucket_rango_pequeno", str(n), str(REPS), str(LIMITE_S)],
          timeout_total)

    salida.close()
    print(f"FIN {lenguaje}", flush=True)


if __name__ == "__main__":
    main()
