package com.abyss.polyglot.springboot.web;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.config.ConfigurableListableBeanFactory;
import org.springframework.boot.autoconfigure.condition.ConditionEvaluationReport;
import org.springframework.context.ApplicationContext;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Instrumentation, not part of the contract. Reports resolved runtime data — never a
 * claimed identity.
 *
 * The auto-configuration report is Boot's own condition evaluation, read live. The
 * autoconfiguration-delta check pairs it against the traditional module's explicit bean
 * set and derives the difference from the two running applications rather than from
 * anything asserted in prose.
 */
@RestController
public class InstrumentationController {

    private final ApplicationContext context;

    public InstrumentationController(ApplicationContext context) {
        this.context = context;
    }

    @GetMapping("/__instrumentation/identity")
    public Map<String, Object> identity() {
        Map<String, Object> doc = new LinkedHashMap<>();
        doc.put("runtime_version", System.getProperty("java.version"));
        // The exact build, not the marketing version. "25.0.3" is what the floor is
        // compared against and stays the parseable field; this is the string that
        // identifies precisely which JDK produced the answers on this page.
        doc.put("runtime_version_exact", System.getProperty("java.runtime.version"));
        doc.put("runtime_vendor", System.getProperty("java.vendor"));
        doc.put("runtime_vendor_version", System.getProperty("java.vendor.version"));
        doc.put("http_server_class", context.getBean(
                org.springframework.boot.web.server.servlet.ServletWebServerFactory.class)
                .getClass().getName());
        doc.put("artifacts", artifacts());
        return doc;
    }

    /**
     * Which capability each bean came from, and whether auto-configuration supplied it.
     * Read from the live bean factory and Boot's condition report, not a maintained list.
     */
    @GetMapping("/__instrumentation/autoconfig")
    public Map<String, Object> autoconfig() {
        ConfigurableListableBeanFactory factory =
                ((ConfigurableApplicationContext) context).getBeanFactory();
        ConditionEvaluationReport report = ConditionEvaluationReport.get(factory);

        record Probe(String capability, Class<?> type) {}
        List<Probe> probes = List.of(
                new Probe("datasource", javax.sql.DataSource.class),
                new Probe("transaction-manager", org.springframework.transaction.PlatformTransactionManager.class),
                new Probe("jdbc-template", org.springframework.jdbc.core.JdbcTemplate.class),
                new Probe("property-resolution", org.springframework.context.support.PropertySourcesPlaceholderConfigurer.class),
                new Probe("dispatcher", org.springframework.web.servlet.DispatcherServlet.class),
                new Probe("servlet-container", org.springframework.boot.web.server.servlet.ServletWebServerFactory.class));

        // The set of auto-configuration classes whose conditions matched, read from
        // Boot's own report. A bean is auto-configured when its declaring class is one of
        // these, or nested inside one — which is a fact from the report rather than a
        // guess from a class name. Matching on the string "AutoConfiguration" got five of
        // six wrong, because most declaring classes are nested Configuration classes
        // whose names do not contain it.
        List<String> positives = new ArrayList<>(
                report.getConditionAndOutcomesBySource().entrySet().stream()
                        .filter(entry -> entry.getValue().isFullMatch())
                        .map(Map.Entry::getKey)
                        .toList());
        positives.sort(String::compareTo);

        Map<String, Map<String, String>> capabilities = new LinkedHashMap<>();
        for (Probe probe : probes) {
            for (String name : factory.getBeanNamesForType(probe.type(), true, false)) {
                Map<String, String> detail = new LinkedHashMap<>();
                detail.put("bean", name);
                String site = declaredAt(factory, name);
                detail.put("declared_at", site);
                // A declaration site arrives either as a class name or as a classpath
                // resource path, depending on how the definition was registered. Both
                // forms are compared, so the answer does not depend on which one Spring
                // happened to record.
                // Report entries may name a bean method (Class#method) and declaration
                // sites may be class names or classpath resource paths. Compare on the
                // declaring class alone, in both notations.
                boolean fromAutoConfig = positives.stream().anyMatch(applied -> {
                    String cls = applied.contains("#") ? applied.substring(0, applied.indexOf('#')) : applied;
                    return site.equals(cls)
                            || site.startsWith(cls + "$")
                            || site.contains(cls.replace('.', '/'));
                });
                detail.put("source", fromAutoConfig ? "auto-configuration" : "explicit");
                capabilities.put(probe.capability(), detail);
                break;
            }
        }

        Map<String, Object> doc = new LinkedHashMap<>();
        doc.put("capabilities", capabilities);
        doc.put("autoConfigurationsApplied", positives);
        return doc;
    }

    private String declaredAt(ConfigurableListableBeanFactory factory, String name) {
        try {
            var definition = factory.getBeanDefinition(name);
            String factoryBean = definition.getFactoryBeanName();
            if (factoryBean != null && !factoryBean.isBlank()) {
                return factoryBean;
            }
            String source = definition.getResourceDescription();
            return source == null || source.isBlank()
                    ? String.valueOf(definition.getBeanClassName()) : source;
        } catch (Exception e) {
            return "unknown";
        }
    }

    private List<String> artifacts() {
        List<String> found = new ArrayList<>();
        for (String element : System.getProperty("java.class.path", "")
                .split(java.io.File.pathSeparator)) {
            if (!element.isBlank()) {
                String name = new java.io.File(element).getName();
                // The classpath carries target/classes itself, not only jars — this
                // module's own compiled output, listed alongside its actual dependencies.
                // It is neither a jar nor a version, and reporting it as one is the
                // defect: an artifact list read for exact versions should never contain
                // an entry with no version at all.
                if (name.endsWith(".jar")) {
                    found.add(name);
                }
            }
        }
        found.sort(String::compareTo);
        return List.copyOf(found);
    }
}
