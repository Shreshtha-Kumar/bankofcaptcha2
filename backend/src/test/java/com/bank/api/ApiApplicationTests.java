package com.bank.api;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

@SpringBootTest
@TestPropertySource(locations = "classpath:application-test.properties")
class ApiApplicationTests {

    @Test
    @DisplayName("Spring Application Context loads successfully")
    void contextLoads() {
    }
}

