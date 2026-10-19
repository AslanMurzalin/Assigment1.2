import pytest
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.db.session import engine, Base, SessionLocal
from app.models.user import UserModel
from app.models.link import LinkModel
from app.models.tag import TagModel, link_tags

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def init_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup integration test records
    db = SessionLocal()
    try:
        user = db.query(UserModel).filter(UserModel.email == "e2e_user@example.com").first()
        if user:
            # Delete links belonging to this user
            links = db.query(LinkModel).filter(LinkModel.user_id == user.id).all()
            for l in links:
                db.delete(l)
            db.delete(user)
            db.commit()
    finally:
        db.close()

def test_e2e_full_lifecycle():
    # 1. Health check
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "ok"

    # 2. Signup
    signup_resp = client.post(
        "/api/v1/auth/signup",
        json={"email": "e2e_user@example.com", "password": "Password123!"},
    )
    assert signup_resp.status_code == 201
    user_id = signup_resp.json()["id"]

    # 3. Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "e2e_user@example.com", "password": "Password123!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Verify /me
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["id"] == user_id
    assert me_resp.json()["email"] == "e2e_user@example.com"

    # 5. Create Link 1: YouTube link with tags
    yt_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    link1_resp = client.post(
        "/api/v1/links",
        headers=headers,
        json={
            "url": yt_url,
            "user_notes": "Favorite 80s hit for testing",
            "tags": ["music", "classics"],
        },
    )
    assert link1_resp.status_code == 201
    link1 = link1_resp.json()
    assert link1["site_type"] == "youtube"
    assert "Rick Astley" in link1["title"] or "dQw4w9WgXcQ" in link1["title"] or len(link1["title"]) > 0

    # 6. Create Link 2: Generic link with overlapping and new tags
    doc_url = "https://fastapi.tiangolo.com"
    link2_resp = client.post(
        "/api/v1/links",
        headers=headers,
        json={
            "url": doc_url,
            "user_notes": "FastAPI web framework",
            "tags": ["python", "backend", "classics"],
        },
    )
    assert link2_resp.status_code == 201
    link2 = link2_resp.json()
    assert link2["site_type"] == "generic"

    # 7. Relational Search & Tag Filter
    # Tag filter "classics" should return both links
    filter_classics = client.get("/api/v1/links?tag=classics", headers=headers)
    assert filter_classics.status_code == 200
    assert len(filter_classics.json()) == 2

    # Tag filter "backend" should return only link 2
    filter_backend = client.get("/api/v1/links?tag=backend", headers=headers)
    assert filter_backend.status_code == 200
    assert len(filter_backend.json()) == 1
    assert filter_backend.json()[0]["id"] == link2["id"]

    # Search query "Favorite" should return link 1
    search_fav = client.get("/api/v1/links?q=Favorite", headers=headers)
    assert search_fav.status_code == 200
    assert len(search_fav.json()) == 1
    assert search_fav.json()[0]["id"] == link1["id"]

    # 8. YouTube Download Endpoint check
    # Generic link download should be rejected with 400
    dl_fail = client.get(f"/api/v1/links/{link2['id']}/download", headers=headers)
    assert dl_fail.status_code == 400

    # 9. Link Update
    patch_resp = client.patch(
        f"/api/v1/links/{link1['id']}",
        headers=headers,
        json={"user_notes": "Updated Rickroll note", "tags": ["music", "pop"]},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["user_notes"] == "Updated Rickroll note"
    assert set(patch_resp.json()["tags"]) == {"music", "pop"}

    # 10. Link Delete
    del_resp = client.delete(f"/api/v1/links/{link1['id']}", headers=headers)
    assert del_resp.status_code == 204

    # Confirm Link 1 is gone
    get_del = client.get(f"/api/v1/links/{link1['id']}", headers=headers)
    assert get_del.status_code == 404
