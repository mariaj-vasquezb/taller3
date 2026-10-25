"""
Genera todas las gráficas del informe a partir de resultados/ordenamiento.json,
resultados/busqueda.json y resultados/experimentos_extra.json.

Convenciones (todas las gráficas):
  - eje del tiempo en escala logarítmica;
  - valores MEDIDOS: línea continua y marcador relleno / barra sólida;
  - valores ESTIMADOS: línea punteada y marcador hueco / barra rayada con "≈" en la etiqueta;
  - en los gráficos de barras, el valor de tiempo aparece sobre cada barra.
"""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FixedLocator, FuncFormatter, LogLocator, NullFormatter  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(RAIZ, "resultados")
OUT = os.path.join(RAIZ, "graficas")
os.makedirs(OUT, exist_ok=True)

# Paleta categórica validada (orden fijo) y tokens de texto/rejilla
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
MARCADORES = ["o", "s", "D", "^", "v", "P"]
TXT1, TXT2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#ffffff"

plt.rcParams.update({
    "font.family": ["Inter", "DejaVu Sans"],
    "font.size": 9,
    "axes.edgecolor": GRID, "axes.labelcolor": TXT2, "axes.titlecolor": TXT1,
    "axes.titlesize": 11, "axes.titleweight": "semibold", "axes.titlelocation": "left",
    "xtick.color": TXT2, "ytick.color": TXT2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "legend.frameon": False, "legend.fontsize": 8.5,
})

ORD = ["insertion", "quicksort_dual", "merge", "heap", "radix", "bucket"]
NOM_ORD = {"insertion": "Insertion Sort", "quicksort_dual": "Dual-Pivot QuickSort", "merge": "Merge Sort",
           "heap": "Heap Sort", "radix": "Radix Sort", "bucket": "Bucket Sort"}
BUS = ["lineal", "binaria", "ternaria", "saltos", "interpolacion", "exponencial"]
NOM_BUS = {"lineal": "Lineal", "binaria": "Binaria", "ternaria": "Ternaria", "saltos": "Saltos (Jump)",
           "interpolacion": "Interpolación", "exponencial": "Exponencial"}
NOM_LANG = {"java": "Java (compilado)", "python": "Python (interpretado)"}
TAM = [1_000, 10_000, 100_000, 1_000_000]


def cargar(nombre):
    with open(os.path.join(RES, f"{nombre}.json")) as f:
        return json.load(f)


def indice(regs):
    return {(r["lenguaje"], r["algoritmo"], r["variante"], r["n"]): r for r in regs}


def fmt_t(seg):
    """Formatea un tiempo en segundos con la unidad adecuada (coma decimal)."""
    if seg is None or (isinstance(seg, float) and math.isnan(seg)):
        return "—"
    for lim, div, u in ((1e-6, 1e-9, "ns"), (1e-3, 1e-6, "µs"), (1, 1e-3, "ms"), (120, 1, "s"),
                        (7200, 60, "min"), (172800, 3600, "h")):
        if seg < lim:
            v = seg / div
            break
    else:
        v, u = seg / 86400, "días"
    txt = f"{v:.3g}" if v < 100 else f"{v:.0f}"
    return f"{txt.replace('.', ',')} {u}"


# Marcas "redondas" del eje de tiempo, en segundos (décadas de ns a s, luego min y h)
MARCAS_T = [10.0 ** e for e in range(-10, 2)] + [60, 600, 3600, 36000, 360000]
ETIQ_T = {60: "1 min", 600: "10 min", 3600: "1 h", 36000: "10 h", 360000: "100 h"}


def eje_tiempo(ax):
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(FixedLocator(MARCAS_T))
    ax.yaxis.set_minor_locator(LogLocator(base=10, subs=range(2, 10), numticks=40))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: ETIQ_T.get(v, fmt_t(v))))


def eje_n(ax):
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(FixedLocator(TAM))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v):,}".replace(",", ".")))
    ax.set_xlim(700, 1.45e6)
    ax.set_xlabel("Tamaño del arreglo (n)")
    ax.grid(axis="x", visible=False)


def guardar(fig, nombre):
    fig.savefig(os.path.join(OUT, nombre), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("gráfica:", nombre)


def leyenda_estilo():
    return [Line2D([], [], color=MUTED, lw=2, marker="o", ms=6, label="Medido"),
            Line2D([], [], color=MUTED, lw=1.6, ls=(0, (3, 2)), marker="o", ms=6, mfc=SURF, label="Estimado")]


# ---------------------------------------------------------------- líneas de crecimiento
def grafica_crecimiento(idx, algs, nombres, lang, variante, titulo, subtitulo, ylabel, archivo):
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    handles = []
    hay_est = False
    for i, alg in enumerate(algs):
        c, m = SERIES[i], MARCADORES[i]
        pts = [(n, idx.get((lang, alg, variante, n))) for n in TAM]
        pts = [(n, r["promedio_ns"] / 1e9, r["tipo"]) for n, r in pts if r and r["promedio_ns"] is not None]
        med = [(n, t) for n, t, tp in pts if tp == "medido"]
        est = [(n, t) for n, t, tp in pts if tp == "estimado"]
        if med:
            ax.plot(*zip(*med), color=c, lw=2, marker=m, ms=6, mec=SURF, mew=1.2, zorder=3,
                    solid_capstyle="round")
        if est:
            hay_est = True
            puente = ([med[-1]] if med else []) + est
            ax.plot(*zip(*puente), color=c, lw=1.6, ls=(0, (3, 2)), zorder=2)
            ax.plot(*zip(*est), ls="none", marker=m, ms=6, mfc=SURF, mec=c, mew=1.6, zorder=3)
        handles.append(Line2D([], [], color=c, lw=2, marker=m, ms=6, mec=SURF, label=nombres[alg]))
    eje_n(ax)
    eje_tiempo(ax)
    ax.set_ylabel(ylabel)
    ax.set_title(titulo, pad=22)
    ax.text(0, 1.02, subtitulo, transform=ax.transAxes, color=TXT2, fontsize=8.5)
    estilo = leyenda_estilo() if hay_est else leyenda_estilo()[:1]
    ax.legend(handles=handles + estilo, loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0)
    guardar(fig, archivo)


# ---------------------------------------------------------------- barras agrupadas
def grafica_barras(grupos, series, valor, titulo, subtitulo, ylabel, archivo, ancho_fig=7.6):
    """grupos: lista de (clave, etiqueta). series: lista de (clave, etiqueta, color).
    valor(gk, sk) -> (segundos, tipo) o None."""
    fig, ax = plt.subplots(figsize=(ancho_fig, 4.6))
    k = len(series)
    w = 0.8 / k
    vals = []
    hay_est = False
    for gi, (gk, _) in enumerate(grupos):
        for si, (sk, _, col) in enumerate(series):
            v = valor(gk, sk)
            if not v or v[0] is None or (isinstance(v[0], float) and math.isnan(v[0])):
                continue
            t, tipo = v
            vals.append(t)
            x = gi + (si - (k - 1) / 2) * w
            est = tipo == "estimado"
            hay_est = hay_est or est
            ax.bar(x, t, width=w * 0.88, bottom=None, color=(col if not est else SURF),
                   edgecolor=col, hatch=("////" if est else None), linewidth=(1.2 if est else 0), zorder=3)
            etiqueta = ("≈ " if est else "") + fmt_t(t)
            ax.text(x, t * 1.12, etiqueta, ha="center", va="bottom", rotation=90, fontsize=7, color=TXT1,
                    zorder=4)
    eje_tiempo(ax)
    lo = 10 ** math.floor(math.log10(min(vals)) - 0.6)
    hi = 10 ** math.ceil(math.log10(max(vals)) + 1.3)
    ax.set_ylim(lo, hi)
    ax.set_xticks(range(len(grupos)))
    ax.set_xticklabels([e for _, e in grupos])
    ax.grid(axis="x", visible=False)
    ax.set_ylabel(ylabel)
    ax.set_title(titulo, pad=22)
    ax.text(0, 1.02, subtitulo, transform=ax.transAxes, color=TXT2, fontsize=8.5)
    hs = [Patch(color=col, label=lab) for _, lab, col in series]
    if hay_est:
        hs.append(Patch(facecolor=SURF, edgecolor=MUTED, hatch="////", label="Estimado (no medido)"))
    ax.legend(handles=hs, loc="upper left", ncol=len(hs), bbox_to_anchor=(0, -0.2), borderaxespad=0)
    guardar(fig, archivo)


def main():
    so = indice(cargar("ordenamiento"))
    bu = indice(cargar("busqueda"))
    ex = indice(cargar("experimentos_extra"))

    def v_sort(lang, alg, var, n):
        r = so.get((lang, alg, var, n))
        return (r["promedio_ns"] / 1e9, r["tipo"]) if r else None

    # ---- Punto 1: crecimiento (2 gráficas)
    for lang in ("java", "python"):
        grafica_crecimiento(so, ORD, NOM_ORD, lang, "aleatorio",
                            f"Ordenamiento: crecimiento del tiempo en {NOM_LANG[lang]}",
                            "Entrada aleatoria · promedio de 5 repeticiones · escala log-log",
                            "Tiempo por ordenamiento", f"p1_crecimiento_{lang}.png")

    # ---- Punto 1: efecto del orden de entrada (3 gráficas, Java)
    var_series = [("aleatorio", "Aleatoria", SERIES[0]), ("ascendente", "Ascendente", SERIES[1]),
                  ("descendente", "Descendente", SERIES[2])]
    grupos_ord = [(a, NOM_ORD[a].replace(" Sort", "\nSort").replace("Dual-Pivot ", "Dual-Pivot\n"))
                  for a in ORD]
    for n in (1_000, 10_000, 100_000):
        grafica_barras(grupos_ord, var_series, lambda a, v, n=n: v_sort("java", a, v, n),
                       f"Efecto del orden de entrada · n = {n:,}".replace(",", "."),
                       "Java (compilado) · promedio de 5 repeticiones · eje logarítmico",
                       "Tiempo por ordenamiento", f"p1_orden_entrada_n{n}.png")

    # ---- Punto 1: compilado vs interpretado n = 1.000.000
    lang_series = [("java", NOM_LANG["java"], SERIES[0]), ("python", NOM_LANG["python"], SERIES[1])]
    grafica_barras(grupos_ord, lang_series, lambda a, l: v_sort(l, a, "aleatorio", 1_000_000),
                   "Ordenamiento: compilado frente a interpretado · n = 1.000.000",
                   "Entrada aleatoria · promedio de 5 repeticiones · eje logarítmico",
                   "Tiempo por ordenamiento", "p1_compilado_vs_interpretado.png")

    # ---- Punto 2: crecimiento (2 gráficas)
    for lang in ("java", "python"):
        grafica_crecimiento(bu, BUS, NOM_BUS, lang, "claves",
                            f"Búsqueda: crecimiento del tiempo en {NOM_LANG[lang]}",
                            "1.000 claves (500 presentes, 500 ausentes) · tiempo promedio por búsqueda",
                            "Tiempo promedio por búsqueda", f"p2_crecimiento_{lang}.png")

    # ---- Punto 2: compilado vs interpretado n = 1.000.000
    grupos_bus = [(a, NOM_BUS[a].replace(" (", "\n(")) for a in BUS]

    def v_bus(lang, alg, modo, n):
        r = bu.get((lang, alg, modo, n))
        return (r["promedio_ns"] / 1e9, r["tipo"]) if r else None

    grafica_barras(grupos_bus, lang_series, lambda a, l: v_bus(l, a, "claves", 1_000_000),
                   "Búsqueda: compilado frente a interpretado · n = 1.000.000",
                   "1.000 claves · tiempo promedio por búsqueda · eje logarítmico",
                   "Tiempo promedio por búsqueda", "p2_compilado_vs_interpretado.png")

    # ---- Punto 3.1: experimentos complementarios
    grupos_ex = [("radix8", "Radix Sort\n8 dígitos\nn = 1.000.000"), ("radix16", "Radix Sort\n16 dígitos\nn = 1.000.000"),
                 ("bucket_u10", "Bucket Sort\nuniforme\nn = 10.000"), ("bucket_c10", "Bucket Sort\nconcentrado\nn = 10.000"),
                 ("bucket_u100", "Bucket Sort\nuniforme\nn = 100.000"),
                 ("bucket_c100", "Bucket Sort\nconcentrado\nn = 100.000"),
                 ("bucket_r100", "Bucket Sort\nrango pequeño\nn = 100.000")]

    def v_ex(g, lang):
        if g == "radix8":
            return v_sort(lang, "radix", "aleatorio", 1_000_000)
        if g == "radix16":
            r = ex.get((lang, "radix16", "16digitos", 1_000_000))
        elif g == "bucket_r100":
            r = ex.get((lang, "bucket_rango_pequeno", "rango_pequeno", 100_000))
        elif g.startswith("bucket_u"):
            return v_sort(lang, "bucket", "aleatorio", 10_000 if g.endswith("10") else 100_000)
        else:
            r = ex.get((lang, "bucket_concentrado", "concentrado", 10_000 if g.endswith("10") else 100_000))
        return (r["promedio_ns"] / 1e9, r["tipo"]) if r else None

    grafica_barras(grupos_ex, lang_series, v_ex,
                   "Cuando no se cumple el supuesto de los algoritmos no comparativos",
                   "Promedio de 5 repeticiones · eje logarítmico", "Tiempo por ordenamiento",
                   "p3_supuestos_no_comparativos.png", ancho_fig=9.0)

    # ---- Punto 3.2: ¿ordenar o no ordenar?
    with open(os.path.join(RES, "punto3_k.json")) as f:
        kdat = json.load(f)
    fig, axs = plt.subplots(1, 2, figsize=(9.4, 4.0), sharey=False)
    for ax, lang in zip(axs, ("java", "python")):
        d = kdat[lang]
        ks = [10 ** (e / 20) for e in range(0, 101)]
        a = [k * d["t_lineal_s"] for k in ks]
        b = [d["t_orden_s"] + k * d["t_binaria_s"] for k in ks]
        ax.plot(ks, a, color=SERIES[0], lw=2, label="k búsquedas lineales")
        ax.plot(ks, b, color=SERIES[1], lw=2, label=f"Ordenar ({d['nombre_orden']}) + k binarias")
        ax.axvline(d["k_equilibrio"], color=MUTED, lw=1)
        ax.text(d["k_equilibrio"] * 1.15, d["t_orden_s"] * 0.22, f"k* ≈ {d['k_equilibrio']:.1f}".replace(".", ",") + f"\n→ k ≥ {d['k_min']}",
                color=TXT1, fontsize=8)
        ax.set_xscale("log")
        eje_tiempo(ax)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
        ax.set_xlabel("Número de búsquedas (k)")
        ax.set_ylabel("Tiempo total")
        ax.set_title(NOM_LANG[lang], fontsize=10)
        ax.legend(loc="upper left")
    fig.suptitle("¿Ordenar o no ordenar? Costo total para n = 1.000.000", x=0.08, ha="left",
                 fontsize=11, fontweight="semibold", color=TXT1)
    fig.tight_layout()
    guardar(fig, "p3_ordenar_o_no.png")


if __name__ == "__main__":
    main()
