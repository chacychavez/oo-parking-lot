import datetime

import pytest

from backend.models.parking import ParkingLog, ParkingSystem, Size, Vehicle
from backend.models.parkingerrs import (
    AlreadyParkedError,
    NoSlotAvailableError,
    VehicleNotExistsError,
)

entry_points = 3
slots = [(1, 2, 3), (2, 3, 5), (0, 1, 4)]
sizes = [0, 2, 1]


def test_park():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    plate_number = "ABC-123"
    vehicle = Vehicle(plate_number, Size.SMALL)
    location = parking_system.park(vehicle, 0)

    expected_location = (0, 1, 4)
    assert location == expected_location

    slot = parking_system.get_slot(expected_location)
    assert not slot.is_vacant

    vehicle = parking_system.get_vehicle(plate_number)
    assert vehicle.is_parked

    assert vehicle.parking_logs
    assert vehicle.parking_logs[0].slot_location == expected_location


def test_park_full():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    plate_number = "ABC-123"
    vehicle = Vehicle(plate_number, Size.SMALL)
    parking_system.park(vehicle, 0)

    plate_number = "DEF-456"
    vehicle = Vehicle(plate_number, Size.LARGE)
    parking_system.park(vehicle, 2)

    plate_number = "GHI-789"
    vehicle = Vehicle(plate_number, Size.SMALL)
    parking_system.park(vehicle, 1)

    plate_number = "JKL-012"
    vehicle = Vehicle(plate_number, Size.SMALL)
    with pytest.raises(NoSlotAvailableError):
        parking_system.park(vehicle, 0)


def test_already_parked():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    plate_number = "ABC-123"
    vehicle = Vehicle(plate_number, Size.SMALL)
    parking_system.park(vehicle, 0)

    with pytest.raises(AlreadyParkedError):
        parking_system.park(vehicle, 0)


def test_unpark():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    plate_number = "ABC-123"
    vehicle = Vehicle(plate_number, Size.SMALL)
    time_parked = datetime.datetime(2022, 5, 29, 0, 0).timestamp()
    location = parking_system.park(vehicle, 0, time_parked)

    time_unparked = datetime.datetime(2022, 5, 29, 20, 30).timestamp()
    charge = parking_system.unpark(plate_number, time_unparked)
    assert charge == 1120

    slot = parking_system.get_slot(location)
    assert slot.is_vacant

    vehicle = parking_system.get_vehicle(plate_number)
    assert not vehicle.is_parked

    assert vehicle.parking_logs
    assert vehicle.parking_logs[0].charge == 1120


def test_unpark_missing():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    plate_number = "ABC-123"
    with pytest.raises(VehicleNotExistsError):
        parking_system.unpark(plate_number)


def test_continuous_rate():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    plate_number = "ABC-123"
    vehicle = Vehicle(plate_number, Size.SMALL)
    parking_system.park(vehicle, 0)
    parking_system.unpark(plate_number)

    vehicle = Vehicle(plate_number, Size.SMALL)
    parking_system.park(vehicle, 1)

    saved_vehicle = parking_system.get_vehicle(plate_number)
    assert len(saved_vehicle.parking_logs) == 2


def test_not_continuous_rate():
    # Use park and unpark but override time_unpark and unparked
    parking_system = ParkingSystem(entry_points, slots, sizes)

    plate_number = "ABC-123"
    vehicle = Vehicle(plate_number, Size.SMALL)
    parking_system.park(vehicle, 0)
    parking_system.unpark(plate_number)

    saved_vehicle = parking_system.get_vehicle(plate_number)
    current_log = saved_vehicle.parking_logs[-1]
    current_log.time_parked -= ParkingSystem.HOURS_IN_SEC
    current_log.time_unparked -= ParkingSystem.HOURS_IN_SEC

    vehicle = Vehicle(plate_number, Size.SMALL)
    parking_system.park(vehicle, 1)

    # Retrived again to make sure we get the latest saved_vehicle
    saved_vehicle = parking_system.get_vehicle(plate_number)
    assert len(saved_vehicle.parking_logs) == 1


def test_basic_flat_rate():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    # Use ParkingSystem._get_charge directly to properly test rates
    parking_logs = [
        ParkingLog(
            time_parked=datetime.datetime(2022, 5, 29, 1, 0).timestamp(),
            time_unparked=datetime.datetime(2022, 5, 29, 3, 30).timestamp(),
            slot_location=(1, 2, 3),
        )
    ]

    charge = parking_system._get_charge(parking_logs)
    assert charge == 40


def test_basic_hour_rates():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    # Use ParkingSystem._get_charge directly to properly test rates
    parking_logs = [
        ParkingLog(
            time_parked=datetime.datetime(2022, 5, 29, 0, 0).timestamp(),
            time_unparked=datetime.datetime(2022, 5, 29, 13, 30).timestamp(),
            slot_location=(1, 2, 3),
        )
    ]

    # hours_consumed (ceiled) = 14
    # hours consumed after flat rate = 11
    # 40 + (11 * 20) = 260
    charge = parking_system._get_charge(parking_logs)
    assert charge == 260


def test_basic_day_rates():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    # Use ParkingSystem._get_charge directly to properly test rates
    parking_logs = [
        ParkingLog(
            time_parked=datetime.datetime(2022, 5, 29, 0, 0).timestamp(),
            time_unparked=datetime.datetime(2022, 5, 31, 6, 30).timestamp(),
            slot_location=(2, 3, 5),
        )
    ]

    # days = 2
    # hours = 7
    # hour rate = 100/hr
    # (5000 * 2) + (7 * 100) = 10700
    charge = parking_system._get_charge(parking_logs)
    assert charge == 10700


def test_continuous_rate_flat_and_flat_no_charge():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    # Use ParkingSystem._get_charge directly to properly test rates
    parking_logs = [
        ParkingLog(
            time_parked=0,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 2.5,
            slot_location=(1, 2, 3),
            charge=40,
        ),
        ParkingLog(
            time_parked=2.8,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 3,
            slot_location=(1, 2, 3),
        ),
    ]

    charge = parking_system._get_charge(parking_logs)
    assert charge == 0


def test_continuous_rate_hour_and_hour_no_charge():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    # Use ParkingSystem._get_charge directly to properly test rates
    parking_logs = [
        ParkingLog(
            time_parked=0,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 3.5,
            slot_location=(1, 2, 3),
            charge=60,
        ),
        ParkingLog(
            time_parked=ParkingSystem.HOURS_IN_SEC * 3.8,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 4,
            slot_location=(2, 3, 5),
        ),
    ]

    charge = parking_system._get_charge(parking_logs)
    assert charge == 0


def test_continuous_rate_day_and_day_no_charge():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    # Use ParkingSystem._get_charge directly to properly test rates
    parking_logs = [
        ParkingLog(
            time_parked=0,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 23.5,
            slot_location=(1, 2, 3),
            charge=5000,
        ),
        ParkingLog(
            time_parked=ParkingSystem.HOURS_IN_SEC * 23.6,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 23.8,
            slot_location=(2, 3, 5),
        ),
    ]

    charge = parking_system._get_charge(parking_logs)
    assert charge == 0


def test_continuous_rate_hour_and_hour():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    # Use ParkingSystem._get_charge directly to properly test rates
    parking_logs = [
        ParkingLog(
            time_parked=0,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 3.5,
            slot_location=(1, 2, 3),
            charge=60,
        ),
        ParkingLog(
            time_parked=ParkingSystem.HOURS_IN_SEC * 3.8,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 5,
            slot_location=(2, 3, 5),
        ),
    ]

    # hour rate = 100
    # hour_consumed after flate rate = 7
    # (7 * 100)
    charge = parking_system._get_charge(parking_logs)
    assert charge == 100


def test_continuous_rate_flat_and_hour():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    # Use ParkingSystem._get_charge directly to properly test rates
    parking_logs = [
        ParkingLog(
            time_parked=0,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 2.5,
            slot_location=(1, 2, 3),
            charge=40,
        ),
        ParkingLog(
            time_parked=ParkingSystem.HOURS_IN_SEC * 3.1,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 10,
            slot_location=(2, 3, 5),
        ),
    ]

    # hour rate = 100
    # hour_consumed after flate rate = 7
    # (7 * 100)
    charge = parking_system._get_charge(parking_logs)
    assert charge == 700


def test_continuous_rate_flat_and_day():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    # Use ParkingSystem._get_charge directly to properly test rates
    parking_logs = [
        ParkingLog(
            time_parked=0,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 3,
            slot_location=(1, 2, 3),
            charge=40,
        ),
        ParkingLog(
            time_parked=ParkingSystem.HOURS_IN_SEC * 3.1,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 47.2,
            slot_location=(2, 3, 5),
        ),
    ]

    # days = 2
    # 10000 - 40
    charge = parking_system._get_charge(parking_logs)
    assert charge == 9960


def test_continuous_rate_hour_and_day():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    # Use ParkingSystem._get_charge directly to properly test rates
    parking_logs = [
        ParkingLog(
            time_parked=0,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 13.5,
            slot_location=(1, 2, 3),
            charge=260,
        ),
        ParkingLog(
            time_parked=ParkingSystem.HOURS_IN_SEC * 14,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 50.2,
            slot_location=(2, 3, 5),
        ),
    ]

    # days =2
    # hour_rate = 100/hr
    # (2 * 5000) + 3 * 100
    # 10300 - 260 = 10040
    charge = parking_system._get_charge(parking_logs)
    assert charge == 10040


def test_continuous_rate_flat_hour_and_day():
    parking_system = ParkingSystem(entry_points, slots, sizes)

    # Use ParkingSystem._get_charge directly to properly test rates
    parking_logs = [
        ParkingLog(
            time_parked=0,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 2.5,
            slot_location=(1, 2, 3),
            charge=40,
        ),
        ParkingLog(
            time_parked=2.8,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 13.5,
            slot_location=(1, 2, 3),
            charge=220,
        ),
        ParkingLog(
            time_parked=ParkingSystem.HOURS_IN_SEC * 14,
            time_unparked=ParkingSystem.HOURS_IN_SEC * 50.2,
            slot_location=(2, 3, 5),
        ),
    ]

    # days = 2
    # hour_rate = 100/hr
    # (2 * 5000) + 3 * 100
    # 10300 - 260 = 10040
    charge = parking_system._get_charge(parking_logs)
    assert charge == 10040
