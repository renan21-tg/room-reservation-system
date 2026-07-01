import threading

from tests.conftest import auth_headers, create_user
from app.services.no_show_service import cancel_no_shows


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

def test_recurrence_weekly_creates_parent(client, admin_headers):
    user, user_headers = make_user(client)
    room = make_room(client, admin_headers=admin_headers)
    r = client.post("/reservations", json={
        "user_id": user["id"],
        "room_id": room["id"],
        "starts_at": "2025-09-01T09:00:00+00:00",
        "ends_at": "2025-09-01T11:00:00+00:00",
        "purpose": "Reuniao semanal",
        "recurrence_rule": "weekly",
        "recurrence_end_date": "2025-09-29T23:59:59+00:00",
    }, headers=user_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["recurrence_rule"] == "weekly"
    assert data["parent_id"] is None 


def test_recurrence_conflict_aborts_entire_batch(client, admin_headers):
    user, user_headers = make_user(client)
    room = make_room(client, admin_headers=admin_headers)

    client.post("/reservations", json={
        "user_id": user["id"],
        "room_id": room["id"],
        "starts_at": "2025-09-08T09:00:00+00:00",
        "ends_at": "2025-09-08T11:00:00+00:00",
        "purpose": "Conflito intencional",
    }, headers=user_headers)

    r = client.post("/reservations", json={
        "user_id": user["id"],
        "room_id": room["id"],
        "starts_at": "2025-09-01T09:00:00+00:00",
        "ends_at": "2025-09-01T11:00:00+00:00",
        "purpose": "Serie semanal",
        "recurrence_rule": "weekly",
        "recurrence_end_date": "2025-09-29T23:59:59+00:00",
    }, headers=user_headers)
    assert r.status_code == 409


def test_recurrence_none_is_default(client, admin_headers):
    user, user_headers = make_user(client)
    room = make_room(client, admin_headers=admin_headers)
    r = client.post("/reservations", json={
        "user_id": user["id"],
        "room_id": room["id"],
        "starts_at": BASE_START,
        "ends_at": BASE_END,
        "purpose": "Simples",
    }, headers=user_headers)
    assert r.status_code == 201
    assert r.json()["recurrence_rule"] == "none"


def test_recurrence_requires_end_date(client, admin_headers):
    user, user_headers = make_user(client)
    room = make_room(client, admin_headers=admin_headers)
    r = client.post("/reservations", json={
        "user_id": user["id"],
        "room_id": room["id"],
        "starts_at": BASE_START,
        "ends_at": BASE_END,
        "purpose": "Sem data fim",
        "recurrence_rule": "daily",
    }, headers=user_headers)
    assert r.status_code == 422


def test_recurrence_daily_does_not_conflict_different_room(client, admin_headers):
    user1, user1_headers = make_user(client, "u1@test.com")
    user2, user2_headers = make_user(client, "u2@test.com")
    room_a = make_room(client, admin_headers=admin_headers, name="Sala X")
    room_b = make_room(client, admin_headers=admin_headers, name="Sala Y")
    client.post("/reservations", json={
        "user_id": user1["id"],
        "room_id": room_a["id"],
        "starts_at": "2025-10-01T10:00:00+00:00",
        "ends_at": "2025-10-01T11:00:00+00:00",
        "purpose": "Serie A",
        "recurrence_rule": "daily",
        "recurrence_end_date": "2025-10-03T23:59:59+00:00",
    }, headers=user1_headers)

    r = client.post("/reservations", json={
        "user_id": user2["id"],
        "room_id": room_b["id"],
        "starts_at": "2025-10-02T10:00:00+00:00",
        "ends_at": "2025-10-02T11:00:00+00:00",
        "purpose": "Sala B sem conflito",
    }, headers=user2_headers)
    assert r.status_code == 201

def test_checkin_registers_timestamp(client, db, admin_headers):
    user, user_headers = make_user(client)
    room = make_room(client, admin_headers)
    res = client.post("/reservations", json={
        "room_id": room["id"],
        "starts_at": BASE_START, "ends_at": BASE_END, "purpose": "Reuniao"
    }, headers=user_headers).json()

    client.patch(f"/reservations/{res['id']}/approve", headers=admin_headers)

    r = client.patch(f"/reservations/{res['id']}/checkin", headers=user_headers)
    assert r.status_code == 200
    assert r.json()["checked_in_at"] is not None


def test_no_show_cancels_approved_without_checkin(db):
    from datetime import datetime, timedelta, timezone
    from app.models.reservation import Reservation, ReservationStatus
    from app.models.room import Room
    from app.models.user import User
    from app.core.security import hash_password

    user = User(name="U", email="u@test.com", password_hash=hash_password("123"), role="user")
    db.add(user)
    room = Room(name="Sala T", location="Bloco T", capacity=10)
    db.add(room)
    db.flush()

    past_start = datetime.now(timezone.utc) - timedelta(minutes=20)
    reservation = Reservation(
        user_id=user.id,
        room_id=room.id,
        starts_at=past_start,
        ends_at=past_start + timedelta(hours=1),
        purpose="No show",
        status=ReservationStatus.APPROVED.value,
        recurrence_rule="none",
    )
    db.add(reservation)
    db.commit()

    canceled_count = cancel_no_shows(db=db)

    assert canceled_count == 1
    db.refresh(reservation)
    assert reservation.status == ReservationStatus.CANCELED.value


def test_no_show_does_not_cancel_with_checkin(db):
    from datetime import datetime, timedelta, timezone
    from app.models.reservation import Reservation, ReservationStatus
    from app.models.room import Room
    from app.models.user import User
    from app.core.security import hash_password

    user = User(name="V", email="v@test.com", password_hash=hash_password("123"), role="user")
    db.add(user)
    room = Room(name="Sala V", location="Bloco V", capacity=10)
    db.add(room)
    db.flush()

    past_start = datetime.now(timezone.utc) - timedelta(minutes=20)
    reservation = Reservation(
        user_id=user.id,
        room_id=room.id,
        starts_at=past_start,
        ends_at=past_start + timedelta(hours=1),
        purpose="Com presenca",
        status=ReservationStatus.APPROVED.value,
        recurrence_rule="none",
        checked_in_at=past_start + timedelta(minutes=5),
    )
    db.add(reservation)
    db.commit()

    canceled_count = cancel_no_shows(db=db)

    assert canceled_count == 0
    db.refresh(reservation)
    assert reservation.status == ReservationStatus.APPROVED.value


def test_no_show_does_not_cancel_pending(db):
    from datetime import datetime, timedelta, timezone
    from app.models.reservation import Reservation, ReservationStatus
    from app.models.room import Room
    from app.models.user import User
    from app.core.security import hash_password

    user = User(name="W", email="w@test.com", password_hash=hash_password("123"), role="user")
    db.add(user)
    room = Room(name="Sala W", location="Bloco W", capacity=10)
    db.add(room)
    db.flush()

    past_start = datetime.now(timezone.utc) - timedelta(minutes=20)
    reservation = Reservation(
        user_id=user.id,
        room_id=room.id,
        starts_at=past_start,
        ends_at=past_start + timedelta(hours=1),
        purpose="Pendente",
        status=ReservationStatus.PENDING.value,
        recurrence_rule="none",
    )
    db.add(reservation)
    db.commit()

    canceled_count = cancel_no_shows(db=db)

    assert canceled_count == 0
    db.refresh(reservation)
    assert reservation.status == ReservationStatus.PENDING.value


def test_checkin_on_pending_reservation_returns_400(client, admin_headers):
    user, user_headers = make_user(client)
    room = make_room(client, admin_headers)
    res = client.post("/reservations", json={
        "room_id": room["id"],
        "starts_at": BASE_START, "ends_at": BASE_END, "purpose": "Pendente"
    }, headers=user_headers).json()

    r = client.patch(f"/reservations/{res['id']}/checkin", headers=user_headers)
    assert r.status_code == 400

def test_user_cannot_exceed_max_reservation_duration(client, admin_headers):
    _, user_headers = make_user(client)
    room = make_room(client, admin_headers)
    r = client.post("/reservations", json={
        "room_id": room["id"],
        "starts_at": "2025-11-01T08:00:00+00:00",
        "ends_at":   "2025-11-01T11:00:00+00:00", 
        "purpose": "Reuniao longa",
    }, headers=user_headers)
    assert r.status_code == 422
    assert "limit" in r.json()["detail"].lower()


def test_user_cannot_exceed_max_active_reservations(client, admin_headers):
    _, user_headers = make_user(client)
    room1 = make_room(client, admin_headers, name="Limite A")
    room2 = make_room(client, admin_headers, name="Limite B")
    room3 = make_room(client, admin_headers, name="Limite C")

    client.post("/reservations", json={
        "room_id": room1["id"],
        "starts_at": "2025-11-01T09:00:00+00:00",
        "ends_at":   "2025-11-01T10:00:00+00:00",
        "purpose": "Reserva 1",
    }, headers=user_headers)
    client.post("/reservations", json={
        "room_id": room2["id"],
        "starts_at": "2025-11-02T09:00:00+00:00",
        "ends_at":   "2025-11-02T10:00:00+00:00",
        "purpose": "Reserva 2",
    }, headers=user_headers)

    r = client.post("/reservations", json={
        "room_id": room3["id"],
        "starts_at": "2025-11-03T09:00:00+00:00",
        "ends_at":   "2025-11-03T10:00:00+00:00",
        "purpose": "Reserva 3",
    }, headers=user_headers)
    assert r.status_code == 422
    assert "limit" in r.json()["detail"].lower()


def test_user_cannot_exceed_daily_hours(client, admin_headers):
    from app.core.config import settings
    original_active_limit = settings.user_max_active_reservations
    settings.user_max_active_reservations = 10

    try:
        _, user_headers = make_user(client)
        room1 = make_room(client, admin_headers, name="Diaria A")
        room2 = make_room(client, admin_headers, name="Diaria B")
        room3 = make_room(client, admin_headers, name="Diaria C")

        client.post("/reservations", json={
            "room_id": room1["id"],
            "starts_at": "2025-11-10T08:00:00+00:00",
            "ends_at":   "2025-11-10T10:00:00+00:00",
            "purpose": "Manha",
        }, headers=user_headers)

        r2 = client.post("/reservations", json={
            "room_id": room2["id"],
            "starts_at": "2025-11-10T14:00:00+00:00",
            "ends_at":   "2025-11-10T16:00:00+00:00",
            "purpose": "Tarde",
        }, headers=user_headers)
        assert r2.status_code == 201  

        r3 = client.post("/reservations", json={
            "room_id": room3["id"],
            "starts_at": "2025-11-10T17:00:00+00:00",
            "ends_at":   "2025-11-10T18:00:00+00:00",
            "purpose": "Extra",
        }, headers=user_headers)
        assert r3.status_code == 422
        assert "daily limit" in r3.json()["detail"].lower()
    finally:
        settings.user_max_active_reservations = original_active_limit


def test_admin_is_exempt_from_all_limits(client, admin_headers):
    room = make_room(client, admin_headers, name="Admin Sala")

    r = client.post("/reservations", json={
        "room_id": room["id"],
        "starts_at": "2025-12-01T08:00:00+00:00",
        "ends_at":   "2025-12-01T11:00:00+00:00",
        "purpose": "Reuniao longa do admin",
    }, headers=admin_headers)
    assert r.status_code == 201


def test_canceled_reservation_does_not_count_toward_limit(client, admin_headers):
    _, user_headers = make_user(client)
    room1 = make_room(client, admin_headers, name="Count A")
    room2 = make_room(client, admin_headers, name="Count B")
    room3 = make_room(client, admin_headers, name="Count C")

    r1 = client.post("/reservations", json={
        "room_id": room1["id"],
        "starts_at": "2025-12-10T09:00:00+00:00",
        "ends_at":   "2025-12-10T10:00:00+00:00",
        "purpose": "Cancelada 1",
    }, headers=user_headers).json()
    r2 = client.post("/reservations", json={
        "room_id": room2["id"],
        "starts_at": "2025-12-11T09:00:00+00:00",
        "ends_at":   "2025-12-11T10:00:00+00:00",
        "purpose": "Cancelada 2",
    }, headers=user_headers).json()
    client.patch(f"/reservations/{r1['id']}/cancel", headers=user_headers)
    client.patch(f"/reservations/{r2['id']}/cancel", headers=user_headers)

    r3 = client.post("/reservations", json={
        "room_id": room3["id"],
        "starts_at": "2025-12-12T09:00:00+00:00",
        "ends_at":   "2025-12-12T10:00:00+00:00",
        "purpose": "Nova apos cancelamentos",
    }, headers=user_headers)
    assert r3.status_code == 201
