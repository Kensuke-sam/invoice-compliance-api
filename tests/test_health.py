from __future__ import annotations

from fastapi.testclient import TestClient


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_protected_route_requires_api_key(client: TestClient) -> None:
    payload = {
        "vendor_name": "ACME Hosting",
        "invoice_number": "INV-2026-001",
        "currency": "JPY",
        "total_amount": 128000.0,
        "line_items": [
            {"description": "Hosting fee", "amount": "100000"},
            {"description": "Support surcharge", "amount": "28000"},
        ],
    }
    response = client.post("/invoices", json=payload)
    assert response.status_code == 401
