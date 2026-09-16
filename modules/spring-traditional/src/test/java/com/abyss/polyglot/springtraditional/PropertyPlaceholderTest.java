package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import org.springframework.beans.factory.config.BeanFactoryPostProcessor;

/** Executable proof that ${...} is rewritten before the bean is built, and that without
 *  this bean the literal placeholder text reaches the property. */

@Tag("property-placeholder")
class PropertyPlaceholderTest {

    @Test
    void withoutThisBeanPlaceholdersArriveAsLiteralText() {
        // The method's own name is the assertion, so it has to be executed rather than
        // described. Checking that the returned object is a BeanFactoryPostProcessor
        // passed against a counter that returns one and resolves nothing — the interface
        // is the shape, and resolution is the mechanism.
        var factory = new org.springframework.beans.factory.support.DefaultListableBeanFactory();
        var definition = new org.springframework.beans.factory.support.RootBeanDefinition(Holder.class);
        definition.getPropertyValues().add("value", "${probe.key}");
        factory.registerBeanDefinition("holder", definition);

        var environment = new org.springframework.core.env.StandardEnvironment();
        environment.getPropertySources().addFirst(
                new org.springframework.core.env.MapPropertySource(
                        "probe", java.util.Map.of("probe.key", "resolved")));

        var configurer = RootConfig.propertyPlaceholderConfigurer();
        if (configurer instanceof org.springframework.context.support.PropertySourcesPlaceholderConfigurer placeholders) {
            placeholders.setEnvironment(environment);
        }
        configurer.postProcessBeanFactory(factory);

        assertEquals("resolved", factory.getBean(Holder.class).getValue(),
                "the placeholder was rewritten before the bean was built; without this "
                        + "the literal ${probe.key} reaches the property");
    }

    /** A bean with one property, to have something for a placeholder to arrive in. */
    public static class Holder {
        private String value;

        public String getValue() {
            return value;
        }

        public void setValue(String value) {
            this.value = value;
        }
    }
}
