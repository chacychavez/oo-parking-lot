class ParkingError(Exception):
    def __init__(self, message):
        self.message = message


class NoSlotAvailableError(ParkingError):
    pass


class AlreadyParkedError(ParkingError):
    pass


class VehicleNotExistsError(ParkingError):
    pass


class InvalidEntryPointError(ParkingError):
    pass


class InvalidSizeError(ParkingError):
    pass
