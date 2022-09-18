from config import PoiTrackerConfig

from SimConnect import *
from geopy import distance
from collections import namedtuple
from sys import maxsize
from math import ceil, radians, degrees, tan, sin, cos, asin, atan2, log2, copysign
from time import sleep
from copy import copy


class SimConnectDataError(Exception):
    pass

class FlightDataMetrics:
    def __init__(self, simconnect_connection, config: PoiTrackerConfig):
        self.sm = simconnect_connection
        self._config = config
        self.aq = AircraftRequests(self.sm)
        self.messages = []
        self._request_sleep = 0.1
        self._max_request_sleep = 1.0
        self._min_request_sleep = 0.1
        self.update()

    def _get_value(self, aq_name, retries=maxsize):
        # PySimConnect seems to crash the sim if requests happen too fast.
        sleep(self._request_sleep)
        val = self.aq.find(str(aq_name)).value
        i = 0
        while val is None and i < retries:
            i += 1
            self._request_sleep = min(
                self._request_sleep + self._min_request_sleep * i, self._max_request_sleep
            )
            sleep(self._request_sleep)
            val = self.aq.find(str(aq_name)).value
        if i > 0:
            self.messages.append(f"Warning: Retried {aq_name} {i} times.")
        self._request_sleep = max(self._min_request_sleep, self._request_sleep - 0.01)
        return val

    def update(self, retries=maxsize):
        # Load these all up for three reasons.
        # 1. These are static items
        # 2. Running them over and over may trigger a memory leak in the game
        # 3. It seems to increase reliability of reading/setting the data
        self.messages = []
        self.aq_cur_lat = self._get_value("GPS_POSITION_LAT")
        self.aq_cur_long = self._get_value("GPS_POSITION_LON")
        self.aq_agl = self._get_value("PLANE_ALT_ABOVE_GROUND")
        self.aq_ground_speed = self._get_value("GPS_GROUND_SPEED")

    @property
    def location(self):
        return (self.aq_cur_lat, self.aq_cur_long)
    
    @property
    def agl(self):
        return self.aq_agl
    
    @property
    def ground_speed(self):
        # Convert m/s to nm/s
        ground_speed = self.aq_ground_speed * 5.4e-4 * 60 * 60
        return ground_speed

class SightseeingDiscriminator:
    def __init__(self, flight_parameters, config: PoiTrackerConfig):
        self._config = config
        self._flight_params: FlightDataMetrics = flight_parameters
        self.messages = []
    
    @property
    def is_sightseeing(self):
        if (self._flight_params.ground_speed < 200 and
           self._flight_params.agl < 3500):
           return True

    def get_messages(self):
        messages = copy(self.messages)
        return messages
