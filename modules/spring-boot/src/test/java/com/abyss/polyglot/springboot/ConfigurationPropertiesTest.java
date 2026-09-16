package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.config.DemoProperties;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.boot.autoconfigure.context.ConfigurationPropertiesAutoConfiguration;
import org.springframework.boot.autoconfigure.context.PropertyPlaceholderAutoConfiguration;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import org.springframework.context.annotation.Configuration;

/** Executable proof that @ConfigurationProperties binds kebab-case keys onto typed
 *  fields, converting as it goes and failing at startup when a value will not convert. */
@Tag("configuration-properties")
class ConfigurationPropertiesTest {

    @Configuration
    @EnableConfigurationProperties(DemoProperties.class)
    static class Config {
    }

    private final ApplicationContextRunner runner = new ApplicationContextRunner()
            .withConfiguration(org.springframework.boot.autoconfigure.AutoConfigurations.of(
                    ConfigurationPropertiesAutoConfiguration.class,
                    PropertyPlaceholderAutoConfiguration.class))
            .withUserConfiguration(Config.class);

    @Test
    void bindingProducesTypedFieldsNotStrings() {
        // Real Spring binding, not a hand-built POJO: kebab-case in the property source,
        // camelCase on the field, a string value converted to int — the three things a
        // manually constructed and manually set DemoProperties can never exercise, which
        // is exactly what let an earlier version of this test pass against a
        // DemoProperties that had never been through binding at all.
        runner.withPropertyValues("demo.label=probe", "demo.seed-count=41").run((context) -> {
            var properties = context.getBean(DemoProperties.class);
            assertEquals("probe expects 41 seeded items", properties.describe(),
                    "relaxed binding matched demo.seed-count to seedCount and converted "
                            + "the string to an int; nothing here set a field by hand");
        });
    }

    @Test
    void aValueThatDoesNotConvertFailsAtBindingNotAtFirstRead() {
        // The docstring's other claim: a bad value fails the context at startup rather
        // than surfacing later. A hand-constructed properties.setSeedCount(...) call
        // cannot fail this way — there is no string to convert, only an int already typed.
        runner.withPropertyValues("demo.seed-count=not-a-number").run((context) ->
                assertTrue(context.getStartupFailure() != null,
                        "an unconvertible value should fail context startup, not read as 0"));
    }
}
