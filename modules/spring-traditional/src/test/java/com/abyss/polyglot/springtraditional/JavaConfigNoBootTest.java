package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

/** Executable proof that the configuration classes are handed to the context by name,
 *  and that registering them is a separate decision from scanning for components. */
@Tag("java-config-no-boot")
class JavaConfigNoBootTest {

    @Test
    void configurationClassesAreNamedByHand() {
        var context = new AppInitializer().rootContext();

        assertTrue(context.containsBeanDefinition("rootConfig"),
                "RootConfig was handed to the reader by name, not discovered");
        assertTrue(context.containsBeanDefinition("webConfig"));
        assertFalse(context.containsBeanDefinition("workItemService"),
                "nothing was scanned yet — registration and scanning are separate decisions");
        context.close();
    }
}
