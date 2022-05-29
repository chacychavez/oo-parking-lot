import dataclasses
import datetime
import json

from flask import Blueprint, Response, request

from backend.models.parking import ParkingSystem, Size, Vehicle
from backend.models.parkingerrs import (
    AlreadyParkedError,
    InvalidEntryPointError,
    InvalidSizeError,
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

    error = None
    try:
        parking_system = ParkingSystem(entry_points, slots, sizes)
    except InvalidSizeError as err:
        error = dict(response=err.message, status=400)
    except Exception as exc:
        error = dict(response=str(exc), status=500)

    if error:
        return Response(**error)

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


@parking.route("/vehicles", methods=(["GET"]))
def get_vehicles():
    if parking_system is None:
        # Not initialized
        return Response(response="System not initialized", status=405)

    vehicles = parking_system.get_vehicles()

    data = dict(vehicles=vehicles)
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

    # TODO: Move handling to Vehicle class
    if size not in {*Size}:
        return Response(response="Invalid vehicle size", status=400)
    vehicle = Vehicle(plate_number, size)

    time_parked = body.get("time_parked")
    time_parked_timestamp = None
    if time_parked:
        time_parked_timestamp = datetime.datetime(*time_parked).timestamp()

    error = None
    try:
        location = parking_system.park(vehicle, entry_point, time_parked_timestamp)
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

    time_unparked = body.get("time_unparked")
    time_unparked_timestamp = None
    if time_unparked:
        time_unparked_timestamp = datetime.datetime(*time_unparked).timestamp()

    error = None
    try:
        charge = parking_system.unpark(plate_number, time_unparked_timestamp)
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
