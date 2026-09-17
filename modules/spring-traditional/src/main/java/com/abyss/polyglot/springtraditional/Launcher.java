package com.abyss.polyglot.springtraditional;

import java.io.File;
import org.apache.catalina.startup.Tomcat;
import org.springframework.context.ApplicationContext;

/**
 * Runs the war as a process.
 *
 * Tomcat is embedded here so this module runs like every other stack, but it is wired by
 * hand: instantiated, configured, started. That is the opposite of Boot's embedded
 * server, which appears because a starter is on the classpath.
 */
public final class Launcher {

    private Launcher() {
    }

    public static void main(String[] args) throws Exception {
        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));

        Tomcat tomcat = new Tomcat();
        tomcat.setPort(port);
        tomcat.getConnector();

        File base = new File(System.getProperty("java.io.tmpdir"));
        tomcat.addWebapp("", base.getAbsolutePath());

        startLifecycle(tomcat);
        tomcat.getServer().await();
    }

    /**
     * The servlet lifecycle, started explicitly. A war is not a program with a main: the
     * container starts, scans for initializers, calls onStartup, builds contexts, then
     * begins serving, and it must be told to await rather than exiting. Boot inverts
     * this: the application owns a main and starts a server inside itself.
     */
    static void startLifecycle(Tomcat tomcat) throws Exception {
        tomcat.start();
    }

    /**
     * The container itself: a registry that constructs beans, resolves what each one
     * needs, orders their creation by dependency, and hands them out by type or name. It
     * is an object graph builder, and inversion of control means this method decides
     * nothing about how JdbcTemplate is made. It asks, and the container has already
     * worked out that a DataSource had to exist first.
     */
    public static <T> T lookup(ApplicationContext context, Class<T> type) {
        return context.getBean(type);
    }
}
