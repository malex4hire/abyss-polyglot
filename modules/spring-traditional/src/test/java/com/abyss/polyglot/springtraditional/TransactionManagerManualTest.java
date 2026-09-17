package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

/** Executable proof that @Transactional is inert without a hand-declared
 *  PlatformTransactionManager, and that the bean is wired to the datasource given it. */

@Tag("transaction-manager-manual")
class TransactionManagerManualTest {

    @Test
    void transactionalIsInertWithoutThisBean() {
        // Definitions, not instances. Refreshing the context would instantiate WebConfig's
        // @EnableWebMvc beans and fail for want of a ServletContext, and instantiation was
        // never the claim. The point is that the container's definition of this bean IS a
        // factory method on a configuration class, which is readable before anything runs.
        var registry = new org.springframework.beans.factory.support.DefaultListableBeanFactory();
        new org.springframework.context.annotation.AnnotatedBeanDefinitionReader(registry)
                .register(RootConfig.class);
        new org.springframework.context.annotation.ConfigurationClassPostProcessor()
                .postProcessBeanDefinitionRegistry(registry);
        // Constructing the manager by hand asserted only that a constructor stores its
        // argument, and passed just as well against a configuration that declared no bean
        // at all, the state RootConfig's own comment warns of, where @Transactional is
        // silently ignored and every statement commits alone.
        assertTrue(registry.containsBeanDefinition("transactionManager"),
                "without this definition @Transactional does nothing, and nothing says so");
        var definition = registry.getBeanDefinition("transactionManager");
        assertEquals("transactionManager", definition.getFactoryMethodName(),
                "declared here by hand, which is the whole point");

        // The definition checks above read the @Bean-annotated method's signature, which
        // an edit to the method body leaves untouched. Call the factory method directly,
        // no context refresh needed, and assert on the instance it actually returns: that
        // is what a stub body (one that throws, or returns null) fails.
        var dataSource = new DriverManagerDataSource();
        var manager = new RootConfig().transactionManager(dataSource);
        assertInstanceOf(DataSourceTransactionManager.class, manager);
        assertSame(dataSource, ((DataSourceTransactionManager) manager).getDataSource(),
                "the manager must be wired to the datasource it was handed");
    }
}
