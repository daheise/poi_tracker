# Rudimentary bgl reader
import io
import os
from pathlib import Path
from sre_constants import SUCCESS

landmark_header = bytearray.fromhex("00ea")


def parse_landmark(bgl):
    SUCCESS = False
    endian = "big"
    signed = False
    recType = landmark_header
    recSz = int.from_bytes(bgl.read(4), byteorder=endian, signed=signed)
    # guid = int.from_bytes(bgl.read(16), byteorder=endian, signed=signed)
    # lon = int.from_bytes(bgl.read(4), byteorder=endian, signed=signed) * (360.0 / (3 * 0x10000000)) - 180.0
    # lat = 90.0 - int.from_bytes(bgl.read(4), byteorder=endian, signed=signed) * (180.0 / (2 * 0x10000000))
    # alt = int.from_bytes(bgl.read(4), byteorder=endian, signed=signed)
    # nameLen = int.from_bytes(bgl.read(1), byteorder=endian, signed=signed)
    # typeLen = int.from_bytes(bgl.read(1), byteorder=endian, signed=signed)
    # ownerLen = int.from_bytes(bgl.read(1), byteorder=endian, signed=signed)
    # try:
    #     if(nameLen > 0 and typeLen > 0 and ownerLen > 0 and abs(lon) <= 180 and abs(lat) <= 90):
    #         name = bgl.read(nameLen).decode('utf-8')
    #         _type = bgl.read(typeLen).decode('utf-8')
    #         owner = bgl.read(ownerLen).decode('utf-8')
    #     print(name, _type, owner)
    #     print(recType, recSz, guid, lon, lat, alt, nameLen, typeLen, ownerLen)
    # except:
    #     pass
    if recSz > (2 << 24):
        return False
    try:
        record = bgl.read(recSz).decode("utf-8")
        print(record)
    except:
        pass
    return False

for root, dirs, files in os.walk(
    os.path.expandvars("%USERPROFILE%/AppData/Local/Packages/Microsoft.FlightSimulator_8wekyb3d8bbwe/LocalCache/Packages")
):
    files = []
    for d in dirs:
        path = f"{root}/{d}"
        files = Path(path).glob("*.bgl")
    for filename in files:
        print(filename)
        bgl = open(filename, mode="rb")
        haystack = bytearray(bgl.read(2))
        count = 0
        pos = -1
        end = bgl.seek(0, io.SEEK_END)
        bgl.seek(0)
        while pos < end:  # haystack != bytearray():
            if haystack == landmark_header:
                count += 1
                pos = bgl.tell()
                parse_landmark(bgl)
                bgl.seek(pos + 1)
            haystack.pop(0)
            while len(haystack) < 2:
                haystack += bytearray(bgl.read(1))
        print(count)
        bgl.close()
