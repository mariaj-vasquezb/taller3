package taller;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Ejecuta UNA configuración de medición y escribe el resultado como una línea JSON en stdout.
 * El orquestador (orquestador/ejecutar_mediciones.py) la invoca una vez por configuración.
 *
 * Uso:
 *   sort   <datos> <algoritmo> <variante> <n> <repeticiones> <limite_s> <calentamiento: completo|prefijo>
 *   search <datos> <algoritmo> <modo> <n> <repeticiones> <limite_s>
 *          modo: claves | inicio | centro | final | claves_desordenado
 *   extra  <datos> <experimento> <n> <repeticiones> <limite_s>
 *          experimento: radix16 | bucket_concentrado
 *
 * Tiempos en nanosegundos (System.nanoTime). La lectura de archivos, la copia del arreglo
 * y la verificación quedan por fuera del tiempo medido.
 */
public final class Benchmark {

    interface Buscador {
        int buscar(int[] arr, int x);
    }

    static final long CALENTAMIENTO_MIN_NS = 500_000_000L; // al menos 0,5 s de calentamiento
    static final int CALENTAMIENTO_MAX_RUNS = 2000;
    static volatile long sumidero; // evita que el JIT elimine el trabajo como código muerto

    public static void main(String[] args) throws Exception {
        String modo = args[0];
        Path datos = Path.of(args[1]);
        try {
            switch (modo) {
                case "sort" -> sort(datos, args[2], args[3], Integer.parseInt(args[4]),
                        Integer.parseInt(args[5]), Double.parseDouble(args[6]), args[7]);
                case "search" -> search(datos, args[2], args[3], Integer.parseInt(args[4]),
                        Integer.parseInt(args[5]), Double.parseDouble(args[6]));
                case "extra" -> extra(datos, args[2], Integer.parseInt(args[3]),
                        Integer.parseInt(args[4]), Double.parseDouble(args[5]));
                default -> throw new IllegalArgumentException(modo);
            }
        } catch (OutOfMemoryError e) {
            System.out.println(json("error", "OutOfMemoryError", "fase=desconocida", List.of(), 0));
        }
    }

    // ------------------------------------------------------------------ lectura de datos
    static int[] leer(Path ruta) throws IOException {
        int[] a = new int[1024];
        int n = 0;
        try (BufferedReader br = Files.newBufferedReader(ruta)) {
            String linea;
            while ((linea = br.readLine()) != null) {
                if (linea.isEmpty()) continue;
                if (n == a.length) a = Arrays.copyOf(a, a.length * 2);
                a[n++] = Integer.parseInt(linea.trim());
            }
        }
        return Arrays.copyOf(a, n);
    }

    static long[] leerLong(Path ruta) throws IOException {
        long[] a = new long[1024];
        int n = 0;
        try (BufferedReader br = Files.newBufferedReader(ruta)) {
            String linea;
            while ((linea = br.readLine()) != null) {
                if (linea.isEmpty()) continue;
                if (n == a.length) a = Arrays.copyOf(a, a.length * 2);
                a[n++] = Long.parseLong(linea.trim());
            }
        }
        return Arrays.copyOf(a, n);
    }

    // ------------------------------------------------------------------ ordenamiento
    static void sort(Path datos, String alg, String variante, int n, int reps, double limiteS,
                     String calentamiento) throws IOException {
        Path carpeta = datos.resolve("n_" + n);
        int[] original = leer(carpeta.resolve(variante + ".txt"));
        int[] esperado = leer(carpeta.resolve("ascendente.txt"));
        long limiteNs = (long) (limiteS * 1e9);
        List<Long> tiempos = new ArrayList<>();
        String fase = "calentamiento";
        int runsCal = 0;
        try {
            // Calentamiento (JIT), fuera de las mediciones:
            //  (a) ejecuciones repetidas sobre copias del prefijo de 10.000 elementos, hasta
            //      acumular >= 0,5 s y >= 20 ejecuciones, para que el método llegue a la
            //      compilación optimizada (C2) y no solo a la compilación OSR de un ciclo largo;
            //  (b) una ejecución completa de calentamiento con el tamaño real, salvo que se
            //      prediga larga (modo "prefijo"), en cuyo caso se usa el prefijo de 100.000.
            int[] prefijo = Arrays.copyOf(original, Math.min(n, 10_000));
            long inicioCal = System.nanoTime();
            do {
                int[] c = prefijo.clone();
                Ordenamiento.ordenar(alg, c);
                runsCal++;
            } while ((System.nanoTime() - inicioCal < CALENTAMIENTO_MIN_NS || runsCal < 20)
                    && runsCal < CALENTAMIENTO_MAX_RUNS);
            int[] completo = calentamiento.equals("prefijo")
                    ? Arrays.copyOf(original, Math.min(n, 100_000)) : original.clone();
            Ordenamiento.ordenar(alg, completo);
            runsCal++;

            fase = "medicion";
            for (int r = 0; r < reps; r++) {
                int[] copia = original.clone();           // copia nueva, fuera del tiempo
                long t0 = System.nanoTime();
                Ordenamiento.ordenar(alg, copia);
                long t1 = System.nanoTime();
                if (!Arrays.equals(copia, esperado)) {    // verificación, fuera del tiempo
                    System.out.println(json("error", "VerificacionFallida",
                            "el arreglo no quedó ordenado en la repetición " + (r + 1), tiempos, runsCal));
                    return;
                }
                tiempos.add(t1 - t0);
                if (t1 - t0 > limiteNs) {
                    System.out.println(json("limite", "", "la repetición " + (r + 1)
                            + " superó el límite de tiempo", tiempos, runsCal));
                    return;
                }
            }
            System.out.println(json("ok", "", "", tiempos, runsCal));
        } catch (StackOverflowError e) {
            System.out.println(json("error", "StackOverflowError",
                    "desbordamiento de pila durante la fase de " + fase, tiempos, runsCal));
        }
    }

    // ------------------------------------------------------------------ búsqueda
    static Buscador buscador(String alg) {
        return switch (alg) {
            case "lineal" -> Busqueda::linearSearch;
            case "binaria" -> Busqueda::binarySearch;
            case "ternaria" -> Busqueda::ternarySearch;
            case "saltos" -> Busqueda::jumpSearch;
            case "interpolacion" -> Busqueda::interpolationSearch;
            case "exponencial" -> Busqueda::exponentialSearch;
            default -> throw new IllegalArgumentException(alg);
        };
    }

    static void search(Path datos, String alg, String modo, int n, int reps, double limiteS)
            throws IOException {
        Path carpeta = datos.resolve("n_" + n);
        int[] ordenado = leer(carpeta.resolve("ascendente.txt"));
        int[] arr = modo.equals("claves_desordenado") ? leer(carpeta.resolve("aleatorio.txt")) : ordenado;
        int[] claves;
        if (modo.equals("claves") || modo.equals("claves_desordenado")) {
            claves = leer(carpeta.resolve("claves.txt"));
        } else {
            int[] pos = leer(carpeta.resolve("claves_posicion.txt"));
            int c = switch (modo) {
                case "inicio" -> pos[0];
                case "centro" -> pos[1];
                case "final" -> pos[2];
                default -> throw new IllegalArgumentException(modo);
            };
            claves = new int[1000];
            Arrays.fill(claves, c);
        }
        Buscador b = buscador(alg);

        // Verificación (fuera del tiempo): cada resultado debe ser correcto.
        for (int x : claves) {
            int r = b.buscar(arr, x);
            boolean presente = Arrays.binarySearch(ordenado, x) >= 0;
            if ((r == -1 && presente) || (r != -1 && arr[r] != x)) {
                System.out.println(json("error", "VerificacionFallida",
                        "resultado incorrecto para la clave " + x, List.of(), 0));
                return;
            }
        }

        // Calentamiento JIT
        int runsCal = 0;
        long acum = 0;
        // La pasada completa sobre las 1.000 claves está en su propio método (unaPasada) para que
        // el calentamiento compile exactamente el mismo código que luego se mide.
        long inicioCal = System.nanoTime();
        do {
            acum += unaPasada(b, arr, claves);
            runsCal++;
        } while ((System.nanoTime() - inicioCal < CALENTAMIENTO_MIN_NS || runsCal < 20)
                && runsCal < CALENTAMIENTO_MAX_RUNS);

        long limiteNs = (long) (limiteS * 1e9);
        List<Long> tiempos = new ArrayList<>();
        for (int r = 0; r < reps; r++) {
            long t0 = System.nanoTime();
            acum += unaPasada(b, arr, claves);
            long t1 = System.nanoTime();
            tiempos.add(t1 - t0); // tiempo TOTAL de las 1.000 búsquedas
            if (t1 - t0 > limiteNs) {
                sumidero = acum;
                System.out.println(json("limite", "", "", tiempos, runsCal));
                return;
            }
        }
        sumidero = acum;
        System.out.println(json("ok", "", "", tiempos, runsCal));
    }

    static long unaPasada(Buscador b, int[] arr, int[] claves) {
        long s = 0;
        for (int x : claves) s += b.buscar(arr, x);
        return s;
    }

    // ------------------------------------------------------------------ experimentos complementarios
    static void extra(Path datos, String exp, int n, int reps, double limiteS) throws IOException {
        long limiteNs = (long) (limiteS * 1e9);
        List<Long> tiempos = new ArrayList<>();
        int runsCal = 0;
        if (exp.equals("radix16")) {
            long[] original = leerLong(datos.resolve("extra").resolve("16digitos_" + n + ".txt"));
            long[] esperado = original.clone();
            Arrays.sort(esperado);
            long inicioCal = System.nanoTime();
            do {
                long[] c = original.clone();
                Ordenamiento.radixSortLong(c);
                runsCal++;
            } while (System.nanoTime() - inicioCal < CALENTAMIENTO_MIN_NS && runsCal < CALENTAMIENTO_MAX_RUNS);
            for (int r = 0; r < reps; r++) {
                long[] c = original.clone();
                long t0 = System.nanoTime();
                Ordenamiento.radixSortLong(c);
                long t1 = System.nanoTime();
                if (!Arrays.equals(c, esperado)) {
                    System.out.println(json("error", "VerificacionFallida", "", tiempos, runsCal));
                    return;
                }
                tiempos.add(t1 - t0);
                if (t1 - t0 > limiteNs) {
                    System.out.println(json("limite", "", "", tiempos, runsCal));
                    return;
                }
            }
        } else if (exp.equals("bucket_concentrado") || exp.equals("bucket_rango_pequeno")) {
            String archivo = exp.equals("bucket_concentrado") ? "concentrado_" : "rango_pequeno_";
            int[] original = leer(datos.resolve("extra").resolve(archivo + n + ".txt"));
            int[] esperado = original.clone();
            Arrays.sort(esperado);
            long inicioCal = System.nanoTime();
            do {
                int[] c = original.clone();
                Ordenamiento.bucketSort(c);
                runsCal++;
            } while (System.nanoTime() - inicioCal < CALENTAMIENTO_MIN_NS && runsCal < CALENTAMIENTO_MAX_RUNS);
            for (int r = 0; r < reps; r++) {
                int[] c = original.clone();
                long t0 = System.nanoTime();
                Ordenamiento.bucketSort(c);
                long t1 = System.nanoTime();
                if (!Arrays.equals(c, esperado)) {
                    System.out.println(json("error", "VerificacionFallida", "", tiempos, runsCal));
                    return;
                }
                tiempos.add(t1 - t0);
                if (t1 - t0 > limiteNs) {
                    System.out.println(json("limite", "", "", tiempos, runsCal));
                    return;
                }
            }
        } else {
            throw new IllegalArgumentException(exp);
        }
        System.out.println(json("ok", "", "", tiempos, runsCal));
    }

    // ------------------------------------------------------------------ salida JSON
    static String json(String estado, String error, String detalle, List<Long> tiempos, int runsCal) {
        StringBuilder sb = new StringBuilder();
        sb.append("{\"estado\":\"").append(estado).append("\",\"error\":\"").append(error)
          .append("\",\"detalle\":\"").append(detalle.replace("\"", "'")).append("\",\"calentamiento_runs\":")
          .append(runsCal).append(",\"tiempos_ns\":[");
        for (int i = 0; i < tiempos.size(); i++) {
            if (i > 0) sb.append(',');
            sb.append(tiempos.get(i));
        }
        sb.append("]}");
        return sb.toString();
    }
}
