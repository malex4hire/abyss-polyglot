package com.abyss.polyglot.javamodern;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Seed data, loaded from the classpath at startup. Identical across every backend. */
public final class Seed {

    private Seed() {
    }

    /**
     * Read the seed file. Every resource opened in the try header is closed on the way
     * out, in reverse order, whether the block returns or throws — and if closing itself
     * throws while an exception is already in flight, the close failure is attached as
     * suppressed rather than replacing the original. That is the part a hand-written
     * finally block almost always gets wrong.
     */
    public static List<WorkItem> load(Instant now) {
        List<WorkItem> loaded = new ArrayList<>();
        try (InputStream raw = Seed.class.getResourceAsStream("/seed.csv");
             BufferedReader reader = new BufferedReader(
                     new InputStreamReader(requireStream(raw), StandardCharsets.UTF_8))) {
            String line;
            boolean header = true;
            while ((line = reader.readLine()) != null) {
                if (header) {
                    header = false;
                    continue;
                }
                if (line.isBlank()) {
                    continue;
                }
                loaded.add(parse(line, now));
            }
        } catch (IOException e) {
            throw new IllegalStateException("seed data could not be read", e);
        }
        return List.copyOf(loaded);
    }

    private static InputStream requireStream(InputStream raw) throws IOException {
        if (raw == null) {
            throw new IOException("seed.csv is not on the classpath");
        }
        return raw;
    }

    private static WorkItem parse(String line, Instant now) {
        String[] cells = line.split(",", -1);
        List<String> tags = cells[5].isBlank()
                ? List.of()
                : Arrays.stream(cells[5].split(";")).map(String::trim).toList();
        return new WorkItem(
                cells[0], cells[1], Status.valueOf(cells[2]),
                Integer.parseInt(cells[3]), cells[4],
                now, now, tags, null);
    }
}
