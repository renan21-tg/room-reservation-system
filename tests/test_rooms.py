def test_create_room_success(client, admin_headers):
    response = client.post("/rooms", json={
        "name": "Sala 101", "location": "Bloco A", "capacity": 20
    }, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["is_active"] is True

def test_create_room_requires_admin(client, user_headers):
    r = client.post(
        "/rooms",
        json={"name": "Sala 101", "location": "A", "capacity": 10},
        headers=user_headers,
    )
    assert r.status_code == 403

def test_create_room_duplicate_name(client, admin_headers):
    client.post(
        "/rooms",
        json={"name": "Sala 101", "location": "A", "capacity": 10},
        headers=admin_headers,
    )
    r = client.post(
        "/rooms",
        json={"name": "Sala 101", "location": "B", "capacity": 10},
        headers=admin_headers,
    )
    assert r.status_code == 409

def test_create_room_invalid_capacity(client, admin_headers):
    r = client.post(
        "/rooms",
        json={"name": "S", "location": "A", "capacity": 0},
        headers=admin_headers,
    )
    assert r.status_code == 422

def test_list_rooms_min_capacity(client, admin_headers):
    client.post("/rooms", json={"name": "P", "location": "A", "capacity": 5}, headers=admin_headers)
    client.post("/rooms", json={"name": "G", "location": "B", "capacity": 30}, headers=admin_headers)
    r = client.get("/rooms?min_capacity=10")
    assert r.status_code == 200
    rooms = r.json()
    assert all(room["capacity"] >= 10 for room in rooms)
    assert len(rooms) == 1

def test_deactivate_room(client, admin_headers):
    room = client.post(
        "/rooms",
        json={"name": "R", "location": "A", "capacity": 10},
        headers=admin_headers,
    ).json()
    r = client.patch(f"/rooms/{room['id']}", json={"is_active": False}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["is_active"] is False

def test_inactive_room_hidden_from_list(client, admin_headers):
    room = client.post(
        "/rooms",
        json={"name": "RR", "location": "A", "capacity": 10},
        headers=admin_headers,
    ).json()
    client.patch(f"/rooms/{room['id']}", json={"is_active": False}, headers=admin_headers)
    r = client.get("/rooms")
    ids = [rm["id"] for rm in r.json()]
    assert room["id"] not in ids
