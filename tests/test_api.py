def _create_driver(client):
    response = client.post(
        "/drivers",
        json={
            "first_name": "Jan",
            "last_name": "Novak",
            "email": "jan.novak@example.com",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def _create_vehicle(client, license_plate: str, vin: str):
    response = client.post(
        "/vehicles",
        json={
            "license_plate": license_plate,
            "vin": vin,
            "brand": "Skoda",
            "model": "Octavia",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_create_assignment_success(client):
    driver_id = _create_driver(client)
    vehicle_id = _create_vehicle(client, "BA123AA", "VIN0001")

    response = client.post(
        "/assignments",
        json={
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "assigned_from": "2026-01-01",
            "assigned_to": "2026-01-31",
            "is_primary": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["driver_id"] == driver_id
    assert payload["vehicle_id"] == vehicle_id
    assert payload["is_primary"] is True


def test_driver_cannot_have_overlapping_assignment(client):
    driver_id = _create_driver(client)
    vehicle_1 = _create_vehicle(client, "BA111AA", "VIN1111")
    vehicle_2 = _create_vehicle(client, "BA222AA", "VIN2222")

    first = client.post(
        "/assignments",
        json={
            "driver_id": driver_id,
            "vehicle_id": vehicle_1,
            "assigned_from": "2026-02-01",
            "assigned_to": "2026-02-28",
            "is_primary": False,
        },
    )
    assert first.status_code == 200

    overlapping = client.post(
        "/assignments",
        json={
            "driver_id": driver_id,
            "vehicle_id": vehicle_2,
            "assigned_from": "2026-02-15",
            "assigned_to": "2026-03-15",
            "is_primary": False,
        },
    )

    assert overlapping.status_code == 400
    assert "Driver already has an assignment" in overlapping.json()["detail"]


def test_vehicle_cannot_have_overlapping_assignment(client):
    driver_1 = _create_driver(client)

    response = client.post(
        "/drivers",
        json={
            "first_name": "Peter",
            "last_name": "Mrkva",
            "email": "peter.mrkva@example.com",
        },
    )
    assert response.status_code == 200
    driver_2 = response.json()["id"]

    vehicle_id = _create_vehicle(client, "BA333AA", "VIN3333")

    first = client.post(
        "/assignments",
        json={
            "driver_id": driver_1,
            "vehicle_id": vehicle_id,
            "assigned_from": "2026-04-01",
            "assigned_to": "2026-04-30",
            "is_primary": False,
        },
    )
    assert first.status_code == 200

    overlapping = client.post(
        "/assignments",
        json={
            "driver_id": driver_2,
            "vehicle_id": vehicle_id,
            "assigned_from": "2026-04-15",
            "assigned_to": "2026-05-10",
            "is_primary": False,
        },
    )

    assert overlapping.status_code == 400
    assert "Vehicle is already assigned" in overlapping.json()["detail"]


def test_assignment_date_validation(client):
    driver_id = _create_driver(client)
    vehicle_id = _create_vehicle(client, "BA444AA", "VIN4444")

    response = client.post(
        "/assignments",
        json={
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "assigned_from": "2026-06-30",
            "assigned_to": "2026-06-01",
            "is_primary": False,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "assigned_from cannot be after assigned_to"


def test_update_driver_success(client):
    driver_id = _create_driver(client)

    response = client.put(
        f"/drivers/{driver_id}",
        json={
            "first_name": "Janko",
            "last_name": "Novotny",
            "phone": "+421900123123",
            "email": "janko.novotny@example.com",
            "license_number": "DL-001",
            "license_valid_until": "2028-12-31",
            "note": "updated",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["first_name"] == "Janko"
    assert payload["license_number"] == "DL-001"


def test_delete_driver_without_assignments_success(client):
    driver_id = _create_driver(client)

    response = client.delete(f"/drivers/{driver_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Driver deleted successfully"


def test_driver_deactivate_closes_open_assignments(client):
    driver_id = _create_driver(client)
    vehicle_id = _create_vehicle(client, "BA555AA", "VIN5555")

    assignment = client.post(
        "/assignments",
        json={
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "assigned_from": "2026-07-01",
            "assigned_to": None,
            "is_primary": False,
        },
    )
    assert assignment.status_code == 200
    assignment_id = assignment.json()["id"]

    deactivate = client.post(f"/drivers/{driver_id}/deactivate")
    assert deactivate.status_code == 200

    driver_list = client.get("/drivers")
    assert driver_list.status_code == 200
    assert all(item["id"] != driver_id for item in driver_list.json())

    updated_assignment = client.get(f"/assignments/{assignment_id}")
    assert updated_assignment.status_code == 200
    assert updated_assignment.json()["assigned_to"] is not None


def test_update_vehicle_success(client):
    vehicle_id = _create_vehicle(client, "BA666AA", "VIN6666")

    response = client.put(
        f"/vehicles/{vehicle_id}",
        json={
            "license_plate": "BA666AB",
            "vin": "VIN6666-NEW",
            "brand": "VW",
            "model": "Passat",
            "year": 2022,
            "fuel_type": "diesel",
            "current_km": 145000,
            "note": "updated",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["license_plate"] == "BA666AB"
    assert payload["brand"] == "VW"


def test_delete_vehicle_without_assignments_success(client):
    vehicle_id = _create_vehicle(client, "BA777AA", "VIN7777")

    response = client.delete(f"/vehicles/{vehicle_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Vehicle deleted successfully"


def test_vehicle_duplicate_license_plate_returns_400(client):
    _create_vehicle(client, "BA888AA", "VIN8888")

    response = client.post(
        "/vehicles",
        json={
            "license_plate": "BA888AA",
            "vin": "VIN8889",
            "brand": "Skoda",
            "model": "Fabia",
        },
    )

    assert response.status_code == 400
    assert "Vehicle with this license plate or VIN already exists" in response.json()["detail"]


def test_vehicle_duplicate_vin_returns_400(client):
    _create_vehicle(client, "BA889AA", "VIN8890")

    response = client.post(
        "/vehicles",
        json={
            "license_plate": "BA889AB",
            "vin": "VIN8890",
            "brand": "Skoda",
            "model": "Scala",
        },
    )

    assert response.status_code == 400
    assert "Vehicle with this license plate or VIN already exists" in response.json()["detail"]


def test_update_assignment_success(client):
    driver_1 = _create_driver(client)
    driver_2_response = client.post(
        "/drivers",
        json={
            "first_name": "Marek",
            "last_name": "Kovac",
            "email": "marek.kovac@example.com",
        },
    )
    assert driver_2_response.status_code == 200
    driver_2 = driver_2_response.json()["id"]

    vehicle_1 = _create_vehicle(client, "BA900AA", "VIN9000")
    vehicle_2 = _create_vehicle(client, "BA901AA", "VIN9001")

    created = client.post(
        "/assignments",
        json={
            "driver_id": driver_1,
            "vehicle_id": vehicle_1,
            "assigned_from": "2026-08-01",
            "assigned_to": "2026-08-10",
            "is_primary": False,
        },
    )
    assert created.status_code == 200
    assignment_id = created.json()["id"]

    updated = client.put(
        f"/assignments/{assignment_id}",
        json={
            "driver_id": driver_2,
            "vehicle_id": vehicle_2,
            "assigned_from": "2026-08-12",
            "assigned_to": "2026-08-25",
            "is_primary": True,
            "note": "updated",
        },
    )

    assert updated.status_code == 200
    payload = updated.json()
    assert payload["driver_id"] == driver_2
    assert payload["vehicle_id"] == vehicle_2
    assert payload["is_primary"] is True


def test_delete_assignment_success(client):
    driver_id = _create_driver(client)
    vehicle_id = _create_vehicle(client, "BA990AA", "VIN9900")

    created = client.post(
        "/assignments",
        json={
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "assigned_from": "2026-09-01",
            "assigned_to": "2026-09-30",
            "is_primary": False,
        },
    )
    assert created.status_code == 200
    assignment_id = created.json()["id"]

    deleted = client.delete(f"/assignments/{assignment_id}")
    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Assignment deleted successfully"

    missing = client.get(f"/assignments/{assignment_id}")
    assert missing.status_code == 404


def test_create_update_delete_trip(client):
    driver_id = _create_driver(client)
    vehicle_id = _create_vehicle(client, "BATRIP1", "VINTRIP1")

    created = client.post(
        "/trips",
        json={
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "trip_date": "2026-10-01",
            "start_km": 1000,
            "end_km": 1125,
            "route": "BA-KE",
            "purpose": "Delivery",
            "note": "first trip",
        },
    )
    assert created.status_code == 200
    trip_id = created.json()["id"]

    updated = client.put(
        f"/trips/{trip_id}",
        json={
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "trip_date": "2026-10-02",
            "start_km": 1125,
            "end_km": 1240,
            "route": "KE-PO",
            "purpose": "Service",
            "note": "updated",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["end_km"] == 1240

    deleted = client.delete(f"/trips/{trip_id}")
    assert deleted.status_code == 200

    missing = client.get(f"/trips/{trip_id}")
    assert missing.status_code == 404


def test_trip_kilometer_validation(client):
    driver_id = _create_driver(client)
    vehicle_id = _create_vehicle(client, "BAERR1", "VINERR1")

    response = client.post(
        "/trips",
        json={
            "driver_id": driver_id,
            "vehicle_id": vehicle_id,
            "trip_date": "2026-11-01",
            "start_km": 2000,
            "end_km": 1500,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "end_km cannot be lower than start_km"


def test_create_update_delete_refuel(client):
    driver_id = _create_driver(client)
    vehicle_id = _create_vehicle(client, "BAFUEL1", "VINFUEL1")

    created = client.post(
        "/refuels",
        json={
            "vehicle_id": vehicle_id,
            "driver_id": driver_id,
            "refuel_date": "2026-12-01",
            "liters": 42.5,
            "total_cost": 75.9,
            "price_per_liter": 1.786,
            "odometer_km": 1240,
            "station": "OMV",
            "note": "full tank",
        },
    )
    assert created.status_code == 200
    refuel_id = created.json()["id"]

    updated = client.put(
        f"/refuels/{refuel_id}",
        json={
            "vehicle_id": vehicle_id,
            "driver_id": None,
            "refuel_date": "2026-12-02",
            "liters": 20.0,
            "total_cost": 38.0,
            "price_per_liter": 1.9,
            "odometer_km": 1310,
            "station": "Shell",
            "note": "partial",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["station"] == "Shell"

    deleted = client.delete(f"/refuels/{refuel_id}")
    assert deleted.status_code == 200

    missing = client.get(f"/refuels/{refuel_id}")
    assert missing.status_code == 404


def test_refuel_liters_validation(client):
    vehicle_id = _create_vehicle(client, "BAFUEL2", "VINFUEL2")

    response = client.post(
        "/refuels",
        json={
            "vehicle_id": vehicle_id,
            "driver_id": None,
            "refuel_date": "2026-12-05",
            "liters": 0,
            "total_cost": 15.0,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "liters must be greater than 0"
