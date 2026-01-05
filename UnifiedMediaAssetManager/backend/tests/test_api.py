import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_dev_token():
    r = client.post("/auth/dev-token")
    assert r.status_code == 200
    return r.json()["token"]


def test_user_and_universe_lifecycle():
    token = get_dev_token()
    headers = {"Authorization": f"Bearer {token}"}

    # create user
    r = client.post("/users", params={"username": "dev", "display_name": "Dev User"})
    assert r.status_code == 201
    user = r.json()
    assert user["username"] == "dev"

    # create universe (omit id so server generates one)
    r = client.post("/universes", headers=headers, json={"name":"Test Universe","description":"desc","elements":[]})
    assert r.status_code == 201
    uni = r.json()
    assert uni["name"] == "Test Universe"

    # list universes
    r = client.get("/universes")
    assert r.status_code == 200
    items = r.json()
    assert any(u["name"] == "Test Universe" for u in items)


from pathlib import Path
from app import auth


def test_media_upload_and_serving():
    token = get_dev_token()
    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("test.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", "image/png")}

    r = client.post("/media/upload", headers=headers, files=files)
    assert r.status_code == 200
    data = r.json()
    assert "url" in data
    url = data["url"]
    assert url.startswith("/media/images/")

    filename = url.split("/")[-1]
    media_dir = Path(__file__).resolve().parent.parent / "media" / "images"
    saved_file = media_dir / filename
    assert saved_file.exists()

    # Verify StaticFiles serves the uploaded file
    r2 = client.get(url)
    assert r2.status_code == 200
    assert r2.content


def test_permission_enforcement_for_elements_and_components():
    owner_token = auth.create_access_token(subject="owner", roles=["user"])
    other_token = auth.create_access_token(subject="other", roles=["user"])
    admin_token = auth.create_access_token(subject="admin", roles=["admin"])

    headers_owner = {"Authorization": f"Bearer {owner_token}"}
    headers_other = {"Authorization": f"Bearer {other_token}"}
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    # create universe as owner
    r = client.post("/universes", headers=headers_owner, json={"name":"Owner Uni","description":"desc","elements":[]})
    assert r.status_code == 201
    uni = r.json()
    uni_id = uni["id"]

    # other cannot add element
    r = client.post(f"/universes/{uni_id}/elements", headers=headers_other, json={"name":"E1"})
    assert r.status_code == 403

    # owner can add element
    r = client.post(f"/universes/{uni_id}/elements", headers=headers_owner, json={"name":"E1"})
    assert r.status_code == 201
    el = r.json()
    el_id = el["id"]

    # other cannot add component
    r = client.post(f"/universes/{uni_id}/elements/{el_id}/components", headers=headers_other, json={"type":"TextComponent","data":{"field":"Description","content":"x"}})
    assert r.status_code == 403

    # admin can add component
    r = client.post(f"/universes/{uni_id}/elements/{el_id}/components", headers=headers_admin, json={"type":"TextComponent","data":{"field":"Description","content":"y"}})
    assert r.status_code == 201
