import pytest
from datetime import datetime, timezone

def make_user(client, email="u@u.com"):
    return client.post("/users", json={"name": "User", "email": email}).json()

def make_room(client, name="Sala A"):
    return client.post("/rooms", json={
        "name": name, "location": "Bloco A", "capacity": 10
    }).json()

BASE_START = "2025-09-01T09:00:00+00:00"
BASE_END   = "2025-09-01T11:00:00+00:00"

def test_create_reservation_success(client):
    user = make_user(client)
    room = make_room(client)
    r = client.post("/reservations", json={
        "user_id": user["id"], "room_id": room["id"],
        "starts_at": BASE_START, "ends_at": BASE_END,
        "purpose": "Reuniao de equipe"
    })
    assert r.status_code == 201
    assert r.json()["status"] == "active"

def test_reservation_conflict_full_overlap(client):
    user = make_user(client)
    room = make_room(client)
    payload = {"user_id": user["id"], "room_id": room["id"],
               "starts_at": BASE_START, "ends_at": BASE_END, "purpose": "Reuniao"}
    client.post("/reservations", json=payload)
    r = client.post("/reservations", json=payload)
    assert r.status_code == 409

def test_reservation_conflict_starts_inside(client):
    user = make_user(client)
    room = make_room(client)
    client.post("/reservations", json={
        "user_id": user["id"], "room_id": room["id"],
        "starts_at": "2025-09-01T09:00:00+00:00",
        "ends_at": "2025-09-01T11:00:00+00:00",
        "purpose": "R1"
    })
    r = client.post("/reservations", json={
        "user_id": user["id"], "room_id": room["id"],
        "starts_at": "2025-09-01T10:00:00+00:00",
        "ends_at": "2025-09-01T12:00:00+00:00",
        "purpose": "R2"
    })
    assert r.status_code == 409

def test_different_rooms_no_conflict(client):
    user = make_user(client)
    room1 = make_room(client, name="Sala A")
    room2 = make_room(client, name="Sala B")
    client.post("/reservations", json={
        "user_id": user["id"], "room_id": room1["id"],
        "starts_at": BASE_START, "ends_at": BASE_END, "purpose": "R1"
    })
    r = client.post("/reservations", json={
        "user_id": user["id"], "room_id": room2["id"],
        "starts_at": BASE_START, "ends_at": BASE_END, "purpose": "R2"
    })
    assert r.status_code == 201

def test_reservation_inactive_room(client):
    user = make_user(client)
    room = make_room(client)
    client.patch(f"/rooms/{room['id']}", json={"is_active": False})
    r = client.post("/reservations", json={
        "user_id": user["id"], "room_id": room["id"],
        "starts_at": BASE_START, "ends_at": BASE_END, "purpose": "Teste"
    })
    assert r.status_code == 400

def test_reservation_user_not_found(client):
    room = make_room(client)
    r = client.post("/reservations", json={
        "user_id": 9999, "room_id": room["id"],
        "starts_at": BASE_START, "ends_at": BASE_END, "purpose": "Teste"
    })
    assert r.status_code == 404

def test_reservation_invalid_time_range(client):
    user = make_user(client)
    room = make_room(client)
    r = client.post("/reservations", json={
        "user_id": user["id"], "room_id": room["id"],
        "starts_at": "2025-09-01T11:00:00+00:00",
        "ends_at": "2025-09-01T09:00:00+00:00",
        "purpose": "Invalido"
    })
    assert r.status_code == 422

def test_cancel_reservation(client):
    user = make_user(client)
    room = make_room(client)
    res = client.post("/reservations", json={
        "user_id": user["id"], "room_id": room["id"],
        "starts_at": BASE_START, "ends_at": BASE_END, "purpose": "Reuniao"
    }).json()
    r = client.patch(f"/reservations/{res['id']}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "canceled"

def test_canceled_reservation_frees_slot(client):
    user = make_user(client)
    room = make_room(client)
    res = client.post("/reservations", json={
        "user_id": user["id"], "room_id": room["id"],
        "starts_at": BASE_START, "ends_at": BASE_END, "purpose": "R1"
    }).json()
    client.patch(f"/reservations/{res['id']}/cancel")
    r = client.post("/reservations", json={
        "user_id": user["id"], "room_id": room["id"],
        "starts_at": BASE_START, "ends_at": BASE_END, "purpose": "R2"
    })
    assert r.status_code == 201

def test_list_reservations_by_user(client):
    u1 = make_user(client, "u1@x.com")
    u2 = make_user(client, "u2@x.com")
    room = make_room(client)
    client.post("/reservations", json={
        "user_id": u1["id"], "room_id": room["id"],
        "starts_at": BASE_START, "ends_at": BASE_END, "purpose": "R1"
    })
    r = client.get(f"/reservations?user_id={u1['id']}")
    assert r.status_code == 200
    assert all(res["user_id"] == u1["id"] for res in r.json())
