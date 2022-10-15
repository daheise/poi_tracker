import configparser


class PoiTrackerConfigError(Exception):
    pass


class PoiTrackerConfig:
    def __init__(self, file=None):
        if file is None:
            self.max_agl = 3000  # ft
            self.max_speed = 200  # knots
            self.max_distance = 1  # nm
            self.annunciation = False
            self.update_speed = 5
            self.closest_count = 3
            self.start_poi = ""
        else:
            self._config = configparser.ConfigParser()
            self._config.read("config.ini")
            if self._config.sections() == []:
                raise PoiTrackerConfigError

            self.annunciation = self._config.getboolean("features", "annunciation")
            self.networkx = self._config.getboolean("features", "networkx")
            self.use_lnm = self._config.getboolean("features", "use_lnm")
            self.traveling_salesman = self._config.getboolean(
                "features", "traveling_salesman"
            )
            self.minimum_poi = int(self._config.get("features", "minimum_poi"))
            self.update_speed = int(self._config.get("features", "update_speed"))
            self.closest_count = int(self._config.get("features", "closest_count"))
            self.max_agl = int(self._config.get("restrictions", "max_agl"))  # ft
            self.max_speed = int(self._config.get("restrictions", "max_speed"))  # knots
            self.max_distance = float(
                self._config.get("restrictions", "max_distance")
            )  # nm
            self.settlement_distance = float(
                self._config.get("restrictions", "settlement_distance")
            )  # nm
            self.poi_render_distance = float(
                self._config.get("restrictions", "poi_render_distance")
            )
            self.render_annunciation = self._config.get(
                "restrictions", "render_annunciation"
            )
            self.start_poi = self._config.get("networkx", "start_poi")
            self.next_poi_override = self._config.get("networkx", "next_poi_override")
