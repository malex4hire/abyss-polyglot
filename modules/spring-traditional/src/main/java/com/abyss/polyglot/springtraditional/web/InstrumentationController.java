package com.abyss.polyglot.springtraditional.web;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.config.ConfigurableListableBeanFactory;
import org.springframework.context.ApplicationContext;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Instrumentation, not contract: these endpoints report resolved runtime facts and are
 * no part of contract/openapi.yaml. Nothing here is a claimed identity. It is the
 * artifacts actually on the classpath, and the bean definitions the container resolved
 * together with where each was declared.
 *
 * The autoconfiguration-delta check reads the capability map from here and the live
 * condition-evaluation report from the Boot module, and computes the difference between
 * the two running artifacts.
 */
@RestController
public class InstrumentationController {

    private final ApplicationContext context;

    public InstrumentationController(ApplicationContext context) {
        this.context = context;
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of("status", "UP");
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
        doc.put("http_server_class", "org.apache.catalina.startup.Tomcat");
        doc.put("artifacts", artifacts());
        return doc;
    }

    /**
     * Capabilities this module declares explicitly, each with the site that declared it.
     * Read from the live bean factory, not from a maintained list.
     */
    @GetMapping("/__instrumentation/beans")
    public Map<String, Object> beans() {
        ConfigurableListableBeanFactory factory =
                ((org.springframework.context.ConfigurableApplicationContext) context).getBeanFactory();

        Map<String, Map<String, String>> capabilities = new LinkedHashMap<>();
        record Probe(String capability, Class<?> type) {}
        List<Probe> probes = List.of(
                new Probe("datasource", javax.sql.DataSource.class),
                new Probe("transaction-manager", org.springframework.transaction.PlatformTransactionManager.class),
                new Probe("jdbc-template", org.springframework.jdbc.core.JdbcTemplate.class),
                new Probe("property-resolution", org.springframework.context.support.PropertySourcesPlaceholderConfigurer.class),
                new Probe("dispatcher", org.springframework.web.servlet.DispatcherServlet.class));

        for (Probe probe : probes) {
            for (String name : factory.getBeanNamesForType(probe.type(), true, false)) {
                Map<String, String> detail = new LinkedHashMap<>();
                detail.put("bean", name);
                detail.put("source", "explicit");
                detail.put("declared_at", declaredAt(factory, name));
                capabilities.put(probe.capability(), detail);
                break;
            }
        }

        Map<String, Object> doc = new LinkedHashMap<>();
        doc.put("capabilities", capabilities);
        doc.put("beanDefinitionCount", factory.getBeanDefinitionCount());
        return doc;
    }

    private String declaredAt(ConfigurableListableBeanFactory factory, String name) {
        try {
            var definition = factory.getBeanDefinition(name);
            String source = definition.getResourceDescription();
            if (source != null && !source.isBlank()) {
                return source;
            }
            String factoryBean = definition.getFactoryBeanName();
            return factoryBean == null ? definition.getBeanClassName() : factoryBean;
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
                // The classpath carries target/classes itself, not only jars. That
                // entry is this module's own compiled output, listed alongside its
                // actual dependencies. It is neither a jar nor a version, and reporting
                // it as one is the defect: an artifact list read for exact versions
                // should never contain an entry with no version at all.
                if (name.endsWith(".jar")) {
                    found.add(name);
                }
            }
        }
        found.sort(String::compareTo);
        return List.copyOf(found);
    }
}
