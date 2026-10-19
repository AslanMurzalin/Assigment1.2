import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.repositories.in_memory import InMemoryUserRepository, InMemoryLinkRepository
from app.api.dependencies import get_user_repository, get_link_repository

user_repo = InMemoryUserRepository()
link_repo = InMemoryLinkRepository()

@pytest.fixture(autouse=True)
def setup_in_memory():
    app.dependency_overrides[get_user_repository] = lambda: user_repo
    app.dependency_overrides[get_link_repository] = lambda: link_repo
    user_repo._users.clear()
    user_repo._emails.clear()
    link_repo._links.clear()
    yield
    app.dependency_overrides.clear()

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_auth_flow():
    # 1. Signup
    signup_resp = client.post(
        "/api/v1/auth/signup",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert signup_resp.status_code == 201
    user_data = signup_resp.json()
    assert user_data["email"] == "alice@example.com"
    assert "id" in user_data

    # 2. Duplicate signup should return 409 Conflict
    dup_resp = client.post(
        "/api/v1/auth/signup",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert dup_resp.status_code == 409

    # 3. Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    token = token_data["access_token"]

    # 4. Get profile /me
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "alice@example.com"

    # 5. Invalid token
    bad_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert bad_resp.status_code == 401

def test_links_crud_and_search():
    # Register and login Alice
    client.post("/api/v1/auth/signup", json={"email": "alice@example.com", "password": "password123"})
    login_resp = client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "password123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create YouTube link
    yt_resp = client.post(
        "/api/v1/links",
        headers=headers,
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "user_notes": "Great classic 80s song",
            "tags": ["music", "classics", "80s"],
        },
    )
    assert yt_resp.status_code == 201
    yt_link = yt_resp.json()
    assert yt_link["site_type"] == "youtube"
    assert "music" in yt_link["tags"]
    link_id = yt_link["id"]

    # Create Generic link
    gen_resp = client.post(
        "/api/v1/links",
        headers=headers,
        json={
            "url": "https://fastapi.tiangolo.com",
            "user_notes": "FastAPI official documentation",
            "tags": ["python", "backend"],
        },
    )
    assert gen_resp.status_code == 201
    assert gen_resp.json()["site_type"] == "generic"

    # List links
    list_resp = client.get("/api/v1/links", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2

    # Search with query
    search_resp = client.get("/api/v1/links?q=classic", headers=headers)
    assert search_resp.status_code == 200
    assert len(search_resp.json()) == 1
    assert search_resp.json()[0]["id"] == link_id

    # Filter with tag
    tag_resp = client.get("/api/v1/links?tag=backend", headers=headers)
    assert tag_resp.status_code == 200
    assert len(tag_resp.json()) == 1
    assert tag_resp.json()[0]["site_type"] == "generic"

    # Get single link
    get_resp = client.get(f"/api/v1/links/{link_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == link_id

    # Patch notes and tags
    patch_resp = client.patch(
        f"/api/v1/links/{link_id}",
        headers=headers,
        json={"user_notes": "Updated note", "tags": ["updated_tag"]},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["user_notes"] == "Updated note"
    assert "updated_tag" in patch_resp.json()["tags"]

    # Delete link
    del_resp = client.delete(f"/api/v1/links/{link_id}", headers=headers)
    assert del_resp.status_code == 204

    # Confirm deleted
    get_del = client.get(f"/api/v1/links/{link_id}", headers=headers)
    assert get_del.status_code == 404

def test_user_data_isolation():
    # User 1 (Alice)
    client.post("/api/v1/auth/signup", json={"email": "alice@example.com", "password": "password123"})
    token_alice = client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "password123"}).json()["access_token"]

    # User 2 (Bob)
    client.post("/api/v1/auth/signup", json={"email": "bob@example.com", "password": "password123"})
    token_bob = client.post("/api/v1/auth/login", json={"email": "bob@example.com", "password": "password123"}).json()["access_token"]

    # Alice creates a link
    created = client.post(
        "/api/v1/links",
        headers={"Authorization": f"Bearer {token_alice}"},
        json={"url": "https://example.com/secret", "user_notes": "Alice's secret"},
    ).json()
    alice_link_id = created["id"]

    # Bob lists links -> should be empty
    bob_list = client.get(
        "/api/v1/links",
        headers={"Authorization": f"Bearer {token_bob}"},
    ).json()
    assert len(bob_list) == 0

    # Bob tries to access Alice's link -> should return 404
    bob_get = client.get(
        f"/api/v1/links/{alice_link_id}",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert bob_get.status_code == 404

    # Bob tries to delete Alice's link -> should return 404
    bob_del = client.delete(
        f"/api/v1/links/{alice_link_id}",
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert bob_del.status_code == 404

def test_download_validation():
    # Alice creates generic link
    client.post("/api/v1/auth/signup", json={"email": "alice@example.com", "password": "password123"})
    token = client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    gen_link = client.post(
        "/api/v1/links",
        headers=headers,
        json={"url": "https://example.com", "user_notes": "Not a video"},
    ).json()

    # Attempting to download generic link should fail with 400 Bad Request
    dl_resp = client.get(f"/api/v1/links/{gen_link['id']}/download", headers=headers)
    assert dl_resp.status_code == 400
    assert "YouTube" in dl_resp.json()["detail"]
