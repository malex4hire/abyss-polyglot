package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

/** Executable proof that a @Bean factory method is both the definition and the wiring:
 *  the container reads it as a definition, and calling it returns the wired instance. */

@Tag("explicit-bean-definition")
class ExplicitBeanDefinitionTest {

    @Test
    void theFactoryMethodIsTheDefinitionAndTheWiring() {
        // Definitions, not instances. Refreshing the context would instantiate WebConfig's
        // @EnableWebMvc beans and fail for want of a ServletContext, and instantiation was
        // never the claim. The point is that the container's definition of this bean IS a
        // factory method on a configuration class, which is readable before anything runs.
        var registry = new org.springframework.beans.factory.support.DefaultListableBeanFactory();
        new org.springframework.context.annotation.AnnotatedBeanDefinitionReader(registry)
                .register(RootConfig.class);
        new org.springframework.context.annotation.ConfigurationClassPostProcessor()
                .postProcessBeanDefinitionRegistry(registry);
        var definition = registry.getBeanDefinition("jdbcTemplate");

        // Asking the class instead of the bean factory proved only that Java calls
        // methods, and passed identically against a version that registered the same bean
        // by component scanning, where the definition and the wiring stop being one thing.
        assertEquals("jdbcTemplate", definition.getFactoryMethodName(),
                "defined by a factory method, not discovered by a scan");
        assertNotNull(definition.getFactoryBeanName(),
                "and that method belongs to a configuration class");
        assertTrue(definition.getFactoryBeanName().toLowerCase().contains("rootconfig"),
                "declared in RootConfig, where the wiring is readable: "
                        + definition.getFactoryBeanName());

        // The checks above read the @Bean-annotated method's signature, which an edit to
        // the method body leaves untouched. Call the factory method directly, no context
        // refresh needed, and assert on the instance it actually returns: that is what a
        // stub body (one that throws, or returns null) fails.
        var dataSource = new DriverManagerDataSource();
        var template = new RootConfig().jdbcTemplate(dataSource);
        assertSame(dataSource, template.getDataSource(),
                "the definition and the wiring are the same piece of code");
    }
}
