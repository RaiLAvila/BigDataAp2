class HotelBookingDetails:
    def __init__(
        self,
        destination: str = None,
        checkin_date: str = None,
        checkout_date: str = None,
    ):
        self.destination = destination
        self.checkin_date = checkin_date
        self.checkout_date = checkout_date
