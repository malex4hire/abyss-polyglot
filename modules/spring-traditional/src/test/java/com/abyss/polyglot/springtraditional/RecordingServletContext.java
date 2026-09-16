package com.abyss.polyglot.springtraditional;

import jakarta.servlet.Servlet;
import jakarta.servlet.ServletRegistration;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;
import org.springframework.mock.web.MockServletContext;

/**
 * Test double.
 *
 * Spring's MockServletContext refuses addServlet outright, so the initializer tests have
 * nothing to observe without this. It records what was registered and how it was mapped,
 * which is exactly what those tests are asserting about.
 */
class RecordingServletContext extends MockServletContext {

    final Map<String, Servlet> servlets = new LinkedHashMap<>();
    final Map<String, Set<String>> mappings = new LinkedHashMap<>();
    final Map<String, Integer> startupOrder = new LinkedHashMap<>();
    final java.util.List<Object> listeners = new java.util.ArrayList<>();

    @Override
    public void addListener(java.util.EventListener listener) {
        listeners.add(listener);
    }

    @Override
    public void addListener(String className) {
        listeners.add(className);
    }

    @Override
    public void addListener(Class<? extends java.util.EventListener> listenerClass) {
        listeners.add(listenerClass);
    }

    @Override
    public ServletRegistration.Dynamic addServlet(String name, Servlet servlet) {
        servlets.put(name, servlet);
        mappings.put(name, new LinkedHashSet<>());
        return (ServletRegistration.Dynamic) java.lang.reflect.Proxy.newProxyInstance(
                getClass().getClassLoader(),
                new Class<?>[]{ServletRegistration.Dynamic.class},
                (proxy, method, args) -> switch (method.getName()) {
                    case "addMapping" -> {
                        for (Object mapping : (Object[]) args[0]) {
                            mappings.get(name).add(String.valueOf(mapping));
                        }
                        yield Set.of();
                    }
                    case "setLoadOnStartup" -> {
                        startupOrder.put(name, (Integer) args[0]);
                        yield null;
                    }
                    case "getMappings" -> mappings.get(name);
                    case "getName" -> name;
                    default -> null;
                });
    }
}
