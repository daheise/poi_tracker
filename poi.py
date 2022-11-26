from unidecode import unidecode
import geopy
import re
import string
import zlib

def strip_cruft(needle):
    needle = unidecode(needle)
    punc = "!#$%&'()*+,-./:;<=>?@[\]^_`{|}~\s"
    needle = re.sub(f"[{punc}]", "", needle)
    return needle

#   0   1     2       4       5          6              6             7     8          9        10          11         12
# Type,Name,Ident,Latitude,Longitude,Elevation,Magnetic Declination,Tags,Description,Region,Visible From,Last Edit,Import Filename
class LnmUserpoint:
    def __init__(
        self,
        name,
        latitude,
        longitude,
        kind="",
        ident="",
        elevation="",
        tags="",
        description="",
        region="",
        visibility="",
        source_filename="",
    ) -> None:
        self.name = name
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.kind = kind
        if len(ident) == 0:
            self.ident = strip_cruft(self.name).upper()[0:5]
        else:
            self.ident = ident
        sfx = self._custom_suffix()
        if sfx not in ident:
            self.ident += sfx
        self.elevation = elevation
        self.tags = tags
        self.description = description
        self.region = region
        self.visibility = visibility
        self.source_filename = source_filename

    def _custom_suffix(self):
        adder = string.ascii_uppercase + "0123456789"
        # Just for fun to make the number more random
        idx = zlib.adler32(bytes(self.name, encoding="utf-8")) % len(adder)
        return "U" + self.kind[0] + adder[idx]
    

    @classmethod
    def from_lnm_list(cls, items):
        while len(items) < 13:
            items.append("")
        return cls(
            name=items[1],
            latitude=items[3],
            longitude=items[4],
            kind=items[0],
            ident=items[2],
            elevation=items[5],
            tags=items[7],
            description=items[8],
            region=items[9],
            visibility=items[10],
            source_filename=items[12],
        )

    @classmethod
    def from_lnm_csv(cls, str):
        items = str.split(",")
        while len(items) < 13:
            items.append("")
        return cls(
            name=items[1],
            latitude=items[3],
            longitude=items[4],
            kind=items[0],
            ident=items[2],
            elevation=items[5],
            tags=items[7],
            description=items[8],
            region=items[9],
            visibility=items[10],
            source_filename=items[12],
        )

    def __str__(self) -> str:
        return f"{self.kind},{self.name},{self.ident},{self.latitude},{self.longitude},{self.elevation},,{self.tags},{self.description},{self.region},{self.visibility},,{self.source_filename}"


class Poi:
    # def __init__(self, kind, name, lat, lon, description):
    #     self.userpoint = LnmUserpoint(name=name, kind=kind, name=name, latitude=lat, longitude=lon, description=description)
    #     self.distance = 10819.389  # Half the circumference of Earth
    #     self.bearing = 0

    def __init__(self, userpoint: LnmUserpoint) -> None:
        self.userpoint = userpoint
        self.distance = 10819.389  # Half the circumference of Earth
        self.bearing = 0

    def to_list(self):
        # This format matches LNM's userpoint CSV
        return str(self.userpoint).split(",")

    def __str__(self):
        return f"Poi(LnmUserpoint({self.userpoint}), {self.distance}, {self.bearing})"

    def _get_comparable_name(self, name):
        name = unidecode(name).lower()
        punc = "!#$%&'()*+,-./:;<=>?@[\]^_`{|}~\s"
        name = re.sub(f"[{punc}]", "", name)
        return name

    def __hash__(self):
        name = self._get_comparable_name(self.name)
        return hash(
            f"{name}{self.userpoint.latitude}{self.userpoint.longitude}{self.userpoint.kind}"
        )

    def __eq__(self, other):
        tmp_name = self._get_comparable_name(self.name)
        tmp_other_name = self._get_comparable_name(other.name)
        distance = geopy.distance.great_circle(
            (self.lat, self.lon), (other.lat, other.lon)
        )

        same_kind = True
        # We only really care about kindedness if one is a settlement
        same_kind = self.userpoint.kind == other.userpoint.kind
        equivalent_kinds = ["POI", "Building", "Lighthouse", "Location"]
        same_kind = same_kind or (
            self.userpoint.kind in equivalent_kinds
            and other.userpoint.kind in equivalent_kinds
        )

        return (
            same_kind
            and (
                (tmp_name.startswith(tmp_other_name))
                or (tmp_other_name.startswith(tmp_name))
            )
            and distance.ft < 3000
        ) or distance.ft < 100

    @property
    def name(self):
        return self.userpoint.name

    @property
    def lat(self):
        return self.userpoint.latitude

    @property
    def lon(self):
        return self.userpoint.longitude

    @property
    def kind(self):
        return self.userpoint.kind
