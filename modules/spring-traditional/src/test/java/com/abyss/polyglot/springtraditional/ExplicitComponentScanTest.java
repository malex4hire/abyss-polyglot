package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that scanning is opt-in and its scope is a package that was named,
 *  so classes nobody enumerated are still registered. */
@Tag("explicit-component-scan")
class ExplicitComponentScanTest {

    @Test
    void scanningIsOptInAndItsScopeIsStated() {
        // A bare context, so this exercises the scanner and nothing else.
        var context = new org.springframework.web.context.support.GenericWebApplicationContext();

        int registered = new AppInitializer().scanPackages(context);

        assertTrue(registered > 0, "the scan registered definitions");
        assertTrue(context.containsBeanDefinition("workItemService"),
                "the annotated service was found in the package we named");
        // The scope is the package, not a list. Naming two classes by hand satisfies every
        // assertion above and stops finding anything nobody remembered to add — which is
        // the whole difference, and is only visible by asking for a class that such a
        // hand-written list would not mention.
        assertTrue(context.containsBeanDefinition("workItemRepository")
                        && context.containsBeanDefinition("workloadController"),
                "everything annotated in the package is registered, not an enumerated few: "
                        + java.util.Arrays.toString(context.getBeanDefinitionNames()));
        context.close();
    }
}
