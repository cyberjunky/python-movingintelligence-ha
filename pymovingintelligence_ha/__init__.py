"""Home Assistant Python 3 API wrapper for Moving Intelligence."""
import datetime
import logging

from .utils import Utils

_LOGGER = logging.getLogger("pymovingintelligence_ha")


class MovingIntelligence:
    """Class for communicating with the Moving Intelligence API."""

    def __init__(
        self,
        username: str = None,
        apikey: str = None,
    ):
        """Init module."""

        self.utils = Utils(username, apikey)

    async def get_devices(self) -> dict:
        """Get devices."""
        result = []

        objects = await self.utils.request(
            "GET",
            endpoint="/v1/objects",
        )

        for item in objects:
            device = Device(self.utils, item["licence"])
            await device.update_from_json(item)
            if device.odometer:
                result.append(device)

        return result


class Device:
    """Entity used to store device information."""

    def __init__(self, utilities, license_plate):
        """Initialize a device, also a vehicle."""
        self._utilities = utilities

        self.identifier = None
        self.make = None
        self.model = None
        self.license_plate = license_plate
        self.chassis_number = None
        self.in_use_date = None
        self.year = None
        self.remarks = None
        self.latitude = 0
        self.longitude = 0
        self.odometer = None
        self.speed = None
        self.start_trip_time = None
        self.start_trip_street = None
        self.start_trip_city = None
        self.start_trip_country = None
        self.trip_distance = None
        self.end_trip_street = None
        self.end_trip_city = None
        self.end_trip_country = None
        self.end_trip_time = None
        self.trip_distance = None
        self.start_trip_address = None
        self.end_trip_address = None
        self.last_seen = None
        self.location_alias = None

    @property
    def data(self):
        """Return all data of the vehicle."""

        return {
            "id": self.identifier,
            "make": self.make,
            "model": self.model,
            "license_plate": self.license_plate,
            "chassis_number": self.chassis_number,
            "in_use_date": self.in_use_date,
            "year": self.year,
            "remarks": self.remarks,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "odometer": self.odometer,
            "speed": self.speed,
            "start_trip_time": self.start_trip_time,
            "start_trip_address": self.start_trip_address,
            "end_trip_time": self.end_trip_time,
            "end_trip_address": self.end_trip_address,
            "trip_distance": self.trip_distance,
            "last_seen": self.end_trip_time,
            "location_alias": self.location_alias,
        }

    async def update_from_json(self, data):
        """Set all attributes based on API response."""

        self.identifier = self.getvalue(data, "id")
        self.license_plate = self.getvalue(data, "licence")
        self.make = self.getvalue(data, "brand")
        self.model = self.getvalue(data, "model")
        self.chassis_number = self.getvalue(data, "chassisNumber")
        self.in_use_date = self.converttime(self.getvalue(data, "startDate"))
        self.year = self.getvalue(data, "yearOfManufacture")
        self.remarks = self.getvalue(data, "remarks")
        self.odometer = await self.get_odometer(self.identifier)

        trip = await self.get_object_detailed_trips(
            self.identifier, "CURRENT_MONTH", "UNKNOWN"
        )

        if trip:
            location = trip[-1]["locationAndSpeed"]
            if len(location) > 0 and location[-1].get("lat") is not None:
                self.latitude = float(location[-1]["lat"] / 1000000)
                self.longitude = float(location[-1]["lon"] / 1000000)
                self.speed = location[-1]["speed"]

            self.start_trip_time = self.converttime(
                self.getvalue(trip[-1], "startDate")
            )
            self.start_trip_street = self.getvalue(trip[-1], "startRoad")
            self.start_trip_city = self.getvalue(trip[-1], "startCity")
            self.start_trip_city = self.start_trip_city.replace("|m:", " ")
            self.start_trip_country = self.getvalue(trip[-1], "startCountry")

            self.end_trip_street = self.getvalue(trip[-1], "endRoad")
            self.end_trip_city = self.getvalue(trip[-1], "endCity")
            self.end_trip_city = self.end_trip_city.replace("|m:", " ")
            self.end_trip_country = self.getvalue(trip[-1], "endCountry")
            self.end_trip_time = self.converttime(self.getvalue(trip[-1], "endDate"))

            self.trip_distance = self.getvalue(trip[-1], "distance") / 1000
            self.location_alias = self.getvalue(trip[-1], "endAlias")

            self.start_trip_address = f"{self.start_trip_street}, {self.start_trip_city}, {self.start_trip_country}"
            self.end_trip_address = (
                f"{self.end_trip_street}, {self.end_trip_city}, {self.end_trip_country}"
            )

    @staticmethod
    def getvalue(data, value):
        """Safely get values."""
        if value in data:
            return data[value]
        return None

    @staticmethod
    def converttime(stamp):
        """Convert datestamp."""
        if not stamp:
            return stamp

        when = datetime.datetime.fromtimestamp(stamp)
        return when.strftime("%Y-%m-%d %H:%M:%S")

    async def get_odometer(self, object_id: str) -> dict:
        """Get odometer readings."""

        odometer = None
        data = await self._utilities.request(
            "GET", endpoint=f"/v1/object/{object_id}/odometer"
        )

        if data:
            odometer = int(self.getvalue(data, "odoInMeters") / 1000)

        return odometer

    async def get_object_detailed_trips(
        self, object_id: str, period: str, classifications
    ) -> dict:
        """Get detailed trips for object."""

        return await self._utilities.request(
            "GET",
            endpoint=f"/v1/object/{object_id}/detailedtrips",
            params=self._utilities.clean_request_params(
                {
                    "period": period,
                    "classifications": classifications,
                }
            ),
        )
