class FlightBookingDetails:
    def __init__(
        self,
        destination: str = None,
        origin: str = None,
        departure_date: str = None,
        unsupported_airports=None,
    ):
        if unsupported_airports is None:
            unsupported_airports = []
        self.destination = destination
        self.origin = origin
        self.departure_date = departure_date
        self.unsupported_airports = unsupported_airports
