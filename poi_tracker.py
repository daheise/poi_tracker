from copy import deepcopy
from email import header
from genericpath import isfile
from math import atan, radians, sin, cos, atan2, degrees
import os
import csv
import sys
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
    
    def __eq__(self, other):
        return ((self.name == other.name) and
           geopy.distance.distance((self.lat, self.lon), (other.lat, other.lon)).nm < 1)

    
class PoiTracker:
    def __init__(self, discriminator: SightseeingDiscriminator, config: PoiTrackerConfig,  unvisited_pois_file = 'data/unvisited_pois.csv', visited_pois_file = 'data/visited_pois.csv'):
        self.config = config
        self.unvisited_pois_file = unvisited_pois_file
        self.visited_pois_file = visited_pois_file
        self.discriminator = discriminator
        self.load_unvisited_pois()
        self.load_visited_pois()
        self.remove_visited_pois()
    
    def _greedy_sort(self, init_lat, init_lon, pois, cutoff = 3, minimum_poi = 1):
        poi_count = 0
        num_sorted = 0
        unsorted = deepcopy(pois)
        unsorted.sort(key=lambda a: a.distance)
        path = [unsorted.pop(0)]
        num_sorted += 1
        new_lat = path[-1].lat; new_lon = path[-1].lon
        self._update_poi_distances(new_lat, new_lon, unsorted)
        unsorted.sort(key=lambda a: a.distance)
        while(len(unsorted) > 0 and (len(path) < cutoff or poi_count < minimum_poi)):
            if unsorted[0].kind != 'Settlement': poi_count += 1
            path.append(unsorted.pop(0))
            num_sorted += 1
            new_lat = path[-1].lat
            new_lon = path[-1].lon
            self._update_poi_distances(new_lat, new_lon, unsorted)
            unsorted.sort(key=lambda a: a.distance)

        path = path + unsorted
        return path, num_sorted


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
    
    def remove_visited_pois(self):
        for v in self.visited_pois:
            if v in self.unvisited_pois:
                try:
                    self.unvisited_pois.remove(v)
                except ValueError:
                    pass
            #for u in self.unvisited_pois:

            

    def save_pois(self, pois, path):
        header = "Type,Name,Ident,Latitude,Longitude,Elevation,Magnetic Declination,Tags,Description".split(',')
        with open(f"{path}.tmp",'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            for p in pois:
                writer.writerow(p.to_list())
        if os.path.isfile(path):
            os.remove(path)
        os.rename(f"{path}.tmp", f"{path}")

    def save_unvisited_pois(self):
        self.save_pois(self.unvisited_pois, self.unvisited_pois_file)

    def save_visited_pois(self):
        self.save_pois(self.visited_pois, self.visited_pois_file)

    def _update_poi_distances(self, lat, lon, pois):
        for p in pois:
                distance = geopy.distance.distance((lat, lon), (p.lat, p.lon)).nm
                #if p.kind == "Settlement":
                #    distance += 11000
                p.distance = distance
                p.bearing = self._get_bearing(lat, lon, p.lat, p.lon)
        return
    
    def _sort_pois(self, pois, salesman = False):
        num_sorted = len(pois)
        if salesman:
            pois.sort(key=lambda a: a.distance)
            (pois, num_sorted) = self._greedy_sort(pois[0].lat, pois[0].lon, pois, self.config.closest_count)
        else:    
            pois.sort(key=lambda a: a.distance)
        return (pois, num_sorted)

    def get_nearest_unvisited_pois(self, lat, lon):
        self._update_poi_distances(lat, lon, self.unvisited_pois)
        (self.unvisited_pois, num_sorted) = self._sort_pois(self.unvisited_pois, self.config.traveling_salesman)
        #self.save_pois(self.unvisited_pois, 'total_path.csv')
        self._update_poi_distances(lat, lon, self.unvisited_pois)
        return self.unvisited_pois[0:max(self.config.closest_count, num_sorted)]
    
    def get_nearest_visited_pois(self, lat, lon):
        self._update_poi_distances(lat, lon, self.visited_pois)
        self._sort_pois(self.visited_pois)
        return self.visited_pois[0:self.config.closest_count]

    def is_poi_in_sight(self, poi):
        in_sight = False
        if poi.kind == "Settlement" and poi.distance < self.config.settlement_distance:
            in_sight = True
        elif poi.distance < self.config.max_distance:
            in_sight = True
        return in_sight


    def get_pois_in_sight(self, lat, lon):
        #self._update_poi_distances(lat, lon, self.unvisited_pois, self.config.traveling_salesman)
        pois = [p for p in self.unvisited_pois if self.is_poi_in_sight(p)]
        return pois
    
    def get_total_ordering(self, lat = None, lon = None):
        if lat != None and lon != None:
            self._update_poi_distances(lat, lon, self.unvisited_pois)
        return self._sort_pois(self.unvisited_pois, True)

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

def offline_main():
    config = PoiTrackerConfig('config.ini')
    config.closest_count = 9999
    pt = PoiTracker(None, config)
    x = pt.get_total_ordering(35.93454722222222, -79.06594166666666)
    pt.save_pois(x[0], 'total_path.csv')
    for p in x[0][0:config.closest_count]:
        print(p.to_list())
    
    sys.exit(0)

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
        sm = connect(retries = 3)
        if sm == None:
            offline_main()
        os.system("mode con: cols=65 lines=20")
        wrapper(main)
    except OSError:
        os.system("cls")
        print("Flight Simulator exited. Shutting down.")
        sys.exit()