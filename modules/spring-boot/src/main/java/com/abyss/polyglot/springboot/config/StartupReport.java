package com.abyss.polyglot.springboot.config;

import java.io.File;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import javax.sql.DataSource;
import org.springframework.beans.factory.config.ConfigurableListableBeanFactory;
import org.springframework.boot.autoconfigure.AutoConfigurationPackages;
import org.springframework.boot.autoconfigure.condition.ConditionEvaluationReport;
import org.springframework.context.ApplicationContext;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.core.env.PropertySource;
import org.springframework.stereotype.Component;

/**
 * What the framework decided at startup, read back from the running context.
 *
 * Every method here answers a question the traditional module answers by pointing at a
 * line of its own configuration. Here there is no such line, so the answer has to be
 * obtained from the container — which is precisely the contrast.
 */
@Component
public class StartupReport {

    private final ApplicationContext context;
    private final ConfigurableEnvironment environment;
    private final DataSource dataSource;

    public StartupReport(ApplicationContext context, ConfigurableEnvironment environment,
                         DataSource dataSource) {
        this.context = context;
        this.environment = environment;
        this.dataSource = dataSource;
    }

    /**
     * Which starters actually resolved. A starter is not a library: it is a pom with no
     * code that pulls a coherent set of libraries AND the auto-configuration that
     * switches them on. Adding one line to the build is what puts a web server, a JSON
     * converter and an exception handler into the application at once.
     *
     * The traditional module pins each library and its version by hand, which is longer
     * and is also the only way to know exactly what is on the classpath.
     */
    public List<String> starters() {
        List<String> found = new ArrayList<>();
        for (String element : System.getProperty("java.class.path", "").split(File.pathSeparator)) {
            String name = new File(element).getName();
            if (name.startsWith("spring-boot-starter")) {
                found.add(name);
            }
        }
        found.sort(String::compareTo);
        return List.copyOf(found);
    }

    /**
     * The conditions that matched. Every auto-configuration class is a guarded set of
     * bean definitions: @ConditionalOnClass, @ConditionalOnMissingBean and friends decide
     * at startup whether to contribute. "Convention" is not vagueness — it is this report,
     * and it is readable at runtime.
     *
     * @ConditionalOnMissingBean is the part that matters: declare your own DataSource and
     * Boot's stands down. Convention yields to configuration rather than fighting it.
     */
    public int autoConfigurationsApplied() {
        ConfigurableListableBeanFactory factory =
                ((ConfigurableApplicationContext) context).getBeanFactory();
        ConditionEvaluationReport report = ConditionEvaluationReport.get(factory);
        return (int) report.getConditionAndOutcomesBySource().values().stream()
                .filter(ConditionEvaluationReport.ConditionAndOutcomes::isFullMatch)
                .count();
    }

    /**
     * The package being scanned, which nothing in this module states. Boot registers the
     * package of the @SpringBootApplication class and scans downward from there, so the
     * scan boundary is a consequence of where a file sits.
     *
     * Move Application.java one package up and the scope silently widens; move it down and
     * beans vanish with no error. The traditional module names the package to a scanner,
     * so moving a file cannot change what the container sees.
     */
    public List<String> scannedPackages() {
        return AutoConfigurationPackages.get(
                ((ConfigurableApplicationContext) context).getBeanFactory());
    }

    /**
     * The server the application started inside itself. There is no container to deploy
     * to and no war lifecycle to await: the servlet container is a bean, chosen because a
     * web starter is on the classpath, and the application owns a main method.
     *
     * That inversion is the era difference. The traditional module is a war a container
     * starts; this is a program that starts a container.
     */
    public String embeddedServer() {
        return context.getBean(
                org.springframework.boot.web.server.servlet.ServletWebServerFactory.class)
                .getClass().getSimpleName();
    }

    /**
     * Which profiles are active. A profile gates beans and property files by name, so one
     * artifact behaves differently per environment without a rebuild — and with no
     * profile set, "default" is what is active, which is worth knowing before wondering
     * why a bean did not appear.
     */
    public List<String> activeProfiles() {
        String[] active = environment.getActiveProfiles();
        return active.length == 0 ? List.of("default") : List.of(active);
    }

    /**
     * The property sources, in the order they are consulted. First match wins, and the
     * order is the contract: command-line arguments override environment variables,
     * which override profile-specific files, which override application.properties.
     *
     * The traditional module registers one placeholder resolver over one file. Here the
     * layering is inherited, which is why "it works locally" and "it does not work in the
     * container" is usually a question about this list rather than about the code.
     */
    public List<String> propertySourceOrder() {
        List<String> names = new ArrayList<>();
        for (PropertySource<?> source : environment.getPropertySources()) {
            names.add(source.getName());
        }
        return List.copyOf(names);
    }

    /**
     * The datasource nobody in this module constructed. Boot saw a JDBC driver and a
     * spring.datasource.url, chose a connection pool from what was on the classpath, and
     * built it — pool included, which the traditional module's DriverManagerDataSource
     * does not have at all.
     *
     * The convenience is real and so is the cost: when the pool misbehaves, the
     * configuration that produced it is in a library rather than in your source.
     */
    public Map<String, String> datasourceDetail() {
        Map<String, String> detail = new LinkedHashMap<>();
        detail.put("implementation", dataSource.getClass().getName());
        detail.put("declaredInThisModule", "false");
        return detail;
    }
}
