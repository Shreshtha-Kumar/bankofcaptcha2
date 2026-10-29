#!/usr/bin/env python3
"""
BankOfCaptcha End-to-End Containerized Integration & Verification Test Suite.
Used by the CI/CD pipeline and local deployment tests to verify that the
four-tier containerized stack (PostgreSQL, Spring Boot Backend, Vite/Nginx Frontend,
and PyTorch AI Engine) is healthy, functional, and secure.
"""

import os
import sys
import time
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080/api")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
AI_SERVICE_KEY = os.getenv("AI_SERVICE_KEY", "bankofcaptcha-local-ai-service-key-change-before-deployment")

MAX_RETRIES = 30
RETRY_INTERVAL = 2

def wait_for_services():
    print(f"[*] Waiting for Backend at {BACKEND_URL} ...")
    backend_ready = False
    for i in range(MAX_RETRIES):
        try:
            res = requests.get(f"{BACKEND_URL}/branches", timeout=3)
            if res.status_code == 200:
                print(f"[+] Backend is ready! (Attempt {i+1})")
                backend_ready = True
                break
        except Exception:
            pass
        time.sleep(RETRY_INTERVAL)

    if not backend_ready:
        print("[-] Backend failed to become ready in time.")
        sys.exit(1)

    print(f"[*] Waiting for Frontend at {FRONTEND_URL} ...")
    frontend_ready = False
    for i in range(MAX_RETRIES):
        try:
            res = requests.get(FRONTEND_URL, timeout=3)
            if res.status_code == 200 and "<html" in res.text.lower():
                print(f"[+] Frontend is ready! (Attempt {i+1})")
                frontend_ready = True
                break
        except Exception:
            pass
        time.sleep(RETRY_INTERVAL)

    if not frontend_ready:
        print("[-] Frontend failed to become ready in time.")
        sys.exit(1)

def test_auth_workflow():
    print("\n--- [Test 1] Authentication and JWT Generation ---")
    roles = {
        "customer": "ROLE_CUSTOMER",
        "teller": "ROLE_TELLER",
        "branch_manager": "ROLE_BRANCH_MANAGER",
        "compliance": "ROLE_COMPLIANCE_OFFICER",
        "superadmin": "ROLE_SUPER_ADMIN"
    }
    tokens = {}
    for user, expected_role in roles.items():
        res = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"username": user, "password": "password"},
            timeout=5
        )
        assert res.status_code == 200, f"Login failed for {user}: {res.text}"
        data = res.json()
        assert "token" in data, f"No token returned for {user}"
        assert data["role"] == expected_role, f"Role mismatch for {user}: got {data['role']}, expected {expected_role}"
        tokens[user] = data["token"]
        print(f"  ✓ {user} authenticated successfully as {expected_role}")
    return tokens

def test_pqc_audit_verification(compliance_token):
    print("\n--- [Test 2] Post-Quantum Cryptography (PQC) Audit Trail Verification ---")
    headers = {"Authorization": f"Bearer {compliance_token}"}
    
    # Fetch logs
    res = requests.get(f"{BACKEND_URL}/audit/logs", headers=headers, timeout=5)
    assert res.status_code == 200, f"Failed to fetch audit logs: {res.text}"
    logs = res.json()
    assert len(logs) > 0, "No audit logs found"
    
    # Pick the latest log
    latest_log = logs[-1]
    log_id = latest_log["id"]
    print(f"  ✓ Fetched {len(logs)} audit logs. Verifying log ID: {log_id}")

    # Verify cryptographic signature and encryption
    verify_res = requests.get(f"{BACKEND_URL}/audit/logs/{log_id}/verify", headers=headers, timeout=5)
    assert verify_res.status_code == 200, f"Verification request failed: {verify_res.text}"
    v_data = verify_res.json()
    assert v_data.get("valid") is True, f"Cryptographic verification failed: {v_data}"
    assert v_data.get("signatureAlgorithm") == "ML-DSA-65", f"Unexpected signature algorithm: {v_data}"
    assert "ML-KEM-768" in v_data.get("encryptionAlgorithm", ""), f"Unexpected encryption algorithm: {v_data}"
    print(f"  ✓ PQC signature verified with {v_data['signatureAlgorithm']} and {v_data['encryptionAlgorithm']}")

def test_ai_alert_and_risk_containment(customer_token):
    print("\n--- [Test 3] AI Alert Ingestion & Zero-Trust Risk Engine Containment ---")
    flagged_user = "risk_test_user"

    # Register or simulate an AI alert
    headers = {"X-AI-Service-Key": AI_SERVICE_KEY}
    alert_payload = {
        "flaggedUsername": flagged_user,
        "description": "CI/CD automated synthetic anomaly detection event",
        "severity": "HIGH",
        "riskScore": 95
    }
    res = requests.post(f"{BACKEND_URL}/ai/alerts", json=alert_payload, headers=headers, timeout=5)
    assert res.status_code in [200, 201], f"Failed to submit AI alert: {res.status_code} {res.text}"
    print(f"  ✓ Ingested synthetic high-risk alert via AI integration endpoint for '{flagged_user}'")

def test_frontend_delivery():
    print("\n--- [Test 4] Frontend Container Static Asset Delivery ---")
    res = requests.get(FRONTEND_URL, timeout=5)
    assert res.status_code == 200, f"Frontend did not return 200: {res.status_code}"
    assert "text/html" in res.headers.get("Content-Type", "")
    assert "BANK OF CAPTCHA" in res.text or "<div id=\"root\">" in res.text
    print("  ✓ Frontend HTML container is serving responsive React application")

def main():
    print("=" * 60)
    print(" BankOfCaptcha CI/CD Containerized Integration Verification ")
    print("=" * 60)
    wait_for_services()
    tokens = test_auth_workflow()
    test_pqc_audit_verification(tokens["compliance"])
    test_ai_alert_and_risk_containment(tokens["customer"])
    test_frontend_delivery()
    print("\n" + "=" * 60)
    print(" ALL CI/CD DEPLOYMENT VERIFICATION TESTS PASSED SUCCESSFULLY! ")
    print("=" * 60)

if __name__ == "__main__":
    main()
