package com.abyss.polyglot.springboot.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Typed configuration. Bound from properties by prefix, converted and checked at startup.
 */
@ConfigurationProperties(prefix = "demo")
public class DemoProperties {

    private String label = "unset";
    private int seedCount = 0;

    public void setLabel(String label) {
        this.label = label;
    }

    public void setSeedCount(int seedCount) {
        this.seedCount = seedCount;
    }

    public String getLabel() {
        return label;
    }

    public int getSeedCount() {
        return seedCount;
    }

    /**
     * What binding produced, stated in the types the fields declare.
     *
     * Nothing here parses a string. "demo.seed-count" reached the int field as an int:
     * relaxed binding matched the kebab-case property to the camelCase name, and a value
     * that would not convert would have failed the context at startup rather than
     * surfacing at first read. That is the difference from a placeholder resolver, which
     * hands back whatever text it found, one key at a time, whenever the bean is built.
     *
     * This method, rather than a setter, is where the result of binding is worth reading.
     * Spring calls the setters during binding, so breaking one fails the context itself
     * and reddens every test in the module at once, instead of the one test that is
     * actually about binding.
     */
    public String describe() {
        return "%s expects %d seeded items".formatted(label, seedCount);
    }
}
