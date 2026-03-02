from __future__ import annotations

from fastapi.testclient import TestClient


def test_workflow(client: TestClient, auth_headers: dict[str, str]) -> None:
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
    create_response = client.post(
        "/invoices",
        json=payload,
        headers=auth_headers,
    )
    assert create_response.status_code == 201

    record_id = create_response.json()["id"]
    analysis_response = client.post(
        f"/invoices/{record_id}/review",
        headers=auth_headers,
    )
    assert analysis_response.status_code == 200
    assert analysis_response.json()["approval_hint"] == "needs_manual_review"

    get_response = client.get(
        f"/invoices/{record_id}/review",
        headers=auth_headers,
    )
    assert get_response.status_code == 200
