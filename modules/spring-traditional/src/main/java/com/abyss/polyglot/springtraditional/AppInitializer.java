package com.abyss.polyglot.springtraditional;

import jakarta.servlet.ServletContext;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRegistration;
import org.springframework.context.annotation.AnnotatedBeanDefinitionReader;
import org.springframework.context.annotation.ClassPathBeanDefinitionScanner;
import org.springframework.web.WebApplicationInitializer;
import org.springframework.web.context.ContextLoaderListener;
import org.springframework.web.context.support.GenericWebApplicationContext;
import org.springframework.web.servlet.DispatcherServlet;

/**
 * Bootstrap without web.xml and without Boot.
 *
 * Every step Boot performs behind @SpringBootApplication is written out here: build the
 * context, read the configuration classes, scan the named package, create the dispatcher,
 * map it, set its startup order. Nothing is inferred from the classpath, and nothing is
 * inferred from where a class happens to live.
 */
public class AppInitializer implements WebApplicationInitializer {

    /**
     * The servlet container finds this class through the ServletContainerInitializer SPI
     * and calls it at startup. No web.xml, but no magic either: the hook is an interface
     * this class implements, and the order of what happens inside is ours to state.
     */
    @Override
    public void onStartup(ServletContext servletContext) throws ServletException {
        GenericWebApplicationContext root = rootContext();
        scanPackages(root);
        servletContext.addListener(new ContextLoaderListener(root));
        registerDispatcher(servletContext, root);
    }

    /**
     * The context, configured in Java rather than XML and without a starter. An
     * AnnotatedBeanDefinitionReader is handed the configuration classes by name — it is
     * the mechanism Boot drives for you — so what is registered is exactly what this
     * method says and nothing scans the classpath deciding what to switch on.
     */
    GenericWebApplicationContext rootContext() {
        GenericWebApplicationContext context = new GenericWebApplicationContext();
        new AnnotatedBeanDefinitionReader(context).register(RootConfig.class, WebConfig.class);
        return context;
    }

    /**
     * Scanning is opt-in and its scope is stated at the call. The scanner is an object we
     * construct and point at a package; Boot infers that package from wherever its
     * entry-point class happens to sit, so moving that class changes what is picked up.
     * Naming it means a file can move without changing what the container sees.
     */
    int scanPackages(GenericWebApplicationContext context) {
        return new ClassPathBeanDefinitionScanner(context)
                .scan("com.abyss.polyglot.springtraditional");
    }

    /**
     * The front controller, created and mapped by hand. Every request enters here, and
     * the dispatcher resolves a handler, invokes it, and picks a message converter for
     * the return value. Boot registers this servlet at "/" for you; doing it explicitly
     * makes the mapping, the name and the startup order visible decisions.
     */
    ServletRegistration.Dynamic registerDispatcher(ServletContext servletContext,
                                                   GenericWebApplicationContext root) {
        DispatcherServlet dispatcher = new DispatcherServlet(root);
        ServletRegistration.Dynamic registration =
                servletContext.addServlet("dispatcher", dispatcher);
        registration.setLoadOnStartup(1);
        registration.addMapping("/");
        // Async support is opt-in on the registration. Without it the container refuses
        // startAsync — "a filter or servlet of the current chain does not support
        // asynchronous operations" — and B4's stream cannot exist. Boot sets this for you;
        // here it is one more registration decision that has to be made out loud.
        registration.setAsyncSupported(true);
        return registration;
    }
}
