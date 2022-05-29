import dataclasses
import json

from flask import Blueprint, Response, request

from backend.models.parking import ParkingSystem, Vehicle
from backend.models.parkingerrs import (
    AlreadyParkedError,
    InvalidEntryPointError,
    NoSlotAvailableError,
    VehicleNotExistsError,
)


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


parking = Blueprint("parking", __name__)

parking_system = None


@parking.route("/init", methods=(["POST"]))
def init_parking():
    global parking_system
    if parking_system is not None:
        # Already initialized
        return Response(response="System already initialized", status=400)

    body = request.get_json()
    entry_points = body["entry_points"]
    slots = [tuple(slot) for slot in body["slots"]]
    sizes = body["sizes"]
    parking_system = ParkingSystem(entry_points, slots, sizes)

    return Response(response="System initialized", status=201)


@parking.route("/", methods=(["GET"]))
@parking.route("/slots", methods=(["GET"]))
def get_slots():
    if parking_system is None:
        # Not initialized
        return Response(response="System not initialized", status=405)

    slots = parking_system.get_slots()

    data = dict(slots=slots)
    return Response(
        response=json.dumps(data, cls=EnhancedJSONEncoder),
        status=200,
        mimetype="application/json",
    )


@parking.route("/park", methods=(["POST"]))
def park():
    if parking_system is None:
        # Not initialized
        return Response(response="System not initialized", status=405)

    body = request.get_json()
    plate_number = body["plate_number"]
    size = body["size"]
    entry_point = body["entry_point"]
    vehicle = Vehicle(plate_number, size)

    error = None
    try:
        location = parking_system.park(vehicle, entry_point)
    except (AlreadyParkedError, InvalidEntryPointError) as err:
        error = dict(response=err.message, status=400)
    except NoSlotAvailableError as err:
        error = dict(response=err.message, status=503)
    except Exception as exc:
        error = dict(response=str(exc), status=500)

    if error:
        return Response(**error)

    data = dict(location=location)
    return Response(
        response=json.dumps(data, cls=EnhancedJSONEncoder),
        status=200,
        mimetype="application/json",
    )


@parking.route("/unpark", methods=(["POST"]))
def unpark():
    if parking_system is None:
        # Not initialized
        return Response(response="System not initialized", status=405)

    body = request.get_json()
    plate_number = body["plate_number"]

    error = None
    try:
        charge = parking_system.unpark(plate_number)
    except VehicleNotExistsError as err:
        error = dict(response=err.message, status=400)
    except Exception as exc:
        error = dict(response=str(exc), status=500)

    if error:
        return Response(**error)

    data = dict(charge=charge)
    return Response(
        response=json.dumps(data, cls=EnhancedJSONEncoder),
        status=200,
        mimetype="application/json",
    )
