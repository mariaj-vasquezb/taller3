package taller;

import java.util.Arrays;

/**
 * Algoritmos de ordenamiento del Punto 1. La implementación es la misma que en
 * python/ordenamiento.py (misma estructura, mismas variables, mismos ciclos).
 *
 * Fuentes (GeeksforGeeks):
 *  Insertion Sort        https://www.geeksforgeeks.org/insertion-sort-algorithm/
 *  Dual-Pivot QuickSort  https://www.geeksforgeeks.org/dual-pivot-quicksort/
 *  Merge Sort            https://www.geeksforgeeks.org/merge-sort/
 *  Heap Sort             https://www.geeksforgeeks.org/heap-sort/
 *  Radix Sort            https://www.geeksforgeeks.org/radix-sort/
 *  Bucket Sort           https://www.geeksforgeeks.org/bucket-sort-2/  (adaptado a enteros, ver bucketSort)
 */
public final class Ordenamiento {

    private Ordenamiento() {}

    static void swap(int[] arr, int i, int j) {
        int t = arr[i];
        arr[i] = arr[j];
        arr[j] = t;
    }

    // ---------------------------------------------------------------- Insertion Sort
    public static void insertionSort(int[] arr) {
        int n = arr.length;
        for (int i = 1; i < n; ++i) {
            int key = arr[i];
            int j = i - 1;
            while (j >= 0 && arr[j] > key) {
                arr[j + 1] = arr[j];
                j = j - 1;
            }
            arr[j + 1] = key;
        }
    }

    // ---------------------------------------------------------------- Dual-Pivot QuickSort
    // Pivotes: primer elemento (p) y último elemento (q) del subarreglo, con p <= q.
    public static void dualPivotQuickSort(int[] arr) {
        dualPivotQuickSort(arr, 0, arr.length - 1);
    }

    static void dualPivotQuickSort(int[] arr, int low, int high) {
        if (low < high) {
            int[] piv = partition(arr, low, high);
            dualPivotQuickSort(arr, low, piv[0] - 1);
            dualPivotQuickSort(arr, piv[0] + 1, piv[1] - 1);
            dualPivotQuickSort(arr, piv[1] + 1, high);
        }
    }

    static int[] partition(int[] arr, int low, int high) {
        if (arr[low] > arr[high]) swap(arr, low, high);
        int j = low + 1;
        int g = high - 1, k = low + 1;
        int p = arr[low], q = arr[high];
        while (k <= g) {
            if (arr[k] < p) {               // elementos menores que el pivote izquierdo
                swap(arr, k, j);
                j++;
            } else if (arr[k] >= q) {       // elementos mayores o iguales al pivote derecho
                while (arr[g] > q && k < g) g--;
                swap(arr, k, g);
                g--;
                if (arr[k] < p) {
                    swap(arr, k, j);
                    j++;
                }
            }
            k++;
        }
        j--;
        g++;
        swap(arr, low, j);
        swap(arr, high, g);
        return new int[] {j, g};
    }

    // ---------------------------------------------------------------- Merge Sort
    public static void mergeSort(int[] arr) {
        mergeSort(arr, 0, arr.length - 1);
    }

    static void mergeSort(int[] arr, int l, int r) {
        if (l < r) {
            int m = l + (r - l) / 2;
            mergeSort(arr, l, m);
            mergeSort(arr, m + 1, r);
            merge(arr, l, m, r);
        }
    }

    static void merge(int[] arr, int l, int m, int r) {
        int n1 = m - l + 1;
        int n2 = r - m;
        int[] L = new int[n1];
        int[] R = new int[n2];
        for (int i = 0; i < n1; ++i) L[i] = arr[l + i];
        for (int j = 0; j < n2; ++j) R[j] = arr[m + 1 + j];
        int i = 0, j = 0, k = l;
        while (i < n1 && j < n2) {
            if (L[i] <= R[j]) {
                arr[k] = L[i];
                i++;
            } else {
                arr[k] = R[j];
                j++;
            }
            k++;
        }
        while (i < n1) {
            arr[k] = L[i];
            i++;
            k++;
        }
        while (j < n2) {
            arr[k] = R[j];
            j++;
            k++;
        }
    }

    // ---------------------------------------------------------------- Heap Sort
    public static void heapSort(int[] arr) {
        int n = arr.length;
        for (int i = n / 2 - 1; i >= 0; i--) heapify(arr, n, i);
        for (int i = n - 1; i > 0; i--) {
            swap(arr, 0, i);
            heapify(arr, i, 0);
        }
    }

    static void heapify(int[] arr, int n, int i) {
        int largest = i;
        int l = 2 * i + 1;
        int r = 2 * i + 2;
        if (l < n && arr[l] > arr[largest]) largest = l;
        if (r < n && arr[r] > arr[largest]) largest = r;
        if (largest != i) {
            swap(arr, i, largest);
            heapify(arr, n, largest);
        }
    }

    // ---------------------------------------------------------------- Radix Sort (LSD, base 10)
    static void countSort(int[] arr, int exp) {
        int n = arr.length;
        int[] output = new int[n];
        int[] count = new int[10];
        for (int i = 0; i < n; i++) count[(arr[i] / exp) % 10]++;
        for (int i = 1; i < 10; i++) count[i] += count[i - 1];
        for (int i = n - 1; i >= 0; i--) {
            output[count[(arr[i] / exp) % 10] - 1] = arr[i];
            count[(arr[i] / exp) % 10]--;
        }
        for (int i = 0; i < n; i++) arr[i] = output[i];
    }

    public static void radixSort(int[] arr) {
        int m = arr[0];
        for (int x : arr) if (x > m) m = x;
        for (int exp = 1; m / exp > 0; exp *= 10) countSort(arr, exp);
    }

    // Versión para enteros de 16 dígitos (experimento complementario del Punto 3.1).
    // Es el mismo algoritmo; solo cambia el tipo de dato (long) porque int no alcanza.
    static void countSortLong(long[] arr, long exp) {
        int n = arr.length;
        long[] output = new long[n];
        int[] count = new int[10];
        for (int i = 0; i < n; i++) count[(int) ((arr[i] / exp) % 10)]++;
        for (int i = 1; i < 10; i++) count[i] += count[i - 1];
        for (int i = n - 1; i >= 0; i--) {
            output[count[(int) ((arr[i] / exp) % 10)] - 1] = arr[i];
            count[(int) ((arr[i] / exp) % 10)]--;
        }
        for (int i = 0; i < n; i++) arr[i] = output[i];
    }

    public static void radixSortLong(long[] arr) {
        long m = arr[0];
        for (long x : arr) if (x > m) m = x;
        for (long exp = 1; m / exp > 0; exp *= 10) countSortLong(arr, exp);
    }

    // ---------------------------------------------------------------- Bucket Sort
    // GeeksforGeeks presenta Bucket Sort para reales en [0, 1): cubeta = floor(n * x).
    // Adaptación a enteros: se usan k = n cubetas y cada valor x va a la cubeta
    //     floor((x - min) * k / (max - min + 1)),
    // es decir, el rango [min, max] se divide en k intervalos de igual ancho.
    // Cada cubeta se ordena con Insertion Sort y luego se concatenan en orden.
    // Las cubetas son listas dinámicas de enteros (equivalentes a las listas de Python).
    public static void bucketSort(int[] arr) {
        int n = arr.length;
        if (n <= 0) return;
        int min = arr[0], max = arr[0];
        for (int x : arr) {
            if (x < min) min = x;
            if (x > max) max = x;
        }
        int k = n;
        long rango = (long) max - min + 1;
        int[][] buckets = new int[k][];
        int[] sizes = new int[k];
        for (int x : arr) {
            int idx = (int) (((long) (x - min) * k) / rango);
            int[] b = buckets[idx];
            if (b == null) {
                b = new int[4];
                buckets[idx] = b;
            } else if (sizes[idx] == b.length) {
                b = Arrays.copyOf(b, b.length * 2);
                buckets[idx] = b;
            }
            b[sizes[idx]++] = x;
        }
        int index = 0;
        for (int c = 0; c < k; c++) {
            int[] b = buckets[c];
            int s = sizes[c];
            if (s == 0) continue;
            insertionSortRange(b, s);
            for (int t = 0; t < s; t++) arr[index++] = b[t];
        }
    }

    // Insertion Sort sobre los primeros 'len' elementos (los ocupados) de una cubeta.
    static void insertionSortRange(int[] arr, int len) {
        for (int i = 1; i < len; ++i) {
            int key = arr[i];
            int j = i - 1;
            while (j >= 0 && arr[j] > key) {
                arr[j + 1] = arr[j];
                j = j - 1;
            }
            arr[j + 1] = key;
        }
    }

    public static void ordenar(String algoritmo, int[] arr) {
        switch (algoritmo) {
            case "insertion" -> insertionSort(arr);
            case "quicksort_dual" -> dualPivotQuickSort(arr);
            case "merge" -> mergeSort(arr);
            case "heap" -> heapSort(arr);
            case "radix" -> radixSort(arr);
            case "bucket" -> bucketSort(arr);
            default -> throw new IllegalArgumentException("Algoritmo desconocido: " + algoritmo);
        }
    }
}
