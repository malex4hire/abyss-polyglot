package com.abyss.polyglot.springtraditional;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import org.springframework.jdbc.datasource.DriverManagerDataSource;

/** Executable proof that driver url, username and password are all stated by hand here
 *  rather than inferred from anything on the classpath. */

@Tag("datasource-manual-wiring")
class DatasourceManualWiringTest {

    @Test
    void driverUrlAndCredentialsAreAllStated() {
        var source = (DriverManagerDataSource) new RootConfig()
                .dataSource("jdbc:postgresql://db/demo", "demo", "secret");

        assertEquals("jdbc:postgresql://db/demo", source.getUrl());
        assertEquals("demo", source.getUsername());
        assertEquals("secret", source.getPassword());
    }
}
