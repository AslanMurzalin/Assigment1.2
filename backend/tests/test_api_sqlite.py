import pytest
import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.db.session import Base, get_db
from app.models.tag import TagModel, link_tags
from app.models.link import LinkModel
from app.models.user import UserModel

# Test SQLite in-memory database
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(autouse=True)
def setup_test_db():
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

client = TestClient(app)

def test_sqlite_auth_flow():
    # Signup
    signup_resp = client.post(
        "/api/v1/auth/signup",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert signup_resp.status_code == 201
    user_id = signup_resp.json()["id"]

    # Verify user in database
    db = TestingSessionLocal()
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    assert db_user is not None
    assert db_user.email == "alice@example.com"
    db.close()

    # Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Get /me
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "alice@example.com"

def test_sqlite_mn_tags_and_deduplication():
    # Register & Login
    client.post("/api/v1/auth/signup", json={"email": "alice@example.com", "password": "password123"})
    token = client.post("/api/v1/auth/login", json={"email": "alice@example.com", "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create Link 1 with tags: "python", "fastapi"
    resp1 = client.post(
        "/api/v1/links",
        headers=headers,
        json={"url": "https://fastapi.tiangolo.com", "tags": ["python", "fastapi"], "user_notes": "Modern framework"},
    )
    assert resp1.status_code == 201
    link1 = resp1.json()

    # Create Link 2 with tags: "python", "tutorial" (reuses "python" tag!)
    resp2 = client.post(
        "/api/v1/links",
        headers=headers,
        json={"url": "https://docs.python.org", "tags": ["python", "tutorial"], "user_notes": "Official guide"},
    )
    assert resp2.status_code == 201
    link2 = resp2.json()

    # Verify relational tables in database:
    db = TestingSessionLocal()
    # 1. Tags table must contain exactly 3 unique tags: "python", "fastapi", "tutorial"
    all_tags = db.query(TagModel).all()
    assert len(all_tags) == 3
    tag_names = {t.name for t in all_tags}
    assert tag_names == {"python", "fastapi", "tutorial"}

    # 2. Junction table link_tags must contain 4 associations
    junction_rows = db.execute(link_tags.select()).fetchall()
    assert len(junction_rows) == 4
    db.close()

    # Test filtering by shared tag "python" -> returns both links
    filter_resp = client.get("/api/v1/links?tag=python", headers=headers)
    assert filter_resp.status_code == 200
    assert len(filter_resp.json()) == 2

    # Test filtering by specific tag "fastapi" -> returns only link 1
    filter_fastapi = client.get("/api/v1/links?tag=fastapi", headers=headers)
    assert filter_fastapi.status_code == 200
    assert len(filter_fastapi.json()) == 1
    assert filter_fastapi.json()[0]["id"] == link1["id"]

    # Test search with ilike
    search_resp = client.get("/api/v1/links?q=framework", headers=headers)
    assert search_resp.status_code == 200
    assert len(search_resp.json()) == 1
    assert search_resp.json()[0]["id"] == link1["id"]

    # Test updating tags on Link 1
    patch_resp = client.patch(
        f"/api/v1/links/{link1['id']}",
        headers=headers,
        json={"tags": ["python", "backend"]},
    )
    assert patch_resp.status_code == 200
    assert set(patch_resp.json()["tags"]) == {"python", "backend"}

    # Test deleting Link 1
    del_resp = client.delete(f"/api/v1/links/{link1['id']}", headers=headers)
    assert del_resp.status_code == 204

    # Verify Link 1 deleted from db and junction table cleaned up
    db = TestingSessionLocal()
    assert db.query(LinkModel).filter(LinkModel.id == link1["id"]).first() is None
    link1_junctions = db.execute(link_tags.select().where(link_tags.c.link_id == link1["id"])).fetchall()
    assert len(link1_junctions) == 0
    db.close()
