package com.abyss.polyglot.javamodern;

/** The health banner. Rendered on every /health response. */
public final class Banner {

    private Banner() {
    }

    /**
     * The banner text. A text block keeps the multi-line string readable in the source
     * that produces it, with no escaped newlines and no concatenation, and it strips the
     * common indentation so the output is not shaped by where the literal happens to sit.
     * {@code var} on the locals lets the initialiser carry the type: it is inferred at
     * compile time, not dynamic, and it earns its place only where the right-hand side
     * already says what the thing is.
     */
    public static String text(String runtime, int itemCount) {
        var heading = "modern java: jdk http server, no framework";
        var body = """
                runtime : %s
                surface : com.sun.net.httpserver
                items   : %d
                """.formatted(runtime, itemCount);
        return heading + "\n" + body;
    }
}
