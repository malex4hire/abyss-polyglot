package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import org.apache.catalina.LifecycleState;
import org.apache.catalina.startup.Tomcat;

/** Executable proof that a war has no main method: the servlet container is told to
 *  start explicitly and reports the STARTED lifecycle state. */

@Tag("war-packaging-lifecycle")
class WarPackagingLifecycleTest {

    @Test
    void theContainerIsStartedExplicitlyRatherThanHavingAMain() throws Exception {
        var tomcat = new Tomcat();
        tomcat.setPort(0);
        tomcat.getConnector();
        tomcat.addContext("", System.getProperty("java.io.tmpdir"));

        Launcher.startLifecycle(tomcat);

        assertEquals(LifecycleState.STARTED, tomcat.getServer().getState(),
                "a war has no main; the container is told to start");
        tomcat.stop();
        tomcat.destroy();
    }
}
