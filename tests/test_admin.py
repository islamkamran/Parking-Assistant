"""Admin endpoints: separate key, create/list/delete, and protection of paid fines."""
from app.config import settings

ADMIN = {"x-admin-key": settings.admin_api_key}
AGENT = {"x-api-key": settings.api_key}


def test_agent_key_cannot_use_admin(client):
    r = client.post("/admin/fines", json={"plate": "B11111", "amount_aed": 100, "reason": "Test"},
                    headers={"x-admin-key": settings.api_key})
    assert r.status_code == 401


def test_create_fine_then_agent_sees_it(client):
    r = client.post("/admin/fines", json={"plate": "b 11111", "amount_aed": 300, "reason": "Overstay"},
                    headers=ADMIN)
    assert r.status_code == 201
    fine = r.json()
    assert fine["plate"] == "B11111" and fine["fine_id"].startswith("F-") and fine["status"] == "unpaid"

    seen = client.get("/fines/B11111", headers=AGENT).json()
    assert [f["fine_id"] for f in seen] == [fine["fine_id"]]


def test_duplicate_fine_id_rejected(client):
    body = {"plate": "C22222", "amount_aed": 100, "reason": "Test", "fine_id": "F-3001"}
    assert client.post("/admin/fines", json=body, headers=ADMIN).status_code == 201
    assert client.post("/admin/fines", json=body, headers=ADMIN).status_code == 409


def test_invalid_input_rejected(client):
    assert client.post("/admin/fines", json={"plate": "XYZ", "amount_aed": 100, "reason": "Test"},
                       headers=ADMIN).status_code == 422
    assert client.post("/admin/fines", json={"plate": "A1", "amount_aed": -5, "reason": "Test"},
                       headers=ADMIN).status_code == 422


def test_list_filters_by_plate_and_status(client):
    rows = client.get("/admin/fines", params={"plate": "A12345", "status": "unpaid"}, headers=ADMIN).json()
    assert sorted(f["fine_id"] for f in rows) == ["F-1001", "F-1002"]


def test_delete_only_without_payments(client):
    client.post("/payments", json={"fine_id": "F-1001"}, headers=AGENT)          # F-1001 now has a payment
    assert client.delete("/admin/fines/F-1001", headers=ADMIN).status_code == 409
    assert client.delete("/admin/fines/F-1002", headers=ADMIN).status_code == 204
    assert client.delete("/admin/fines/F-1002", headers=ADMIN).status_code == 404
