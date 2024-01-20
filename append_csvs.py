import os
import glob

data_files = glob.glob(
    os.path.expandvars("%OneDrive%/Little Navmap/MSFS POI Little Navmap v1.10/*.csv")
)
data_files.append("data_collection/kml_to_lnm.csv")
data_files.append("data_collection/bgl_to_xml_to_lnm.csv")

output = "thebigone.csv"

with open(output, "w") as o:
    for f in data_files:
        with open(f, "r") as i:
            print(f"Appending {f}")
            x = i.read()
            print(x)
            o.write(x)
