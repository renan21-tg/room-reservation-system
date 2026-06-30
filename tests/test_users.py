from tests.conftest import auth_headers, create_user


def test_create_user_success(client):
    response = client.post("/users", json={
        "name": "Ana Lima",
        "email": "ana@email.com",
        "password": "secret123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "ana@email.com"
    assert data["role"] == "user"
    assert "id" in data

def test_create_user_duplicate_email(client):
    create_user(client, email="ana@email.com")
    response = client.post(
        "/users",
        json={"name": "Ana2", "email": "ana@email.com", "password": "secret123"},
    )
    assert response.status_code == 409

def test_create_user_invalid_email(client):
    response = client.post(
        "/users",
        json={"name": "Ana", "email": "nao_e_email", "password": "secret123"},
    )
    assert response.status_code == 422

def test_login_success(client):
    create_user(client, email="ana@email.com")
    response = client.post(
        "/auth/login",
        json={"email": "ana@email.com", "password": "secret123"},
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert "access_token" in response.json()

def test_list_users_requires_admin(client, user_headers):
    response = client.get("/users", headers=user_headers)
    assert response.status_code == 403

def test_list_users(client, admin_headers):
    create_user(client, email="a@a.com")
    create_user(client, email="b@b.com")
    response = client.get("/users", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()) == 3

def test_get_user_by_id(client):
    created = create_user(client, email="c@c.com")
    headers = auth_headers(client, "c@c.com")
    response = client.get(f"/users/{created['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]

def test_get_user_not_found(client, admin_headers):
    response = client.get("/users/9999", headers=admin_headers)
    assert response.status_code == 404

def test_only_first_user_can_be_admin(client):
    first = create_user(client, email="admin@email.com", role="admin")
    assert first["role"] == "admin"
    response = client.post(
        "/users",
        json={
            "name": "Other Admin",
            "email": "other-admin@email.com",
            "password": "secret123",
            "role": "admin",
        },
    )
    assert response.status_code == 403
