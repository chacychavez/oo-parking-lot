import math
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional

from .parkingerrs import (
    AlreadyParkedError,
    InvalidEntryPointError,
    InvalidSizeError,
    NoSlotAvailableError,
    VehicleNotExistsError,
)


class Size(IntEnum):
    SMALL = 0
    MEDIUM = 1
    LARGE = 2


SlotLocation = tuple


@dataclass
class Slot:
    location: SlotLocation
    size: Size
    is_vacant: bool = True

    pass


@dataclass
class ParkingLog:
    slot_location: SlotLocation
    time_parked: float
    time_unparked: Optional[float] = None
    charge: Optional[int] = None


@dataclass
class Vehicle:
    plate_number: str
    size: Size
    is_parked: bool = False
    parking_logs: List[ParkingLog] = field(default_factory=list)

    def add_log(self, log: ParkingLog):
        self.parking_logs.append(log)


class ParkingSystem:
    HOUR_RATES = {Size.SMALL: 20, Size.MEDIUM: 60, Size.LARGE: 100}
    HOURS_IN_SEC = 60 * 60

    def __init__(self, entry_points: int, slots: List[tuple], sizes: List[int]):
        self._entry_points = entry_points
        self._slots = {}
        self._vehicles = {}

        # Initialize slots
        for i in range(len(slots)):
            if sizes[i] not in {*Size}:
                raise InvalidSizeError("Invalid size")
            self._slots[slots[i]] = Slot(slots[i], sizes[i])

    def get_slots(self) -> List[Slot]:
        return list(self._slots.values())

    def get_slot(self, slot_location: SlotLocation) -> Slot:
        return self._slots.get(slot_location)

    def get_vehicles(self) -> List[Vehicle]:
        return list(self._vehicles.values())

    def get_vehicle(self, plate_number: str) -> Vehicle:
        return self._vehicles.get(plate_number)

    def get_nearest_slot(self, size, entry_point: int) -> Optional[Slot]:
        vacant_slots = filter(
            lambda slot: slot.is_vacant and slot.size >= size, self._slots.values()
        )
        sorted_slots = sorted(vacant_slots, key=lambda item: item.location[entry_point])
        if not sorted_slots:
            return None
        return sorted_slots[0]

    def park(
        self, vehicle: Vehicle, entry_point: int, time_parked=None
    ) -> Optional[SlotLocation]:
        if entry_point not in range(self._entry_points):
            raise InvalidEntryPointError("Invalid entry point.")

        if time_parked is None:
            time_parked = time.time()
        saved_vehicle = self._vehicles.get(vehicle.plate_number)
        if saved_vehicle:
            if saved_vehicle.is_parked:
                raise AlreadyParkedError("Vehicle already parked.")
            # Check for continuous rate parking
            current_log = saved_vehicle.parking_logs[-1]

            # Make sure we don't get negative difference
            assert time_parked >= current_log.time_unparked
            if time_parked - current_log.time_unparked < self.HOURS_IN_SEC:
                vehicle = saved_vehicle

        slot = self.get_nearest_slot(vehicle.size, entry_point)
        if slot is None:
            raise NoSlotAvailableError("No slots available.")

        vehicle.add_log(
            ParkingLog(time_parked=time_parked, slot_location=slot.location)
        )

        # Set attributes after parking
        vehicle.is_parked = True
        slot.is_vacant = False

        # Update/insert vehicle
        self._vehicles[vehicle.plate_number] = vehicle

        return slot.location

    def unpark(self, plate_number: str, time_unparked=None) -> int:
        vehicle = self._vehicles.get(plate_number)
        if vehicle is None or not vehicle.is_parked:
            raise VehicleNotExistsError("Vehicle not parked.")

        if time_unparked is None:
            time_unparked = time.time()
        current_log = vehicle.parking_logs[-1]

        # Make sure we don't get negative difference
        assert time_unparked >= current_log.time_parked
        current_log.time_unparked = time_unparked
        slot = self._slots[current_log.slot_location]

        charge = self._get_charge(vehicle.parking_logs)

        # Set attributes after unparking
        current_log.charge = charge
        vehicle.is_parked = False
        slot.is_vacant = True

        return charge

    def _get_charge(self, logs: List[ParkingLog]) -> int:
        total_hours_consumed = 0
        total_charge = 0
        current_start_time = logs[0].time_parked

        paid_charge = 0
        logs_len = len(logs)
        for i in range(logs_len):
            current_log = logs[i]
            # Make sure we don't get negative difference
            assert current_log.time_unparked >= current_log.time_parked

            # Use for continuous rate conditions
            prev_total_hours_consumed = total_hours_consumed

            hours_consumed = (current_log.time_unparked - current_start_time) / (
                self.HOURS_IN_SEC
            )

            hours_consumed_ceiled = math.ceil(hours_consumed)
            total_hours_consumed += hours_consumed_ceiled

            # Get hour rate
            current_slot = self._slots[current_log.slot_location]
            hour_rate = self.HOUR_RATES[current_slot.size]

            if total_hours_consumed <= 3:
                total_charge = 40
            elif 3 < total_hours_consumed < 24 and prev_total_hours_consumed < 3:
                # Compute continous rate charge from flat charge
                total_charge = 40 + ((total_hours_consumed - 3) * hour_rate)
            elif (
                total_hours_consumed >= 24 and prev_total_hours_consumed < 24
            ) or hours_consumed > 24 - (prev_total_hours_consumed % 24):
                # Compute charge for daily rate
                # Case #1: hours_consumed > 24
                # Case #2: prev_hours_consumed == 40, current hours_consumed == 10
                # -> total of 50 hours;
                total_charge = (5000 * (total_hours_consumed // 24)) + (
                    hour_rate * (total_hours_consumed % 24)
                )
            else:
                # Add hourly rate charge to the total_charge
                total_charge += hours_consumed_ceiled * hour_rate

            # Remaining time computation
            # Since we round up the hours_consumed, we need to get what hour the next
            # charge be given.
            remaining_time = (hours_consumed_ceiled - hours_consumed) * (
                self.HOURS_IN_SEC
            )
            current_start_time = current_log.time_unparked + remaining_time

            # Add all previous charges
            if i < logs_len - 1:
                paid_charge += current_log.charge

        return total_charge - paid_charge
