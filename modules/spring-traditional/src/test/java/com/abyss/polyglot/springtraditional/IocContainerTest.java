package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/** Executable proof that the container orders construction by dependency — building the
 *  dependency first and handing it over — and that beans are singletons by default. */

@Tag("ioc-container")
class IocContainerTest {

    @Configuration
    static class TinyConfig {
        @Bean String dependency() { return "wired"; }
        @Bean Holder holder(String dependency) { return new Holder(dependency); }
    }

    record Holder(String value) {}

    @Test
    void theContainerOrdersConstructionByDependency() {
        try (var context = new AnnotationConfigApplicationContext(TinyConfig.class)) {
            Holder holder = Launcher.lookup(context, Holder.class);
            assertEquals("wired", holder.value(),
                    "the container built the dependency first and handed it over");
            assertSame(holder, Launcher.lookup(context, Holder.class), "singleton by default");
        }
    }
}
