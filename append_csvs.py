import os
import glob

data_files = glob.glob(
    os.path.expandvars("%OneDrive%/Little Navmap/MSFS POI Little Navmap v1.7/*.csv")
)
data_files.append("bgl_to_xml_to_lnm.csv")
data_files.append("kml_to_lnm.csv")

output = "thebigone.csv"

with open(output, "w") as o:
    for f in data_files:
        with open(f, "r") as i:
            print(f"Appending {f}")
            o.write(i.read())
