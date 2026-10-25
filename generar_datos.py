"""
Generador de datos de prueba del taller (se ejecuta UNA sola vez).

Genera, con semilla fija, para cada tamaño n:
  datos/n_<n>/aleatorio.txt    enteros aleatorios de 8 dígitos (10.000.000 a 99.999.999)
  datos/n_<n>/ascendente.txt   los mismos datos ordenados de forma ascendente
  datos/n_<n>/descendente.txt  los mismos datos ordenados de forma descendente
  datos/n_<n>/claves.txt       1.000 claves de búsqueda (500 presentes y 500 ausentes, mezcladas)
  datos/n_<n>/claves_posicion.txt  claves ubicadas al inicio, centro y final del arreglo ascendente

Además genera los datos de los experimentos complementarios del Punto 3:
  datos/extra/16digitos_1000000.txt   1.000.000 enteros aleatorios de 16 dígitos (para Radix Sort)
  datos/extra/concentrado_<n>.txt     99 % de los valores en un rango pequeño + 1 % atípicos (para Bucket Sort)

Formato: un número entero por línea, texto plano.
Uso:  python3 generar_datos.py
"""
import os
import random

SEMILLA = 2026
TAMANOS = [1_000, 10_000, 100_000, 1_000_000]
MIN_8, MAX_8 = 10_000_000, 99_999_999
RAIZ = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(RAIZ, "datos")


def guardar(ruta, valores):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w") as f:
        f.write("\n".join(map(str, valores)))
        f.write("\n")


def main():
    rng = random.Random(SEMILLA)
    for n in TAMANOS:
        carpeta = os.path.join(DATOS, f"n_{n}")
        aleatorio = [rng.randint(MIN_8, MAX_8) for _ in range(n)]
        ascendente = sorted(aleatorio)
        descendente = ascendente[::-1]
        guardar(os.path.join(carpeta, "aleatorio.txt"), aleatorio)
        guardar(os.path.join(carpeta, "ascendente.txt"), ascendente)
        guardar(os.path.join(carpeta, "descendente.txt"), descendente)

        # 500 claves presentes: valores tomados de posiciones distintas del arreglo
        presentes = [aleatorio[i] for i in rng.sample(range(n), 500)]
        # 500 claves ausentes: números de 8 dígitos que no aparecen en el arreglo
        conjunto = set(aleatorio)
        ausentes = set()
        while len(ausentes) < 500:
            c = rng.randint(MIN_8, MAX_8)
            if c not in conjunto:
                ausentes.add(c)
        claves = presentes + sorted(ausentes)
        rng.shuffle(claves)
        guardar(os.path.join(carpeta, "claves.txt"), claves)
        guardar(os.path.join(carpeta, "claves_posicion.txt"),
                [ascendente[0], ascendente[n // 2], ascendente[n - 1]])
        print(f"n={n}: datos y claves generados")

    # --- Experimentos complementarios (Punto 3.1) ---
    extra = os.path.join(DATOS, "extra")
    guardar(os.path.join(extra, "16digitos_1000000.txt"),
            [rng.randint(10**15, 10**16 - 1) for _ in range(1_000_000)])
    for n in (10_000, 100_000):
        atipicos = n // 100
        concentrados = [rng.randint(MIN_8, MIN_8 + 999) for _ in range(n - atipicos)]
        dispersos = [rng.randint(MIN_8, MAX_8) for _ in range(atipicos)]
        valores = concentrados + dispersos
        rng.shuffle(valores)
        guardar(os.path.join(extra, f"concentrado_{n}.txt"), valores)
    # Todos los valores en un rango pequeño, SIN atípicos (para contrastar con el caso anterior)
    guardar(os.path.join(extra, "rango_pequeno_100000.txt"),
            [rng.randint(MIN_8, MIN_8 + 999) for _ in range(100_000)])
    print("datos de experimentos complementarios generados")


if __name__ == "__main__":
    main()
