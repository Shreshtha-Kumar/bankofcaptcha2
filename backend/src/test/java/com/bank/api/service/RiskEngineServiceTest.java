package com.bank.api.service;

import com.bank.api.model.AiAlert;
import com.bank.api.model.User;
import com.bank.api.repository.AiAlertRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class RiskEngineServiceTest {

    @Mock
    private AiAlertRepository aiAlertRepository;

    @Mock
    private AlertService alertService;

    private RiskEngineService riskEngineService;
    private User testUser;

    @BeforeEach
    void setUp() {
        riskEngineService = new RiskEngineService(aiAlertRepository, alertService);
        testUser = new User();
        testUser.setUsername("testuser");
    }

    @Test
    @DisplayName("evaluateTransaction allows transaction when no open alerts exist")
    void evaluateTransaction_AllowedWhenNoAlerts() {
        when(aiAlertRepository.findByFlaggedUsernameAndStatus("testuser", "OPEN"))
                .thenReturn(Collections.emptyList());

        RiskEngineService.RiskEvaluation evaluation = riskEngineService.evaluateTransaction(
                testUser,
                new BigDecimal("500.00"),
                "1000000001"
        );

        assertTrue(evaluation.allowed());
        assertEquals("Transaction risk is within acceptable parameters.", evaluation.message());
    }

    @Test
    @DisplayName("evaluateTransaction blocks transaction when user has active high-risk alert")
    void evaluateTransaction_BlockedWhenActiveAlert() {
        AiAlert alert = new AiAlert();
        alert.setFlaggedUsername("testuser");
        alert.setStatus("OPEN");
        alert.setSeverity("HIGH");

        when(aiAlertRepository.findByFlaggedUsernameAndStatus("testuser", "OPEN"))
                .thenReturn(List.of(alert));

        RiskEngineService.RiskEvaluation evaluation = riskEngineService.evaluateTransaction(
                testUser,
                new BigDecimal("500.00"),
                "1000000001"
        );

        assertFalse(evaluation.allowed());
        assertEquals("Transaction blocked due to active high-risk alerts.", evaluation.message());
    }

    @Test
    @DisplayName("evaluateBulkDataAccess blocks privileged access when user has open alerts")
    void evaluateBulkDataAccess_BlockedWhenOpenAlerts() {
        AiAlert alert = new AiAlert();
        alert.setStatus("OPEN");

        when(aiAlertRepository.findByFlaggedUsernameAndStatus("testuser", "OPEN"))
                .thenReturn(List.of(alert));

        RiskEngineService.RiskEvaluation evaluation = riskEngineService.evaluateBulkDataAccess(
                testUser,
                "/api/accounts"
        );

        assertFalse(evaluation.allowed());
    }
}
