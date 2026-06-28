def test_create_user_success(client):
    response = client.post("/users", json={
        "name": "Ana Lima",
        "email": "ana@email.com"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "ana@email.com"
    assert "id" in data

def test_create_user_duplicate_email(client):
    client.post("/users", json={"name": "Ana", "email": "ana@email.com"})
    response = client.post("/users", json={"name": "Ana2", "email": "ana@email.com"})
    assert response.status_code == 409

def test_create_user_invalid_email(client):
    response = client.post("/users", json={"name": "Ana", "email": "nao_e_email"})
    assert response.status_code == 422

def test_list_users(client):
    client.post("/users", json={"name": "A", "email": "a@a.com"})
    client.post("/users", json={"name": "B", "email": "b@b.com"})
    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_user_by_id(client):
    created = client.post("/users", json={"name": "C", "email": "c@c.com"}).json()
    response = client.get(f"/users/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]

def test_get_user_not_found(client):
    response = client.get("/users/9999")
    assert response.status_code == 404
