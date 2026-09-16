package com.abyss.polyglot.springboot;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;
import org.springframework.context.ConfigurableApplicationContext;

/** The entry point. One annotation replaces the traditional module's whole bootstrap. */
@SpringBootApplication
@ConfigurationPropertiesScan
public class Application {

    public static void main(String[] args) {
        start(args);
    }

    /**
     * The whole bootstrap, in one call against one annotated class.
     *
     * @SpringBootApplication is three annotations at once — @SpringBootConfiguration,
     * @EnableAutoConfiguration and @ComponentScan — and SpringApplication.run turns them
     * into a running context: it reads the configuration, evaluates every
     * auto-configuration condition, scans downward from this class's package, starts an
     * embedded server and returns the context.
     *
     * The traditional module writes that sequence out by hand across a
     * WebApplicationInitializer: build the context, name the configuration classes, scan
     * a named package, create and map the dispatcher, then start the container. Here the
     * sequence is the framework's and the position of this class is what defines the scan
     * boundary.
     */
    static ConfigurableApplicationContext start(String[] args) {
        return SpringApplication.run(Application.class, args);
    }
}
