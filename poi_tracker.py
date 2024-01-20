from math import nan, radians, sin, cos, atan2, degrees
import os
import csv
import sys
import logging
import geopy
import pyttsx3
import networkx as nx
from networkx.algorithms import approximation as approx
import re
import sqlite3 as sql
import pandas as pd
from copy import deepcopy
from time import sleep
from lib.koseng.simconnect_mobiflight import SimConnectMobiFlight
from SimConnect import AircraftEvents
from config import PoiTrackerConfig

from flight_parameters import FlightDataMetrics, SightseeingDiscriminator
from poi_curses import PoiCurses

from poi import LnmUserpoint, Poi

logging.basicConfig(level=logging.DEBUG)


class PoiTracker:
    def __init__(
        self,
        discriminator: SightseeingDiscriminator,
        config: PoiTrackerConfig,
        unvisited_pois_file=os.path.expandvars(
            "%APPDATA%/poi_tracker/data/unvisited_pois.csv"
        ),
        visited_pois_file=os.path.expandvars(
            "%APPDATA%/poi_tracker/data/visited_pois.csv"
        ),
    ):
        self.config = config
        self.unvisited_pois_file = unvisited_pois_file
        self.visited_pois_file = visited_pois_file
        self.discriminator = discriminator
        self.load_unvisited_pois()
        self.load_visited_pois()
        self.remove_duplicate_pois()
        self.remove_visited_pois()
        self.cur_lat = self.unvisited_pois[0].lat
        self.cur_lon = self.unvisited_pois[0].lon
        self.prev_lat = 0
        self.prev_lon = 0
        self.have_total_order = False

    def _mlrose_sort(self, pois, cutoff=28):
        cutoff = len(pois)
        import six
        import numpy as np

        sys.modules["sklearn.externals.six"] = six
        import mlrose

        dist_list = []
        sort_these = pois[0:cutoff]
        unsorted = pois[cutoff:]
        for i in range(0, len(sort_these) - 1):
            for j in range(i + 1, len(sort_these)):
                d = geopy.distance.great_circle(
                    (sort_these[i].lat, sort_these[i].lon),
                    (sort_these[j].lat, sort_these[j].lon),
                ).nm
                if d == 0:
                    logging.warning(
                        f"Weird, ({i}, {j} = {d}). Pois are {str(pois[i])} and {str(pois[j])}"
                    )
                    d = 0.00001
                t = (i, j, d)

                dist_list.append(t)
        # fitness_dists = mlrose.TravellingSales(distances = dist_list)
        # problem_fit = mlrose.TSPOpt(length = len(sort_these), fitness_fn = fitness_dists, maximize= False)
        problem_fit = mlrose.TSPOpt(
            length=len(sort_these), distances=dist_list, maximize=False
        )
        # best_state, best_fitness = mlrose.genetic_alg(problem_fit, random_state = 2)
        best_state, best_fitness = mlrose.random_hill_climb(
            problem_fit,
            init_state=np.arange(len(pois)),
            max_iters=6,
            max_attempts=6,
            random_state=2,
        )
        # best_state, best_fitness = mlrose.mimic(problem_fit, max_iters = 3, random_state = 2, fast_mimic=True)
        best_order = [sort_these[i] for i in best_state] + unsorted
        return (best_order, len(sort_these))

    def _scipy_mst(self, pois, cutoff=28):
        cutoff = len(pois)
        import scipy

        graph = [[nan] * len(pois) for _ in range(len(pois))]
        sort_these = pois
        logging.debug("start")
        for i in range(0, len(sort_these)):
            for j in range(i + 1, len(sort_these)):
                d = int(
                    geopy.distance.great_circle(
                        (sort_these[i].lat, sort_these[i].lon),
                        (sort_these[j].lat, sort_these[j].lon),
                    ).ft
                )
                if d < 1:
                    logging.warning(
                        f"Weird, ({i}, {j} = {d}). Pois are {str(sort_these[i])} and {str(sort_these[j])}"
                    )
                    d = 1
                graph[i][j] = d
                graph[j][i] = d

        logging.debug(graph[0][0], graph[0][-1])
        logging.debug(graph[-1][0], graph[-1][-1])
        cgraph = scipy.sparse.csgraph.csgraph_from_dense(graph)
        tree = scipy.sparse.csgraph.minimum_spanning_tree(cgraph, overwrite=True)
        (path, _) = scipy.sparse.csgraph.breadth_first_order(tree, 0, directed=False)
        # path = scipy.sparse.csgraph.shortest_path(tree, directed = False)
        best_order = [sort_these[i] for i in path]
        return (best_order, len(sort_these))

    def _networkx_greedy_tsp(self):
        G = nx.Graph()

        # The point of this algorithm is to find a total path,
        # so collect everything
        # sort_these = self.unvisited_pois
        sort_these = self.unvisited_pois + self.visited_pois
        # Arbitrary but consistent sort to stabilize the path finding algorithm
        # This one just made the map I like best.
        sort_these.sort(key=lambda a: f"{a.lon}{a.lat}{a.name}")
        # If there is a start poi configured, use it
        for i in range(0, len(sort_these)):
            if self.config.start_poi in sort_these[i].name:
                s = sort_these.pop(i)
                sort_these = [s] + sort_these
                break

        logging.debug("start")
        for i in range(0, len(sort_these)):
            G.add_node(
                i, name=sort_these[i].name, lat=sort_these[i].lat, lon=sort_these[i].lon
            )
        for i in range(0, len(sort_these)):
            for j in range(i + 1, len(sort_these)):
                d = int(
                    geopy.distance.great_circle(
                        (sort_these[i].lat, sort_these[i].lon),
                        (sort_these[j].lat, sort_these[j].lon),
                    ).ft
                )
                G.add_edge(i, j, weight=d)
        nx_path = approx.greedy_tsp(G)
        nx_path.pop(len(nx_path) - 1)
        logging.debug(nx_path)
        best_order = [sort_these[i] for i in nx_path]

        # for v in self.visited_pois:
        #     try:
        #         best_order.remove(v)
        #         print(f"Removing {v} because we have already been there.")
        #     except ValueError:
        #         pass

        # minimum_distance = 10819.389
        # closest_poi = None
        # for p in best_order:
        #     d = geopy.distance.great_circle((self.cur_lat, self.cur_lon), (p.lat, p.lon)).nm
        #     if d < minimum_distance:
        #         closest_poi = p
        #         minimum_distance = d
        # idx = best_order.index(closest_poi)
        # best_order = best_order[idx:] + best_order[0:idx]
        return (best_order, len(sort_these))

    def _networkx_tsp(self):
        G = nx.Graph()

        # The point of this algorithm is to find a total path,
        # so collect everything
        # sort_these = self.unvisited_pois
        #sort_these = self.unvisited_pois  + self.visited_pois
        #random.shuffle(sort_these)
        # Arbitrary but consistent sort to stabilize the path finding algorithm
        # Put our finger on the scale to encourage POIs near each other to be considered nearby in iterations
        (sort_these, _) = self._networkx_greedy_tsp()

        logging.debug("start")
        for i in range(0, len(sort_these)):
            G.add_node(
                i, name=sort_these[i].name, lat=sort_these[i].lat, lon=sort_these[i].lon
            )
        for i in range(0, len(sort_these)):
            for j in range(i + 1, len(sort_these)):
                d = int(
                    geopy.distance.great_circle(
                        (sort_these[i].lat, sort_these[i].lon),
                        (sort_these[j].lat, sort_these[j].lon),
                    ).ft
                )
                G.add_edge(i, j, weight=d)
        nx_path = approx.christofides(G)
        nx_path.pop(len(nx_path) - 1)
        logging.debug(nx_path)
        best_order = [sort_these[i] for i in nx_path]

        for v in self.visited_pois:
            try:
                best_order.remove(v)
                logging.info(f"Removing {v} because we have already been there.")
            except ValueError:
                pass

        # minimum_distance = 10819.389
        # closest_poi = None
        # for p in best_order:
        #     if (self.config.next_poi_override in p.name):
        #         closest_poi = p
        #         break
        #     d = geopy.distance.great_circle(
        #         (self.cur_lat, self.cur_lon), (p.lat, p.lon)
        #     ).nm
        #     if d < minimum_distance:
        #         closest_poi = p
        #         minimum_distance = d
        # idx = best_order.index(closest_poi)
        # best_order = best_order[idx:] + best_order[0:idx]
        return (best_order, len(sort_these))

    def _greedy_sort(self, cutoff=3, minimum_poi=1):
        saved_lat = self.cur_lat
        saved_lon = self.cur_lon
        poi_count = 0
        num_sorted = 0
        unsorted = self.unvisited_pois
        unsorted.sort(key=lambda a: a.distance)
        path = [unsorted.pop(0)]
        num_sorted += 1
        self.cur_lat = path[-1].lat
        self.cur_lon = path[-1].lon
        self._update_poi_distances()
        unsorted.sort(key=lambda a: a.distance)
        while len(unsorted) > 0 and (len(path) < cutoff or poi_count < minimum_poi):
            if unsorted[0].kind != "Settlement":
                poi_count += 1
            path.append(unsorted.pop(0))
            num_sorted += 1
            self.cur_lat = path[-1].lat
            self.cur_lon = path[-1].lon
            self._update_poi_distances()
            unsorted.sort(key=lambda a: a.distance)

        self.unvisited_pois = path + unsorted
        self.cur_lat = saved_lat
        self.cur_lon = saved_lon
        self._update_poi_distances()
        return self.unvisited_pois, num_sorted

    def _get_bearing(self, lat1, lon1, lat2, lon2):
        lat1 = radians(lat1)
        lon1 = radians(lon1)
        lat2 = radians(lat2)
        lon2 = radians(lon2)
        dLon = lon2 - lon1
        x = cos(lat2) * sin(dLon)
        y = (cos(lat1) * sin(lat2)) - (sin(lat1) * cos(lat2) * cos(dLon))
        brng = degrees(atan2(x, y))
        if brng < 0:
            brng += 360
        return brng

    def load_pois(self, path):
        pois = []
        with open(path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                poi = Poi(LnmUserpoint.from_lnm_list(row))
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
                    logging.info(f"Removing {v} because we have already been there.")
                    self.unvisited_pois.remove(v)
                except ValueError:
                    pass
            # for u in self.unvisited_pois:

    def _is_reasonable_name(self, needle):
        return (
            re.search("[A-Z]", needle) is not None
            and re.search("[a-z]", needle) is not None
        )

    def remove_duplicate_pois(self):
        duplicates = []
        for i in range(0, len(self.unvisited_pois)):
            j = -1
            try:
                #j = self.unvisited_pois[i + 1 :].index(self.unvisited_pois[i])
                j = self.unvisited_pois.index(self.unvisited_pois[i], i+1)
            except ValueError:
                pass
            if j > -1:
                logging.warning(
                    f"{self.unvisited_pois[i]} is duplicated at {j} as {self.unvisited_pois[j]}."
                )
                duplicates.append(
                    (self.unvisited_pois[i], self.unvisited_pois[j])
                )

            # else:
            #     new_list.append(self.unvisited_pois[i])
        for d in duplicates:
            if self._is_reasonable_name(d[0].name) and self._is_reasonable_name(
                d[1].name
            ):
                winner = int(len(d[1].name) > len(d[0].name))
                loser = int(not bool(winner))
                while d[loser] in self.unvisited_pois:
                    logging.debug(f"Removing {str(d[loser])}")
                    self.unvisited_pois.remove(d[loser])
                if d[winner] not in self.unvisited_pois:
                    logging.debug(f"Appending {str(d[winner])}")
                    self.unvisited_pois.append(d[winner])
            elif not self._is_reasonable_name(d[0].name) and self._is_reasonable_name(
                d[1].name
            ):
                while d[0] in self.unvisited_pois:
                    logging.debug(f"Removing {str(d[0])}")
                    self.unvisited_pois.remove(d[0])
                if d[1] not in self.unvisited_pois:
                    logging.debug(f"Appending {str(d[1])}")
                    self.unvisited_pois.append(d[1])
            else:
                while d[1] in self.unvisited_pois:
                    logging.debug(f"Removing {str(d[1])}")
                    self.unvisited_pois.remove(d[1])
                if d[0] not in self.unvisited_pois:
                    logging.debug(f"Appending {str(d[0])}")
                    self.unvisited_pois.append(d[0])

        # [new_list.append(x) for x in self.unvisited_pois if x not in new_list]
        # if len(new_list) != len(self.unvisited_pois):
        # print(f"Removed {len(self.unvisited_pois) - len(new_list)} duplicates.")
        logging.info(f"Removed {len(duplicates)} duplicates.")
        # self.unvisited_pois = new_list

    def save_pois(self, pois, path):
        header = "Type,Name,Ident,Latitude,Longitude,Elevation,Magnetic Declination,Tags,Description,Region,Visible From,Last Edit,Import Filename".split(
            ","
        )
        with open(f"{path}.tmp", "w", newline="") as csvfile:
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

    def _update_poi_distances(self):
        if self.prev_lat == self.cur_lat and self.prev_lon == self.cur_lon:
            return
        for p in self.unvisited_pois + self.visited_pois:
            distance = geopy.distance.great_circle(
                (self.cur_lat, self.cur_lon), (p.lat, p.lon)
            ).nm
            # if p.kind == "Settlement":
            #    distance += 11000
            p.distance = distance
            p.bearing = self._get_bearing(self.cur_lat, self.cur_lon, p.lat, p.lon)
        self.prev_lat = self.cur_lat
        self.prev_lon = self.cur_lon
        return

    def _sort_pois(self, pois, salesman=False):
        num_sorted = 0
        if salesman:
            # pois.sort(key=lambda a: a.distance)
            if self.config.networkx and not self.have_total_order:
                (pois, num_sorted) = self._networkx_tsp()
            else:
                (pois, num_sorted) = self._greedy_sort(
                    self.config.closest_count, self.config.minimum_poi
                )
            # (pois, num_sorted) = self._scipy_mst(
            #     pois, self.config.closest_count
            # )
        else:
            pois.sort(key=lambda a: a.distance)
        return (pois, num_sorted)

    def get_next_unvisited_pois(self):
        self._update_poi_distances()
        return self.unvisited_pois[0 : self.config.closest_count]

    def get_next_visited_pois(self):
        self._update_poi_distances()
        return self.visited_pois[0 : self.config.closest_count]

    def get_nearest_unvisited_pois(self):
        self._update_poi_distances()
        (self.unvisited_pois, num_sorted) = self._sort_pois(
            self.unvisited_pois, self.config.traveling_salesman
        )
        return self.unvisited_pois[0 : max(self.config.closest_count, num_sorted)]

    def get_nearest_visited_pois(self):
        self._update_poi_distances()
        self._sort_pois(self.visited_pois)
        return self.visited_pois[0 : self.config.closest_count]

    def is_poi_within(self, poi, distance):
        return poi.distance < distance

    def get_pois_in_render_distance(self):
        unvisited = [
            p
            for p in self.unvisited_pois
            if self.is_poi_within(p, self.config.poi_render_distance)
        ]
        visited = [
            p
            for p in self.visited_pois
            if self.is_poi_within(p, self.config.poi_render_distance)
        ]
        return (unvisited, visited)

    def get_pois_in_sight(self):
        unvisited = [
            p
            for p in self.unvisited_pois
            if self.is_poi_within(
                p,
                self.config.settlement_distance
                if p.kind == "Settlement"
                else self.config.max_distance,
            )
        ]
        visited = [
            p
            for p in self.visited_pois
            if self.is_poi_within(p, self.config.settlement_distance)
        ]
        return (unvisited, visited)

    def get_pois_in_render(self):
        unvisited = [
            p
            for p in self.unvisited_pois
            if self.is_poi_within(p, self.config.settlement_distance)
        ]
        visited = [
            p
            for p in self.visited_pois
            if self.is_poi_within(p, self.config.settlement_distance)
        ]
        return (unvisited, visited)

    def get_total_path_distance(self, pois):
        d = geopy.distance.great_circle(
                (self.cur_lat, self.cur_lon), (pois[0].lat, pois[0].lon)
            ).nm
        for i in range(0, len(pois)-1):
            d += geopy.distance.great_circle(
                (pois[i].lat, pois[i].lon), (pois[i+1].lat, pois[i+1].lon)
            ).nm
        return d

    def set_first_poi(self):
        self._update_poi_distances()
        distances = []
        tmp = deepcopy(self.unvisited_pois)
        for i in range(0, len(self.unvisited_pois)):
            distances.append(self.get_total_path_distance(tmp))
            tmp = tmp[1:] + [tmp[0]]
        assert(len(distances) == len(self.unvisited_pois))
        m = min(distances)
        idx = distances.index(m)

        #next = min(self.unvisited_pois, key=lambda p: p.distance)
        #idx = self.unvisited_pois.index(next)
        tmp = self.unvisited_pois[idx:] + self.unvisited_pois[0:idx]
        assert(len(tmp) == len(self.unvisited_pois))
        self.unvisited_pois = tmp
        print(self.get_total_path_distance(self.unvisited_pois))
        pass

    def get_total_ordering(self):
        logging.debug("Starting total ordering")
        old_count = self.config.closest_count
        self.config.closest_count = 9999
        self._update_poi_distances()
        (self.unvisited_pois, count) = self._sort_pois(self.unvisited_pois, True)
        self.config.closest_count = old_count
        self.have_total_order = True
        self.set_first_poi()
        
        return (self.unvisited_pois, count)

    def remove_pois(self, pois=[]):
        if len(pois) == 0:
            return
        for p in pois:
            self.unvisited_pois.remove(p)
            self.visited_pois.append(p)
        self.save_visited_pois()
        self.save_unvisited_pois()

    def set_location(self, lat, lon):
        self.cur_lat = lat
        self.cur_lon = lon
        return (self.cur_lat, self.cur_lon)


def connect(retries=999):
    connected = False
    sm = None
    i = 0
    while not connected and i < retries:
        i += 1
        try:
            sm = SimConnectMobiFlight()  # SimConnect()
            connected = True
        except KeyboardInterrupt:
            quit()
        except ConnectionError as e:
            # ui.write_message(type(e).__name__, e)
            sleep(i)
    return sm


def offline_main():
    config = PoiTrackerConfig("config.ini")
    config.closest_count = 9999
    pt = PoiTracker(None, config)
    if (
        os.path.exists(
            os.path.expandvars(
                "%APPDATA%\ABarthel\little_navmap_db\little_navmap_logbook.sqlite"
            )
        )
        and config.use_lnm == True
    ):


        con = sql.connect(
            os.path.expandvars(
                "%APPDATA%\ABarthel\little_navmap_db\little_navmap_logbook.sqlite"
            )
        )
        # cur = con.cur()
        # cur.execute("SELECT * FROM LOGBOOK WHERE description LIKE '%WT L%' ORDER BY departure_time DESC")
        df_flight_paths = pd.read_sql_query(
            "SELECT * FROM LOGBOOK WHERE description LIKE '%WT L%' ORDER BY departure_time DESC",
            con,
        )
        logging.debug(df_flight_paths["destination_lonx"].head(5))
        logging.debug(df_flight_paths["destination_laty"].head(5))
        start_lon = df_flight_paths["destination_lonx"][0]
        start_lat = df_flight_paths["destination_laty"][0]
    else:
        start = pt.unvisited_pois[0]
        start_lat = start.lat
        start_lon = start.lon
    pt.set_location(start_lat, start_lon)
    x = pt.get_total_ordering()
    pt.save_pois(
        x[0], os.path.expandvars("%APPDATA%/poi_tracker/data/unvisited_pois.csv")
    )
    # for p in x[0][0 : config.closest_count]:
    #    print(p.to_list())
    total_distance = 0
    max_leg = 0
    for i in range(0, len(x[0]) - 1):
        d = geopy.distance.great_circle(
            (x[0][i].lat, x[0][i].lon), (x[0][i + 1].lat, x[0][i + 1].lon)
        ).nm
        total_distance += d
        max_leg = max(max_leg, d)
    print(total_distance, max_leg, len(x[0]))



# Defining main function
def main(stdscr):
    stdscr.nodelay(True)
    ui = PoiCurses(stdscr)
    config = PoiTrackerConfig("config.ini")
    sm = connect()
    ae = AircraftEvents(sm)
    refuel = ae.find("REPAIR_AND_REFUEL")

    flight_data = FlightDataMetrics(sm, config)
    discriminator = SightseeingDiscriminator(flight_data, config)
    pt = PoiTracker(discriminator, config)
    tts_engine = pyttsx3.init()
    flight_data.update()
    pt.set_location(flight_data.location[0], flight_data.location[1])
    if config.traveling_salesman and not config.networkx:
        pt.get_total_ordering()
        pt.save_unvisited_pois()
    elif config.traveling_salesman and config.networkx:
        pt.have_total_order = True
    seen_this_execution = []

    while True:
        flight_data.update()
        pt.set_location(flight_data.location[0], flight_data.location[1])
        nuv = []
        nv = []
        if pt.have_total_order:
            nuv = pt.get_next_unvisited_pois()
        else:
            nuv = pt.get_nearest_unvisited_pois()
        nv = pt.get_nearest_visited_pois()
        (unvisited, visited) = pt.get_pois_in_sight()
        ui.write_agl(flight_data.agl)
        ui.write_ground_speed(flight_data.ground_speed)
        ui.write_closest_unvisited_pois(nuv)
        ui.write_closest_visited_pois(nv)
        ui.update()
        for p in unvisited:
            tts_engine.say(f"Have {p.name} in sight.")
            tts_engine.runAndWait()
            pt.remove_pois([p])

        (unvisited, visited) = pt.get_pois_in_render_distance()
        for p in unvisited + visited:
            if p not in seen_this_execution:
                normal_rate = tts_engine.getProperty("rate")
                tts_engine.setProperty("rate", normal_rate // 4)
                tts_engine.say(f"{config.render_annunciation} {p.name}")
                tts_engine.runAndWait()
                tts_engine.setProperty("rate", normal_rate)
                tts_engine.runAndWait()
                seen_this_execution.append(p)
        refuel()
        sleep(config.update_speed)


if __name__ == "__main__":
    from curses import wrapper

    try:
        sm = connect(retries=3)
        if sm == None:
            offline_main()
            logging.info("Creating total order.")
        
        os.system("mode con: cols=65 lines=20")
        wrapper(main)
    except OSError:
        os.system("cls")
        logging.critical("Flight Simulator exited. Shutting down.")
        sys.exit()
    except KeyboardInterrupt:
        os.system("cls")
        sys.exit()
