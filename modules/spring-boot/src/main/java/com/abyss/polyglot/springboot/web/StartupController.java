package com.abyss.polyglot.springboot.web;

import com.abyss.polyglot.springboot.config.DemoProperties;
import com.abyss.polyglot.springboot.config.StartupReport;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Serves what the framework decided at startup.
 *
 * This is the request path that keeps every StartupReport method load-bearing: each one
 * is called to build a real response, not only from its own test.
 */
@RestController
public class StartupController {

    private final StartupReport report;
    private final DemoProperties properties;

    public StartupController(StartupReport report, DemoProperties properties) {
        this.report = report;
        this.properties = properties;
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        Map<String, Object> doc = new LinkedHashMap<>();
        doc.put("status", "UP");
        doc.put("label", properties.getLabel());
        doc.put("seedCount", properties.getSeedCount());
        doc.put("configuration", properties.describe());
        doc.put("starters", report.starters());
        doc.put("autoConfigurationsApplied", report.autoConfigurationsApplied());
        doc.put("scannedPackages", report.scannedPackages());
        doc.put("embeddedServer", report.embeddedServer());
        doc.put("activeProfiles", report.activeProfiles());
        doc.put("propertySourceOrder", report.propertySourceOrder());
        doc.put("datasource", report.datasourceDetail());
        return doc;
    }
}
