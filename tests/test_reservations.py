import threading

from tests.conftest import auth_headers, create_user


BASE_START = "2025-09-01T09:00:00+00:00"
BASE_END = "2025-09-01T11:00:00+00:00"


def make_user(client, email="u@u.com"):
    user = create_user(client, email=email)
    headers = auth_headers(client, email)
    return user, headers


def make_room(client, admin_headers, name="Sala A"):
    return client.post(
        "/rooms",
        json={"name": name, "location": "Bloco A", "capacity": 10},
        headers=admin_headers,
    ).json()


def reservation_payload(room_id, starts_at=BASE_START, ends_at=BASE_END):
    return {
        "room_id": room_id,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "purpose": "Reuniao de equipe",
    }


def test_create_reservation_success(client, admin_headers):
    user, user_headers = make_user(client)
    room = make_room(client, admin_headers)
    r = client.post("/reservations", json=reservation_payload(room["id"]), headers=user_headers)
    assert r.status_code == 201
    assert r.json()["user_id"] == user["id"]
    assert r.json()["status"] == "pending"


def test_create_reservation_requires_auth(client, admin_headers):
    room = make_room(client, admin_headers)
    r = client.post("/reservations", json=reservation_payload(room["id"]))
    assert r.status_code == 403


def test_reservation_conflict_full_overlap(client, admin_headers):
    _, user_headers = make_user(client)
    room = make_room(client, admin_headers)
    payload = reservation_payload(room["id"])
    client.post("/reservations", json=payload, headers=user_headers)
    r = client.post("/reservations", json=payload, headers=user_headers)
    assert r.status_code == 409


def test_reservation_conflict_starts_inside(client, admin_headers):
    _, user_headers = make_user(client)
    room = make_room(client, admin_headers)
    client.post(
        "/reservations",
        json=reservation_payload(room["id"]),
        headers=user_headers,
    )
    r = client.post(
        "/reservations",
        json=reservation_payload(
            room["id"],
            starts_at="2025-09-01T10:00:00+00:00",
            ends_at="2025-09-01T12:00:00+00:00",
        ),
        headers=user_headers,
    )
    assert r.status_code == 409


def test_different_rooms_no_conflict(client, admin_headers):
    _, user_headers = make_user(client)
    room1 = make_room(client, admin_headers, name="Sala A")
    room2 = make_room(client, admin_headers, name="Sala B")
    client.post("/reservations", json=reservation_payload(room1["id"]), headers=user_headers)
    r = client.post("/reservations", json=reservation_payload(room2["id"]), headers=user_headers)
    assert r.status_code == 201


def test_reservation_inactive_room(client, admin_headers):
    _, user_headers = make_user(client)
    room = make_room(client, admin_headers)
    client.patch(f"/rooms/{room['id']}", json={"is_active": False}, headers=admin_headers)
    r = client.post("/reservations", json=reservation_payload(room["id"]), headers=user_headers)
    assert r.status_code == 400


def test_reservation_user_not_found_for_admin(client, admin_headers):
    room = make_room(client, admin_headers)
    payload = reservation_payload(room["id"])
    payload["user_id"] = 9999
    r = client.post("/reservations", json=payload, headers=admin_headers)
    assert r.status_code == 404


def test_user_cannot_create_reservation_for_another_user(client, admin_headers):
    user, user_headers = make_user(client, "u1@x.com")
    other, _ = make_user(client, "u2@x.com")
    room = make_room(client, admin_headers)
    payload = reservation_payload(room["id"])
    payload["user_id"] = other["id"]
    r = client.post("/reservations", json=payload, headers=user_headers)
    assert user["id"] != other["id"]
    assert r.status_code == 403


def test_reservation_invalid_time_range(client, admin_headers):
    _, user_headers = make_user(client)
    room = make_room(client, admin_headers)
    r = client.post(
        "/reservations",
        json=reservation_payload(
            room["id"],
            starts_at="2025-09-01T11:00:00+00:00",
            ends_at="2025-09-01T09:00:00+00:00",
        ),
        headers=user_headers,
    )
    assert r.status_code == 422


def test_cancel_reservation(client, admin_headers):
    _, user_headers = make_user(client)
    room = make_room(client, admin_headers)
    res = client.post(
        "/reservations",
        json=reservation_payload(room["id"]),
        headers=user_headers,
    ).json()
    r = client.patch(f"/reservations/{res['id']}/cancel", headers=user_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "canceled"


def test_canceled_reservation_frees_slot(client, admin_headers):
    _, user_headers = make_user(client)
    room = make_room(client, admin_headers)
    res = client.post(
        "/reservations",
        json=reservation_payload(room["id"]),
        headers=user_headers,
    ).json()
    client.patch(f"/reservations/{res['id']}/cancel", headers=user_headers)
    r = client.post("/reservations", json=reservation_payload(room["id"]), headers=user_headers)
    assert r.status_code == 201


def test_admin_can_approve_reservation(client, admin_headers):
    _, user_headers = make_user(client)
    room = make_room(client, admin_headers)
    res = client.post(
        "/reservations",
        json=reservation_payload(room["id"]),
        headers=user_headers,
    ).json()
    r = client.patch(f"/reservations/{res['id']}/approve", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "approved"


def test_user_cannot_approve_reservation(client, admin_headers):
    _, user_headers = make_user(client)
    room = make_room(client, admin_headers)
    res = client.post(
        "/reservations",
        json=reservation_payload(room["id"]),
        headers=user_headers,
    ).json()
    r = client.patch(f"/reservations/{res['id']}/approve", headers=user_headers)
    assert r.status_code == 403


def test_admin_can_reject_reservation(client, admin_headers):
    _, user_headers = make_user(client)
    room = make_room(client, admin_headers)
    res = client.post(
        "/reservations",
        json=reservation_payload(room["id"]),
        headers=user_headers,
    ).json()
    r = client.patch(f"/reservations/{res['id']}/reject", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_list_reservations_by_user(client, admin_headers):
    u1, h1 = make_user(client, "u1@x.com")
    _, h2 = make_user(client, "u2@x.com")
    room1 = make_room(client, admin_headers, name="Sala 1")
    room2 = make_room(client, admin_headers, name="Sala 2")
    client.post("/reservations", json=reservation_payload(room1["id"]), headers=h1)
    client.post("/reservations", json=reservation_payload(room2["id"]), headers=h2)
    r = client.get(f"/reservations?user_id={u1['id']}", headers=admin_headers)
    assert r.status_code == 200
    assert all(res["user_id"] == u1["id"] for res in r.json())


def test_regular_user_lists_only_own_reservations(client, admin_headers):
    u1, h1 = make_user(client, "u1@x.com")
    _, h2 = make_user(client, "u2@x.com")
    room1 = make_room(client, admin_headers, name="Sala 1")
    room2 = make_room(client, admin_headers, name="Sala 2")
    client.post("/reservations", json=reservation_payload(room1["id"]), headers=h1)
    client.post("/reservations", json=reservation_payload(room2["id"]), headers=h2)
    r = client.get("/reservations", headers=h1)
    assert r.status_code == 200
    assert all(res["user_id"] == u1["id"] for res in r.json())


def test_concurrent_booking_no_double(client, admin_headers):
    _, user_headers = make_user(client)
    room = make_room(client, admin_headers)
    results = []
    payload = reservation_payload(room["id"])

    def book():
        r = client.post("/reservations", json=payload, headers=user_headers)
        results.append(r.status_code)

    t1 = threading.Thread(target=book)
    t2 = threading.Thread(target=book)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results.count(201) == 1
    assert results.count(409) == 1
