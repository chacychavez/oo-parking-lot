import math
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional

from .parkingerrs import AlreadyParkedError, NoSlotAvailableError, VehicleNotExistsError


class SlotSize(IntEnum):
    SMALL = 0
    MEDIUM = 1
    LARGE = 2


SlotLocation = tuple


@dataclass
class Slot:
    location: SlotLocation
    size: SlotSize
    is_vacant: bool = True

    pass


class VehicleSize(IntEnum):
    SMALL = 0
    MEDIUM = 1
    LARGE = 2


@dataclass
class ParkingLog:
    slot_location: SlotLocation
    time_parked: float
    time_unparked: Optional[float] = None
    charge: Optional[int] = None


@dataclass
class Vehicle:
    plate_number: str
    size: VehicleSize
    is_parked: bool = False
    parking_logs: List[ParkingLog] = field(default_factory=list)

    def add_log(self, log: ParkingLog):
        self.parking_logs.append(log)


class ParkingSystem:
    HOUR_RATES = {SlotSize.SMALL: 20, SlotSize.MEDIUM: 60, SlotSize.LARGE: 100}
    HOURS_IN_SEC = 60 * 60

    def __init__(self, entry_points: int, slots: List[tuple], sizes: List[int]):
        self._entry_points = entry_points
        self._slots = {}
        self._vehicles = {}

        # Initialize slots
        for i in range(len(slots)):
            self._slots[slots[i]] = Slot(slots[i], sizes[i])

    def get_slots(self) -> List[Slot]:
        return list(self._slots.values())

    def get_slot(self, slot_location: SlotLocation) -> Slot:
        return self._slots.get(slot_location)

    def get_vehicles(self) -> List[Vehicle]:
        return list(self._vehicles.values)

    def get_vehicle(self, plate_number: str) -> Vehicle:
        return self._vehicles.get(plate_number)

    def get_nearest_slot(self, size, entry_point: int) -> Optional[Slot]:
        vacant_slot = filter(
            lambda slot: slot.is_vacant and slot.size >= size, self._slots.values()
        )
        sorted_slots = sorted(vacant_slot, key=lambda item: item.location[entry_point])
        if not sorted_slots:
            return None
        return sorted_slots[0]

    def park(self, vehicle: Vehicle, entry_point: int) -> Optional[SlotLocation]:
        time_parked = time.time()
        saved_vehicle = self._vehicles.get(vehicle.plate_number)
        if saved_vehicle:
            if saved_vehicle.is_parked:
                raise AlreadyParkedError("Vehicle already parked.")
            current_log = saved_vehicle.parking_logs[-1]
            if current_log.time_unparked - time_parked < self.HOURS_IN_SEC:
                vehicle = saved_vehicle

        slot = self.get_nearest_slot(vehicle.size, entry_point)
        if slot is None:
            raise NoSlotAvailableError("No slot available.")

        vehicle.add_log(
            ParkingLog(time_parked=time_parked, slot_location=slot.location)
        )

        vehicle.is_parked = True
        slot.is_vacant = False

        # Update/insert vehicle
        self._vehicles[vehicle.plate_number] = vehicle

        return slot.location

    def unpark(self, plate_number: str) -> int:
        vehicle = self._vehicles.get(plate_number)
        if vehicle is None or not vehicle.is_parked:
            raise VehicleNotExistsError("Vehicle not parked.")

        time_unparked = time.time()
        current_log = vehicle.parking_logs[-1]
        current_log.time_unparked = time_unparked
        slot = self._slots[current_log.slot_location]

        charge = self._get_charge(vehicle.parking_logs)

        current_log.charge = charge
        vehicle.is_parked = False
        slot.is_vacant = True

        return charge

    def _get_charge(self, logs: List[ParkingLog]) -> int:
        total_hours_consumed = 0
        total_charge = 0
        current_start_time = logs[0].time_parked

        paid_charge = 0
        for i in range(len(logs)):
            current_log = logs[i]
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
                total_charge = 40 + ((total_hours_consumed - 3) * hour_rate)
            elif (
                total_hours_consumed >= 24 and prev_total_hours_consumed < 24
            ) or hours_consumed > 24 - (prev_total_hours_consumed % 24):
                total_charge = (5000 * (total_hours_consumed // 24)) + (
                    hour_rate * (total_hours_consumed % 24)
                )
            else:
                total_charge += hours_consumed_ceiled * hour_rate

            # Remaining time computation
            remaining_time = (hours_consumed_ceiled - hours_consumed) * (
                self.HOURS_IN_SEC
            )
            current_start_time = current_log.time_unparked + remaining_time

            if current_log.charge is not None:
                paid_charge += current_log.charge

        return total_charge - paid_charge
