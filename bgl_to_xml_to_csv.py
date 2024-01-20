import os
from pathlib import Path
import subprocess
import bs4
import sys
from poi import LnmUserpoint
import re
import logging

logging.basicConfig(level=logging.INFO)
msfsbgltoxml_path = os.path.expandvars("%USERPROFILE%/bin/msfsbglxml/MSFSBglXml.exe")
# msfs_packages_path =  os.path.expandvars("%USERPROFILE%/AppData/Local/Packages/Microsoft.FlightSimulator_8wekyb3d8bbwe/LocalCache/Packages/Official/")
msfs_packages_path =  os.path.expandvars("F:/MSFS2020_PACKAGES/Microsoft.FlightSimulator_8wekyb3d8bbwe/LocalCache/Packages/Official/")
xml_path =  os.path.expandvars("%USERPROFILE%/repos/github/msfs_poi_tracker/data_collection/xml")

# Just to make filenames unique
# counter=0
# os.makedirs(xml_path, exist_ok=True)
# for root,dirs,files in os.walk(msfs_packages_path):
#     files = []
#     for d in dirs:
#         path = f"{root}/{d}"
#         files = Path(path).glob('*.bgl')
#         for filename in files:
#             print(filename)
#             subprocess.call([msfsbgltoxml_path, "--bgl", f"{filename}", "--xml", f"{xml_path}/{counter}_{filename.name}.xml"] )
#             counter +=1

files = Path(xml_path).glob("*.xml")
pois = []
counter = 0
for filename in files:
    with open(filename, "r") as x:
        logging.debug(filename)
        soup = bs4.BeautifulSoup(x.read(), "xml")
        airports = soup.find_all("Airport")
        for a in airports:
            if "AIRPORT" not in a.attrs["name"].upper():
                ident = ""
                if len(a.find_all("Runway")) > 0:
                    logging.warning(f"Possible airport anomaly: f{a.attrs['name']}")
                    ident = a.attrs["ident"]
                # Manual fixes
                a.attrs["name"] = re.sub("Ch.teau", "Château", a.attrs["name"])
                a.attrs["name"] = re.sub("Napol.on", "Napoléon", a.attrs["name"])
                a.attrs["name"] = re.sub("V.zelay", "Vézelay", a.attrs["name"])
                a.attrs["name"] = re.sub("Loub.re", "Loubere", a.attrs["name"])
                a.attrs["name"] = re.sub("Qu.ribus", "Quéribus", a.attrs["name"])
                a.attrs["name"] = re.sub("V.lodrome", "Vélodrome", a.attrs["name"])
                a.attrs["name"] = re.sub("ifc mall", "IFC Mall", a.attrs["name"])
                a.attrs["name"] = re.sub(
                    "diavik.mine", "Diavik Diamond Mine", a.attrs["name"]
                )
                a.attrs["name"] = re.sub(
                    "palacio de deportes de Santander",
                    "Palacio de los Deportes de Santander",
                    a.attrs["name"],
                )
                a.attrs["name"] = re.sub(",", " -", a.attrs["name"])

                userpoint = LnmUserpoint(
                    kind="POI",
                    name=a.attrs["name"],
                    latitude=a.attrs["lat"],
                    longitude=a.attrs["lon"],
                    ident=ident,
                    tags="BGL2XML",
                    source_filename=filename,
                )
                logging.info({f"Adding {str(userpoint)}"})
                pois.append(userpoint)
                print(a.attrs["name"], a.attrs["lat"], a.attrs["lon"])
                # if "Cascade Dam" in a.attrs['name']:
                #     sys.exit()
                counter += 1
        # if "Cascade Dam" in str(soup):
        #     sys.exit()

with open("data_collection/bgl_to_xml_to_lnm.csv", "w") as w:
    w.writelines([str(p) + "\n" for p in pois])

print(counter)
