"""The parts that matter most in payments: auth, validation, idempotency, signatures.

Run:  pytest -q
"""
import json

from app.config import settings
from app.helpers.security import sign

KEY = {"x-api-key": settings.api_key}     # whatever key .env defines


def send_webhook(client, event: dict, signature: str | None = None):
    body = json.dumps(event).encode()
    return client.post("/webhooks/payment", content=body, headers={"x-signature": signature or sign(body)})


def create_link(client, fine_id: str) -> dict:
    return client.post("/payments", json={"fine_id": fine_id}, headers=KEY).json()


def test_requires_api_key(client):
    assert client.get("/fines/A12345").status_code == 422                       # header missing
    assert client.get("/fines/A12345", headers={"x-api-key": "wrong"}).status_code == 401


def test_get_fines_normalises_plate(client):
    r = client.get("/fines/a 12345", headers=KEY)
    assert r.status_code == 200
    assert [f["fine_id"] for f in r.json()] == ["F-1001", "F-1002"]


def test_rejects_bad_plate(client):
    assert client.get("/fines/DROP TABLE", headers=KEY).status_code == 422


def test_unknown_fine_is_404(client):
    assert client.post("/payments", json={"fine_id": "F-9999"}, headers=KEY).status_code == 404


def test_payment_link_is_idempotent(client):
    assert create_link(client, "F-1001")["payment_id"] == create_link(client, "F-1001")["payment_id"]


def test_webhook_bad_signature_rejected(client):
    pay = create_link(client, "F-1001")
    event = {"event_id": "EVT-1", "type": "payment.succeeded", "payment_id": pay["payment_id"]}
    assert send_webhook(client, event, signature="forged").status_code == 401


def test_duplicate_webhook_processed_once(client):
    pay = create_link(client, "F-1001")
    event = {"event_id": "EVT-42", "type": "payment.succeeded", "payment_id": pay["payment_id"]}

    assert send_webhook(client, event).json() == {"status": "ok"}
    assert send_webhook(client, event).json() == {"status": "already processed"}

    assert client.get(f"/payments/{pay['payment_id']}", headers=KEY).json()["status"] == "paid"
    assert [f["fine_id"] for f in client.get("/fines/A12345", headers=KEY).json()] == ["F-1002"]


def test_cannot_pay_twice(client):
    pay = create_link(client, "F-2001")
    send_webhook(client, {"event_id": "EVT-7", "type": "payment.succeeded", "payment_id": pay["payment_id"]})
    assert client.post("/payments", json={"fine_id": "F-2001"}, headers=KEY).status_code == 409


def test_mock_checkout_marks_paid(client):
    pay = create_link(client, "F-1002")
    assert client.post(f"/checkout/{pay['payment_id']}/pay").status_code == 200
    assert client.get(f"/payments/{pay['payment_id']}", headers=KEY).json()["status"] == "paid"
