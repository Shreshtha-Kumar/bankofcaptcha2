package com.bank.api.service;

import com.bank.api.config.properties.PqcConfigProperties;
import com.bank.api.model.AuditLog;
import com.bank.api.repository.AuditLogRepository;
import com.bank.api.repository.PqcKeyMaterialRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@TestPropertySource(locations = "classpath:application-test.properties")
class PqcAuditServiceTest {

    @Autowired
    private PqcAuditService pqcAuditService;

    @Autowired
    private AuditLogRepository auditLogRepository;

    @Autowired
    private PqcKeyMaterialRepository keyMaterialRepository;

    @Test
    @DisplayName("PQC Audit Service seals an event with ML-DSA-65 signature and ML-KEM-768 encapsulation")
    void testRecordAndVerifyAuditLog() {
        LocalDateTime now = LocalDateTime.now();
        String username = "compliance_tester";
        String action = "AUDIT_VERIFICATION_TEST";

        AuditLog savedLog = pqcAuditService.record(username, action, now);

        assertNotNull(savedLog);
        assertNotNull(savedLog.getId());
        assertEquals("ML-DSA-65", savedLog.getSignatureAlgorithm());
        assertEquals("ML-KEM-768 + AES-256-GCM", savedLog.getEncryptionAlgorithm());
        assertNotNull(savedLog.getPqcSignature());
        assertNotNull(savedLog.getEncryptedPayload());
        assertNotNull(savedLog.getKemEncapsulation());

        // Verify the cryptographic integrity of the sealed record
        PqcAuditService.VerificationResult verification = pqcAuditService.verify(savedLog);
        assertTrue(verification.valid(), "PQC cryptographic verification should pass");
        assertEquals("PQC signature and encrypted evidence are valid.", verification.message());
        assertNotNull(verification.verifiedPayload());
    }

    @Test
    @DisplayName("PQC Audit Service rejects tampered audit metadata")
    void testTamperedAuditLogFailsVerification() {
        LocalDateTime now = LocalDateTime.now();
        AuditLog savedLog = pqcAuditService.record("alice", "TRANSFER_FUNDS", now);

        // Tamper with the visible action metadata
        savedLog.setAction("TAMPERED_ACTION");

        PqcAuditService.VerificationResult verification = pqcAuditService.verify(savedLog);
        assertFalse(verification.valid(), "Tampered log must fail cryptographic verification");
    }
}
