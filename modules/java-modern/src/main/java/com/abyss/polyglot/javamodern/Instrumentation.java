package com.abyss.polyglot.javamodern;

import com.sun.net.httpserver.HttpServer;
import java.io.File;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Instrumentation, not contract. This endpoint reports resolved runtime data: the JVM's
 * own version, the artifacts actually on the runtime classpath, and the concrete class of
 * the running HTTP server.
 *
 * It deliberately reports no framework name and no stack name. A module asserting its own
 * identity proves nothing; the runtime-identity check derives identity from what actually
 * resolved, and a claimed label would let a module lie about what it is.
 */
public final class Instrumentation {

    private Instrumentation() {
    }

    public static Map<String, Object> report(HttpServer server) {
        Map<String, Object> doc = new LinkedHashMap<>();
        doc.put("runtime_version", System.getProperty("java.version"));
        // The exact build, not the marketing version. "25.0.3" is what the floor is
        // compared against and stays the parseable field; this is the string that
        // identifies precisely which JDK produced the answers on this page.
        doc.put("runtime_version_exact", System.getProperty("java.runtime.version"));
        doc.put("runtime_vendor_version", System.getProperty("java.vendor.version"));
        doc.put("runtime_vendor", System.getProperty("java.vendor"));
        doc.put("http_server_class", server.getClass().getName());
        // The JDK module is the honest answer. The concrete class is an implementation
        // detail of it (sun.net.httpserver.HttpServerImpl), so the module is the precise
        // one.
        doc.put("http_server_module",
                server.getClass().getModule() == null ? "unnamed" : server.getClass().getModule().getName());
        doc.put("artifacts", artifacts());
        return doc;
    }

    /** Every jar on the runtime classpath, by file name. Read from the JVM, not the pom. */
    private static List<String> artifacts() {
        List<String> found = new ArrayList<>();
        String raw = System.getProperty("java.class.path", "");
        for (String element : raw.split(File.pathSeparator)) {
            if (element.isBlank()) {
                continue;
            }
            String name = new File(element).getName();
            // The classpath carries target/classes itself, not only jars. That entry
            // is this module's own compiled output, listed alongside its actual
            // dependencies. It is neither a jar nor a version, and reporting it as one
            // is the defect: an artifact list an operator reads for exact versions
            // should never contain an entry with no version at all.
            if (name.endsWith(".jar")) {
                found.add(name);
            }
        }
        found.sort(String::compareTo);
        return List.copyOf(found);
    }
}
