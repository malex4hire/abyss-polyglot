package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.config.StartupReport;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/** Executable proof that the component-scan boundary is derived from the package the
 *  annotated application class sits in, rather than named anywhere. */
@Tag("implicit-component-scan")
@SpringBootTest
class ImplicitComponentScanTest {

    @Autowired
    StartupReport report;

    @Autowired
    org.springframework.context.ConfigurableApplicationContext context;

    @Test
    void theScanBoundaryIsAConsequenceOfWhereAFileSits() {
        // Compared against what Boot recorded, not against a string this test also knows.
        // The point is that the boundary follows the annotated class, so the assertion
        // has to come from the same place the value does.
        var recorded = org.springframework.boot.autoconfigure.AutoConfigurationPackages.get(
                context.getBeanFactory());

        assertEquals(recorded, report.scannedPackages(),
                "the scan root is what Boot registered from the application class's package");
        assertEquals(com.abyss.polyglot.springboot.Application.class.getPackageName(),
                report.scannedPackages().get(0),
                "and that package is the one the annotated class sits in");
    }
}
