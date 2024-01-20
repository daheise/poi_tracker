import bs4
import regex

from poi import LnmUserpoint

soup = None
with open("data_collection\Microsoft Flight Simulator Map.kml") as x:
    soup = bs4.BeautifulSoup(x.read(), "xml")

# for each folder
# Get Name
# Select label based on folder name
# for each placemark in folder
# Get info from placemark
# Output placemark as CSV
skip_folders = ["temp", "Aquila Simulations Add-ons"]
folders_to_kinds = {
    "Hand Crafted Airports": "Airport",
    "World Updates (All Points of Interests)": "POI",
    "Points of Interest (Original)": "POI",
    "3D cities (Photogrammetry)": "Settlement",
    "Default": "POI"
}

pois = []
name_regex = regex.compile("((CU ?# ?|WU ?# ?)\d+:?)?(GOTY Ed -)?(.*)")
userpoints = []
for f in soup.find_all("Folder"):
    folder_name = f.find("name").get_text()
    if folder_name in skip_folders:
        continue
    print(f"{folder_name} = {folders_to_kinds[folder_name]}")
    for p in f.find_all("Placemark"):
        # print(p.find('name').get_text())
        #print(name_regex.split(p.find('name').get_text()))
        matches = name_regex.match(p.find("name").get_text())
        try:
            ident = p.find("description").get_text().replace("ICAO: ","")[0:4]
            if "<" in ident:
                ident = ""

        except AttributeError:
            ident =""
        n = matches[-1].strip().replace(",", "-")
        c = p.Point.coordinates.get_text().strip().split(",")
        region = ""
        for m in matches[1:3]:
            if m is not None:
                if len(region) == 0:
                    region = m
                else:
                    region = f"{region} - {m}"
        userpoints.append(
            LnmUserpoint(
                name=n,
                ident=ident,
                region=region,
                latitude=c[1],
                longitude=c[0],
                kind=folders_to_kinds[folder_name],
                tags="KML2LNM",
            )
        )

with open("kml_to_lnm.csv", "w") as output:
    for u in userpoints:
        output.writelines(str(u) + "\n")
    # with open("data/errata.csv", "r") as er:
    #    er.readline()
    #    app = er.read()
    #    output.write(app)


print("Don't die")
