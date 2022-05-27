class ParkingError(Exception):
    pass


class NoSlotAvailableError(ParkingError):
    pass


class AlreadyParkedError(ParkingError):
    pass


class VehicleNotExistsError(ParkingError):
    pass
