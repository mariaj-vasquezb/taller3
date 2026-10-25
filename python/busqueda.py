"""
Algoritmos de búsqueda del Punto 2. Misma implementación que java/src/taller/Busqueda.java.
Devuelven el índice de la clave o -1 si no está.

Fuentes (GeeksforGeeks):
  Lineal         https://www.geeksforgeeks.org/linear-search/
  Binaria        https://www.geeksforgeeks.org/binary-search/        (versión iterativa)
  Ternaria       https://www.geeksforgeeks.org/ternary-search/       (versión iterativa)
  Saltos         https://www.geeksforgeeks.org/jump-search/
  Interpolación  https://www.geeksforgeeks.org/interpolation-search/
  Exponencial    https://www.geeksforgeeks.org/exponential-search/
"""
import math


def linear_search(arr, x):
    n = len(arr)
    for i in range(n):
        if arr[i] == x:
            return i
    return -1


def binary_search(arr, x):
    return _binary_search(arr, 0, len(arr) - 1, x)


def _binary_search(arr, low, high, x):
    while low <= high:
        mid = low + (high - low) // 2
        if arr[mid] == x:
            return mid
        if arr[mid] < x:
            low = mid + 1
        else:
            high = mid - 1
    return -1


def ternary_search(arr, x):
    l = 0
    r = len(arr) - 1
    while r >= l:
        mid1 = l + (r - l) // 3
        mid2 = r - (r - l) // 3
        if arr[mid1] == x:
            return mid1
        if arr[mid2] == x:
            return mid2
        if x < arr[mid1]:
            r = mid1 - 1
        elif x > arr[mid2]:
            l = mid2 + 1
        else:
            l = mid1 + 1
            r = mid2 - 1
    return -1


def jump_search(arr, x):
    n = len(arr)
    salto = int(math.floor(math.sqrt(n)))
    step = salto
    prev = 0
    while arr[min(step, n) - 1] < x:
        prev = step
        step += salto
        if prev >= n:
            return -1
    while arr[prev] < x:
        prev += 1
        if prev == min(step, n):
            return -1
    if arr[prev] == x:
        return prev
    return -1


# Nota: se multiplica antes de dividir (la versión de GeeksforGeeks divide primero con
# división entera, lo que da 0 y degenera en búsqueda lineal). Se evita dividir por cero.
def interpolation_search(arr, x):
    lo = 0
    hi = len(arr) - 1
    while lo <= hi and arr[lo] <= x <= arr[hi]:
        if lo == hi:
            if arr[lo] == x:
                return lo
            return -1
        if arr[hi] == arr[lo]:
            return lo if arr[lo] == x else -1
        pos = lo + ((hi - lo) * (x - arr[lo])) // (arr[hi] - arr[lo])
        if arr[pos] == x:
            return pos
        if arr[pos] < x:
            lo = pos + 1
        else:
            hi = pos - 1
    return -1


def exponential_search(arr, x):
    n = len(arr)
    if arr[0] == x:
        return 0
    i = 1
    while i < n and arr[i] <= x:
        i = i * 2
    return _binary_search(arr, i // 2, min(i, n - 1), x)


ALGORITMOS = {
    "lineal": linear_search,
    "binaria": binary_search,
    "ternaria": ternary_search,
    "saltos": jump_search,
    "interpolacion": interpolation_search,
    "exponencial": exponential_search,
}
