"""Tests for authentication and user management APIs."""

import pytest


@pytest.fixture
def user_data():
    return {"email": "test@example.com", "password": "securepass123", "nickname": "tester"}


# --- Security utils ---


def test_password_hashing():
    from app.core.security import hash_password, verify_password

    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed)
    assert not verify_password("wrongpassword", hashed)


def test_jwt_tokens():
    from app.core.security import create_access_token, create_refresh_token, decode_token

    access = create_access_token("user-123")
    payload = decode_token(access)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"

    refresh = create_refresh_token("user-456")
    payload = decode_token(refresh)
    assert payload is not None
    assert payload["sub"] == "user-456"
    assert payload["type"] == "refresh"


def test_decode_invalid_token():
    from app.core.security import decode_token

    assert decode_token("invalid.token.here") is None
    assert decode_token("") is None


# --- Auth API ---


async def test_register(client, user_data):
    resp = await client.post("/api/v1/auth/register", json=user_data)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == user_data["email"]
    assert data["nickname"] == user_data["nickname"]
    assert "id" in data


async def test_register_duplicate_email(client, user_data):
    await client.post("/api/v1/auth/register", json=user_data)
    resp = await client.post("/api/v1/auth/register", json=user_data)
    assert resp.status_code == 409


async def test_register_weak_password(client):
    resp = await client.post("/api/v1/auth/register", json={"email": "a@b.com", "password": "short"})
    assert resp.status_code == 422


async def test_login(client, user_data):
    await client.post("/api/v1/auth/register", json=user_data)
    resp = await client.post("/api/v1/auth/login", json={"email": user_data["email"], "password": user_data["password"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client, user_data):
    await client.post("/api/v1/auth/register", json=user_data)
    resp = await client.post("/api/v1/auth/login", json={"email": user_data["email"], "password": "wrongpass123"})
    assert resp.status_code == 401


async def test_login_nonexistent_user(client):
    resp = await client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever123"})
    assert resp.status_code == 401


async def test_refresh_token(client, user_data):
    await client.post("/api/v1/auth/register", json=user_data)
    login_resp = await client.post("/api/v1/auth/login", json={"email": user_data["email"], "password": user_data["password"]})
    refresh_token = login_resp.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_with_access_token_fails(client, user_data):
    await client.post("/api/v1/auth/register", json=user_data)
    login_resp = await client.post("/api/v1/auth/login", json={"email": user_data["email"], "password": user_data["password"]})
    access_token = login_resp.json()["access_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


# --- User profile ---


async def test_get_me(client, user_data):
    await client.post("/api/v1/auth/register", json=user_data)
    login_resp = await client.post("/api/v1/auth/login", json={"email": user_data["email"], "password": user_data["password"]})
    token = login_resp.json()["access_token"]

    resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == user_data["email"]


async def test_get_me_unauthorized(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


async def test_update_me(client, user_data):
    await client.post("/api/v1/auth/register", json=user_data)
    login_resp = await client.post("/api/v1/auth/login", json={"email": user_data["email"], "password": user_data["password"]})
    token = login_resp.json()["access_token"]

    resp = await client.patch("/api/v1/users/me", json={"nickname": "new_nick"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["nickname"] == "new_nick"


async def test_change_password(client, user_data):
    await client.post("/api/v1/auth/register", json=user_data)
    login_resp = await client.post("/api/v1/auth/login", json={"email": user_data["email"], "password": user_data["password"]})
    token = login_resp.json()["access_token"]

    resp = await client.post(
        "/api/v1/users/me/password",
        json={"old_password": user_data["password"], "new_password": "newpass12345"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204

    # Verify new password works
    resp = await client.post("/api/v1/auth/login", json={"email": user_data["email"], "password": "newpass12345"})
    assert resp.status_code == 200


async def test_change_password_wrong_old(client, user_data):
    await client.post("/api/v1/auth/register", json=user_data)
    login_resp = await client.post("/api/v1/auth/login", json={"email": user_data["email"], "password": user_data["password"]})
    token = login_resp.json()["access_token"]

    resp = await client.post(
        "/api/v1/users/me/password",
        json={"old_password": "wrongold123", "new_password": "newpass12345"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
