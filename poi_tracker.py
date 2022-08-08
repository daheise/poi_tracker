from email import header
from math import atan, radians, sin, cos, atan2, degrees
import os
import csv
import geopy
import pyttsx3
from time import sleep
from lib.koseng.simconnect_mobiflight import SimConnectMobiFlight
from config import PoiTrackerConfig

from flight_parameters import FlightDataMetrics, SightseeingDiscriminator
from poi_curses import PoiCurses

class Poi:
    def __init__(self, kind, name, lat, lon, description):
        self.kind = kind
        self.name = name
        self.lat = lat
        self.lon = lon
        self.description = description
        self.distance = 10819.389 # Half the circumference of Earth
        self.bearing = 0

    def to_list(self):
        # This format matches LNM's userpoint CSV
        return [self.kind, self.name, '', self.lat, self.lon, '', '', '', self.description]

    
class PoiTracker:
    def __init__(self, discriminator: SightseeingDiscriminator, config: PoiTrackerConfig,  unvisited_pois_file = 'data/unvisited_pois.csv', visited_pois_file = 'data/visited_pois.csv'):
        self.config = config
        self.unvisited_pois_file = unvisited_pois_file
        self.visited_pois_file = visited_pois_file
        self.discriminator = discriminator
        self.load_unvisited_pois()
        self.load_visited_pois()
    
    def load_pois(self, path):
        pois = []
        with open(path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                poi = Poi( kind = row[0], 
                    name = row[1], 
                    lat = float(row[3]), 
                    lon = float(row[4]), 
                    description = row[8])
                pois.append(poi)
        return pois

    def load_unvisited_pois(self):
        self.unvisited_pois = self.load_pois(self.unvisited_pois_file)
    
    def load_visited_pois(self):
        self.visited_pois = self.load_pois(self.visited_pois_file)

    def save_pois(self, pois, path):
        header = "Type,Name,Ident,Latitude,Longitude,Elevation,Magnetic Declination,Tags,Description".split(',')
        with open(f"{path}.tmp",'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            for p in pois:
                writer.writerow(p.to_list())
        os.remove(path)
        os.rename(f"{path}.tmp", f"{path}")

    def save_unvisited_pois(self):
        self.save_pois(self.unvisited_pois, self.unvisited_pois_file)

    def save_visited_pois(self):
        self.save_pois(self.visited_pois, self.visited_pois_file)

    def _get_bearing(self, lat1, lon1, lat2, lon2):
        lat1 = radians(lat1)
        lon1 = radians(lon1)
        lat2 = radians(lat2)
        lon2 = radians(lon2)
        dLon = lon2 - lon1
        x = cos(lat2) * sin(dLon)
        y = (cos(lat1) * sin(lat2)) - (sin(lat1) * cos(lat2) * cos(dLon))
        brng = degrees(atan2(x, y))
        if brng < 0: brng+= 360
        return brng

    def _update_poi_distances(self, lat, lon):
        for p in self.unvisited_pois:
            distance = geopy.distance.distance((lat, lon), (p.lat, p.lon)).nm
            p.distance = distance
            p.bearing = self._get_bearing(lat, lon, p.lat, p.lon)
        for p in self.visited_pois:
            distance = geopy.distance.distance((lat, lon), (p.lat, p.lon)).nm
            p.distance = distance
            p.bearing = self._get_bearing(lat, lon, p.lat, p.lon)
        self.unvisited_pois.sort(key=lambda a: a.distance)
        self.visited_pois.sort(key=lambda a: a.distance)

        return

    def get_nearest_unvisited_pois(self, lat, lon):
        self._update_poi_distances(lat, lon)
        return self.unvisited_pois[0:self.config.closest_count]
    
    def get_nearest_visited_pois(self, lat, lon):
        self._update_poi_distances(lat, lon)
        return self.visited_pois[0:self.config.closest_count]

    def get_pois_in_sight(self, lat, lon):
        self._update_poi_distances(lat, lon)
        pois = [p for p in self.unvisited_pois if p.distance < self.config.max_distance]
        return pois

    def remove_pois(self, pois = []):
        if len(pois) == 0:
            return
        for p in pois:
            self.unvisited_pois.remove(p)
            self.visited_pois.append(p)
        self.save_visited_pois()
        self.save_unvisited_pois()

def connect(retries=999):
    connected = False
    sm = None
    i = 0
    while not connected and i <= retries:
        i += 1
        try:
            sm = SimConnectMobiFlight()  # SimConnect()
            connected = True
        except KeyboardInterrupt:
            quit()
        except Exception as e:
            # ui.write_message(type(e).__name__, e)
            sleep(1)
    return sm

# Defining main function
def main(stdscr):
    stdscr.nodelay(True)
    ui = PoiCurses(stdscr)
    config = PoiTrackerConfig('config.ini')
    sm = connect()
    flight_data = FlightDataMetrics(sm, config)
    discriminator = SightseeingDiscriminator(flight_data, config)
    pt = PoiTracker(discriminator, config)
    tts_engine = pyttsx3.init()

    while True:
        flight_data.update()
        nuv = pt.get_nearest_unvisited_pois(flight_data.location[0], flight_data.location[1])
        nv = pt.get_nearest_visited_pois(flight_data.location[0], flight_data.location[1])
        y = pt.get_pois_in_sight(flight_data.location[0], flight_data.location[1])
        ui.write_agl(flight_data.agl)
        ui.write_ground_speed(flight_data.ground_speed)
        ui.write_closest_unvisited_pois(nuv)
        ui.write_closest_visited_pois(nv)
        ui.update()
        for p in y:
            tts_engine.say(f"Have {p.name} in sight.")
            tts_engine.runAndWait()
        pt.remove_pois(y)
        sleep(config.update_speed)
    
  
  
if __name__ == "__main__":
    from curses import wrapper

    try:
        os.system("mode con: cols=65 lines=20")
        wrapper(main)
    except OSError:
        os.system("cls")
        print("Flight Simulator exited. Shutting down.")
        sys.exit()