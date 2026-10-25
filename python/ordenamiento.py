"""
Algoritmos de ordenamiento del Punto 1. Misma implementación que java/src/taller/Ordenamiento.java.
Todos ordenan la lista en el lugar (la modifican).

Fuentes (GeeksforGeeks):
  Insertion Sort        https://www.geeksforgeeks.org/insertion-sort-algorithm/
  Dual-Pivot QuickSort  https://www.geeksforgeeks.org/dual-pivot-quicksort/
  Merge Sort            https://www.geeksforgeeks.org/merge-sort/
  Heap Sort             https://www.geeksforgeeks.org/heap-sort/
  Radix Sort            https://www.geeksforgeeks.org/radix-sort/
  Bucket Sort           https://www.geeksforgeeks.org/bucket-sort-2/  (adaptado a enteros)
"""


def swap(arr, i, j):
    arr[i], arr[j] = arr[j], arr[i]


# ------------------------------------------------------------------ Insertion Sort
def insertion_sort(arr):
    n = len(arr)
    for i in range(1, n):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j = j - 1
        arr[j + 1] = key


# ------------------------------------------------------------------ Dual-Pivot QuickSort
# Pivotes: primer elemento (p) y último elemento (q) del subarreglo, con p <= q.
def dual_pivot_quick_sort(arr):
    _dual_pivot_quick_sort(arr, 0, len(arr) - 1)


def _dual_pivot_quick_sort(arr, low, high):
    if low < high:
        lp, rp = partition(arr, low, high)
        _dual_pivot_quick_sort(arr, low, lp - 1)
        _dual_pivot_quick_sort(arr, lp + 1, rp - 1)
        _dual_pivot_quick_sort(arr, rp + 1, high)


def partition(arr, low, high):
    if arr[low] > arr[high]:
        swap(arr, low, high)
    j = low + 1
    g = high - 1
    k = low + 1
    p = arr[low]
    q = arr[high]
    while k <= g:
        if arr[k] < p:                 # menores que el pivote izquierdo
            swap(arr, k, j)
            j += 1
        elif arr[k] >= q:              # mayores o iguales al pivote derecho
            while arr[g] > q and k < g:
                g -= 1
            swap(arr, k, g)
            g -= 1
            if arr[k] < p:
                swap(arr, k, j)
                j += 1
        k += 1
    j -= 1
    g += 1
    swap(arr, low, j)
    swap(arr, high, g)
    return j, g


# ------------------------------------------------------------------ Merge Sort
def merge_sort(arr):
    _merge_sort(arr, 0, len(arr) - 1)


def _merge_sort(arr, l, r):
    if l < r:
        m = l + (r - l) // 2
        _merge_sort(arr, l, m)
        _merge_sort(arr, m + 1, r)
        merge(arr, l, m, r)


def merge(arr, l, m, r):
    n1 = m - l + 1
    n2 = r - m
    L = [0] * n1
    R = [0] * n2
    for i in range(n1):
        L[i] = arr[l + i]
    for j in range(n2):
        R[j] = arr[m + 1 + j]
    i = 0
    j = 0
    k = l
    while i < n1 and j < n2:
        if L[i] <= R[j]:
            arr[k] = L[i]
            i += 1
        else:
            arr[k] = R[j]
            j += 1
        k += 1
    while i < n1:
        arr[k] = L[i]
        i += 1
        k += 1
    while j < n2:
        arr[k] = R[j]
        j += 1
        k += 1


# ------------------------------------------------------------------ Heap Sort
def heap_sort(arr):
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    for i in range(n - 1, 0, -1):
        swap(arr, 0, i)
        heapify(arr, i, 0)


def heapify(arr, n, i):
    largest = i
    l = 2 * i + 1
    r = 2 * i + 2
    if l < n and arr[l] > arr[largest]:
        largest = l
    if r < n and arr[r] > arr[largest]:
        largest = r
    if largest != i:
        swap(arr, i, largest)
        heapify(arr, n, largest)


# ------------------------------------------------------------------ Radix Sort (LSD, base 10)
def count_sort(arr, exp):
    n = len(arr)
    output = [0] * n
    count = [0] * 10
    for i in range(n):
        count[(arr[i] // exp) % 10] += 1
    for i in range(1, 10):
        count[i] += count[i - 1]
    for i in range(n - 1, -1, -1):
        output[count[(arr[i] // exp) % 10] - 1] = arr[i]
        count[(arr[i] // exp) % 10] -= 1
    for i in range(n):
        arr[i] = output[i]


def radix_sort(arr):
    m = arr[0]
    for x in arr:
        if x > m:
            m = x
    exp = 1
    while m // exp > 0:
        count_sort(arr, exp)
        exp *= 10


# ------------------------------------------------------------------ Bucket Sort
# Adaptación a enteros de la versión de GeeksforGeeks (reales en [0, 1)):
# k = n cubetas; el valor x va a la cubeta floor((x - min) * k / (max - min + 1)).
# Cada cubeta se ordena con Insertion Sort y luego se concatenan en orden.
def bucket_sort(arr):
    n = len(arr)
    if n <= 0:
        return
    mn = arr[0]
    mx = arr[0]
    for x in arr:
        if x < mn:
            mn = x
        if x > mx:
            mx = x
    k = n
    rango = mx - mn + 1
    buckets = [[] for _ in range(k)]
    for x in arr:
        buckets[((x - mn) * k) // rango].append(x)
    index = 0
    for b in buckets:
        if not b:
            continue
        insertion_sort(b)
        for x in b:
            arr[index] = x
            index += 1


ALGORITMOS = {
    "insertion": insertion_sort,
    "quicksort_dual": dual_pivot_quick_sort,
    "merge": merge_sort,
    "heap": heap_sort,
    "radix": radix_sort,
    "bucket": bucket_sort,
}
