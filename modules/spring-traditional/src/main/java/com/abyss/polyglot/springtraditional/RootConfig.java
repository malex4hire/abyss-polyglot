package com.abyss.polyglot.springtraditional;

import javax.sql.DataSource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.PropertySource;
import org.springframework.context.support.PropertySourcesPlaceholderConfigurer;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;

/**
 * The root application context, declared by hand.
 *
 * Everything the Boot module gets for free is written out here: the datasource, the
 * transaction manager, the JdbcTemplate, the property resolver, the scanned package.
 * That is not an inconvenience to be tidied away. It is the thing this module exists to
 * show. The autoconfiguration-delta check reads this hand-declared set and the Boot
 * module's live condition-evaluation report, and derives the difference between them.
 */
@Configuration
@EnableTransactionManagement
@PropertySource("classpath:application.properties")
@ComponentScan(basePackages = "com.abyss.polyglot.springtraditional")
public class RootConfig {

    /**
     * Resolves ${...} in @Value and in bean definitions. Without this bean the
     * placeholders arrive as literal text. Boot registers it for you, which is exactly
     * why its absence here is invisible until something reads a property and gets
     * "${db.url}" back.
     */
    @Bean
    public static PropertySourcesPlaceholderConfigurer propertyPlaceholderConfigurer() {
        return new PropertySourcesPlaceholderConfigurer();
    }

    /**
     * The datasource, constructed and configured by hand: driver, url, credentials. Boot
     * derives all four from properties and the driver on the classpath. Here the wiring
     * is the code, so there is no question about where the connection came from.
     */
    @Bean
    public DataSource dataSource(@Value("${db.url}") String url,
                                 @Value("${db.user}") String user,
                                 @Value("${db.password}") String password) {
        DriverManagerDataSource source = new DriverManagerDataSource();
        source.setDriverClassName("org.postgresql.Driver");
        source.setUrl(url);
        source.setUsername(user);
        source.setPassword(password);
        return source;
    }

    /**
     * The transaction manager, named and handed its datasource. @Transactional does
     * nothing without a PlatformTransactionManager bean to drive it, and nothing warns
     * you: the annotation is simply ignored and writes commit one statement at a time.
     */
    @Bean
    public PlatformTransactionManager transactionManager(DataSource dataSource) {
        return new DataSourceTransactionManager(dataSource);
    }

    /**
     * A bean declared by a factory method rather than discovered by scanning. The method
     * name is the bean name, the return type is the type the container registers, and the
     * parameters are the dependencies it must resolve first, so the definition and the
     * wiring are the same piece of code.
     */
    @Bean
    public JdbcTemplate jdbcTemplate(DataSource dataSource) {
        return new JdbcTemplate(dataSource);
    }

    /** initMethod rather than @PostConstruct: no extra annotation library on the
     *  classpath, and the lifecycle hook is stated at the definition site. */
    @Bean(initMethod = "initialize")
    public SchemaInitializer schemaInitializer(JdbcTemplate jdbcTemplate) {
        return new SchemaInitializer(jdbcTemplate);
    }
}
