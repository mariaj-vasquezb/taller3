package taller;

/**
 * Algoritmos de búsqueda del Punto 2 (sobre arreglo ordenado ascendente, salvo la lineal).
 * Devuelven el índice de la clave o -1 si no está. Misma implementación que python/busqueda.py.
 *
 * Fuentes (GeeksforGeeks):
 *  Lineal         https://www.geeksforgeeks.org/linear-search/
 *  Binaria        https://www.geeksforgeeks.org/binary-search/        (versión iterativa)
 *  Ternaria       https://www.geeksforgeeks.org/ternary-search/       (versión iterativa)
 *  Saltos         https://www.geeksforgeeks.org/jump-search/
 *  Interpolación  https://www.geeksforgeeks.org/interpolation-search/
 *  Exponencial    https://www.geeksforgeeks.org/exponential-search/
 */
public final class Busqueda {

    private Busqueda() {}

    public static int linearSearch(int[] arr, int x) {
        int n = arr.length;
        for (int i = 0; i < n; i++) {
            if (arr[i] == x) return i;
        }
        return -1;
    }

    public static int binarySearch(int[] arr, int x) {
        return binarySearch(arr, 0, arr.length - 1, x);
    }

    static int binarySearch(int[] arr, int low, int high, int x) {
        while (low <= high) {
            int mid = low + (high - low) / 2;
            if (arr[mid] == x) return mid;
            if (arr[mid] < x) low = mid + 1;
            else high = mid - 1;
        }
        return -1;
    }

    public static int ternarySearch(int[] arr, int x) {
        int l = 0, r = arr.length - 1;
        while (r >= l) {
            int mid1 = l + (r - l) / 3;
            int mid2 = r - (r - l) / 3;
            if (arr[mid1] == x) return mid1;
            if (arr[mid2] == x) return mid2;
            if (x < arr[mid1]) r = mid1 - 1;
            else if (x > arr[mid2]) l = mid2 + 1;
            else {
                l = mid1 + 1;
                r = mid2 - 1;
            }
        }
        return -1;
    }

    public static int jumpSearch(int[] arr, int x) {
        int n = arr.length;
        int salto = (int) Math.floor(Math.sqrt(n));
        int step = salto;
        int prev = 0;
        while (arr[Math.min(step, n) - 1] < x) {
            prev = step;
            step += salto;
            if (prev >= n) return -1;
        }
        while (arr[prev] < x) {
            prev++;
            if (prev == Math.min(step, n)) return -1;
        }
        if (arr[prev] == x) return prev;
        return -1;
    }

    // Nota: la versión de GeeksforGeeks calcula (hi - lo) / (arr[hi] - arr[lo]) con división
    // entera antes de multiplicar, lo que da 0 cuando hay menos elementos que el rango de valores
    // y convierte la búsqueda en lineal. Aquí se multiplica primero (en long) y luego se divide.
    // También se evita la división por cero cuando arr[lo] == arr[hi].
    public static int interpolationSearch(int[] arr, int x) {
        int lo = 0, hi = arr.length - 1;
        while (lo <= hi && x >= arr[lo] && x <= arr[hi]) {
            if (lo == hi) {
                if (arr[lo] == x) return lo;
                return -1;
            }
            if (arr[hi] == arr[lo]) return arr[lo] == x ? lo : -1;
            int pos = lo + (int) (((long) (hi - lo) * (x - arr[lo])) / (arr[hi] - arr[lo]));
            if (arr[pos] == x) return pos;
            if (arr[pos] < x) lo = pos + 1;
            else hi = pos - 1;
        }
        return -1;
    }

    public static int exponentialSearch(int[] arr, int x) {
        int n = arr.length;
        if (arr[0] == x) return 0;
        int i = 1;
        while (i < n && arr[i] <= x) i = i * 2;
        return binarySearch(arr, i / 2, Math.min(i, n - 1), x);
    }

    public static int buscar(String algoritmo, int[] arr, int x) {
        return switch (algoritmo) {
            case "lineal" -> linearSearch(arr, x);
            case "binaria" -> binarySearch(arr, x);
            case "ternaria" -> ternarySearch(arr, x);
            case "saltos" -> jumpSearch(arr, x);
            case "interpolacion" -> interpolationSearch(arr, x);
            case "exponencial" -> exponentialSearch(arr, x);
            default -> throw new IllegalArgumentException("Algoritmo desconocido: " + algoritmo);
        };
    }
}
