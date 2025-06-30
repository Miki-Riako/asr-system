# File: test/test_auth.py

import pytest
from fastapi.testclient import TestClient
from asr_system_backend.app.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def test_user():
    return {
        "username": "testuser",
        "password": "testpassword123"
    }

def test_register_success(test_user):
    resp = client.post("/auth/register", json=test_user)
    assert resp.status_code == 200 or resp.status_code == 409  # 已注册也算通过
    data = resp.json()
    if resp.status_code == 200:
        assert data["username"] == test_user["username"]
        assert "user_id" in data
        assert "created_at" in data

def test_register_duplicate(test_user):
    resp = client.post("/auth/register", json=test_user)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "用户名已存在"

def test_login_success(test_user):
    resp = client.post("/auth/login", json=test_user)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == test_user["username"]
    assert "user_id" in data
    assert "created_at" in data

def test_login_wrong_password(test_user):
    resp = client.post("/auth/login", json={"username": test_user["username"], "password": "wrongpass"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "用户名或密码错误"

def test_login_nonexistent_user():
    resp = client.post("/auth/login", json={"username": "nouser", "password": "any"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "用户名或密码错误" 