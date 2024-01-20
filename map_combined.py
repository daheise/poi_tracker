from math import ceil
import os
import plotly.graph_objects as go
import pandas as pd
import sqlite3 as sql
import poi_tracker
from time import time

line_width = 4
marker_size = line_width + 2
start_pathing = time()
#poi_tracker.offline_main()
end_pathing = time()

start_plotting = time()
fig = go.Figure()

con = sql.connect(
    os.environ["APPDATA"] + "\ABarthel\little_navmap_db\little_navmap_logbook.sqlite"
)
# cur = con.cur()
# cur.execute("SELECT * FROM LOGBOOK WHERE description LIKE '%WT L%' ORDER BY departure_time DESC")
df_flight_paths = pd.read_sql_query(
    "SELECT * FROM LOGBOOK WHERE description LIKE '%WT L%' ORDER BY departure_time ASC",
    con,
)
print(df_flight_paths["departure_ident"].head(5))

fpl_string = [
    dep + " - " + dest
    for dep, dest in zip(
        df_flight_paths["departure_ident"], df_flight_paths["destination_ident"]
    )
]

oldest_color = (255, 255, 255)
newest_color = (119, 136, 153)
diff = (
    newest_color[0] - oldest_color[0],
    newest_color[1] - oldest_color[1],
    newest_color[2] - oldest_color[2],
)
max_denominator = min(max([abs(d) for d in diff]), len(df_flight_paths))
change = (diff[0] / max_denominator,
        diff[1] / max_denominator,
        diff[2] / max_denominator
        )

color = oldest_color
for i in range(0, len(df_flight_paths)):
    fig.add_trace(
        go.Scattergeo(
            locationmode="USA-states",
            lon=[
                df_flight_paths["departure_lonx"][i],
                df_flight_paths["destination_lonx"][i],
            ],
            lat=[
                df_flight_paths["departure_laty"][i],
                df_flight_paths["destination_laty"][i],
            ],
            mode="lines+markers",
            line=dict(width=line_width + 1, color="black"),
            # line = dict(width = 2,color = 'rgb(160,160,164)'),
            marker=dict(size=marker_size + 1),
            # opacity = max(0.5 ,i/len(df_flight_paths))
            # opacity = float(df_flight_paths['cnt'][i]) / float(df_flight_paths['cnt'].max()),
        )
    )
#for i in range(0, len(df_flight_paths)):
    fig.add_trace(
        go.Scattergeo(
            locationmode="USA-states",
            lon=[
                df_flight_paths["departure_lonx"][i],
                df_flight_paths["destination_lonx"][i],
            ],
            lat=[
                df_flight_paths["departure_laty"][i],
                df_flight_paths["destination_laty"][i],
            ],
            mode="lines+markers",
            text=[
                df_flight_paths["departure_ident"][i],
                df_flight_paths["destination_ident"][i],
            ],  # fpl_string[i],
            line=dict(width=line_width, color=f"rgb({color[0]},{color[1]},{color[2]})"),
            # line = dict(width = 2,color = 'rgb(160,160,164)'),
            marker=dict(size=marker_size)
            # opacity = max(0.5 ,i/len(df_flight_paths))
            # opacity = float(df_flight_paths['cnt'][i]) / float(df_flight_paths['cnt'].max()),
        )
    )
    
    if i > max_denominator:
        color = newest_color
    else:
        color = (
            color[0] + change[0],
            color[1] + change[1],
            color[2] + change[2],
        )
# Most recent leg
# fig.add_trace(
#         go.Scattergeo(
#             locationmode = 'USA-states',
#             lon = [df_flight_paths['departure_lonx'][len(df_flight_paths)-1], df_flight_paths['destination_lonx'][len(df_flight_paths)-1]],
#             lat = [df_flight_paths['departure_laty'][len(df_flight_paths)-1], df_flight_paths['destination_laty'][len(df_flight_paths)-1]],
#             mode = 'lines+markers',
#             text = fpl_string[-1],
#             line = dict(width = 2,color = 'deeppink'),
#             marker=dict(size=3),
#             #opacity = float(df_flight_paths['cnt'][i]) / float(df_flight_paths['cnt'].max()),
#         )
#     )


df_pois = pd.read_csv(
    os.path.expandvars("%APPDATA%/poi_tracker/data/unvisited_pois.csv")
)
df_visited = pd.read_csv(os.path.expandvars("%APPDATA%/poi_tracker/data/visited_pois.csv"))
# df_pois = pd.read_csv("total_path.csv")

last_idx = len(df_pois) - 1

fig.add_trace(
    go.Scattergeo(
        lon=[df_flight_paths["destination_lonx"].iat[-1], df_pois["Longitude"][0]],
        lat=[df_flight_paths["destination_laty"].iat[-1], df_pois["Latitude"][0]],
        mode="lines+markers",
        # line=dict(width=line_width, color="plum"),
        line=dict(width=line_width + 1, color="black"),
        marker=dict(size=marker_size + 1),
    )
)
fig.add_trace(
    go.Scattergeo(
        lon=[df_flight_paths["destination_lonx"].iat[-1], df_pois["Longitude"][0]],
        lat=[df_flight_paths["destination_laty"].iat[-1], df_pois["Latitude"][0]],
        mode="lines+markers",
        # line=dict(width=line_width, color="plum"),
        line=dict(width=line_width, color="rgb(255,150,0)"),
        marker=dict(size=marker_size),
        text=[df_flight_paths["destination_ident"].iat[-1], df_pois["Name"][0]],
    )
)

num_visited = min(max([abs(d) for d in diff]), len(df_pois))
active_color = (255, 105, 180)
plan_color = (255, 255, 153)
diff = (
    plan_color[0] - active_color[0],
    plan_color[1] - active_color[1],
    plan_color[2] - active_color[2],
)
change = (diff[0] / num_visited,
        diff[1] / num_visited,
        diff[2] / num_visited
        )
#num_visited = last_idx  # ceil(sum(([abs(d) for d in diff]))/len(diff)**3)

color = active_color
for i in range(0, len(df_pois)-1):
    fig.add_trace(
        go.Scattergeo(
            lon=[df_pois["Longitude"][i], df_pois["Longitude"][i + 1]],
            lat=[df_pois["Latitude"][i], df_pois["Latitude"][i + 1]],
            mode="lines+markers",
            line=dict(width=line_width + 1, color=f"black"),  ##FF69B4
            # line=dict(width=line_width, color="hotpink"), ##FF69B4
            # line=dict(width=line_width, color="rgb(255,0,255)"),
            marker=dict(size=marker_size + 1),
        )
    )
#for i in range(0, len(df_pois)-1):
    fig.add_trace(
        go.Scattergeo(
            lon=[df_pois["Longitude"][i], df_pois["Longitude"][i + 1]],
            lat=[df_pois["Latitude"][i], df_pois["Latitude"][i + 1]],
            mode="lines+markers",
            line=dict(
                width=line_width, color=f"rgb({color[0]},{color[1]},{color[2]})"
            ),  ##FF69B4
            # line=dict(width=line_width, color="hotpink"), ##FF69B4
            # line=dict(width=line_width, color="rgb(255,0,255)"),
            text=[df_pois["Name"][i], df_pois["Name"][i + 1]],
            marker=dict(size=marker_size),
        )
    )
    if i > num_visited:
        color = plan_color
    else:
        color = (
            color[0] + change[0],
            color[1] + change[1],
            color[2] + change[2],
        )

# fig.add_trace(
#     go.Scattergeo(
#         lon=df_pois["Longitude"],
#         lat=df_pois["Latitude"],
#         hoverinfo="text",
#         text=df_pois["Name"],
#         mode="markers",
#         marker=dict(
#             size=3,
#             line=dict(width=1, color="limegreen"),
#         ),
#     )
# )

# for i in range(num_visited, last_idx):
#     fig.add_trace(
#         go.Scattergeo(
#             lon=[df_pois["Longitude"][i], df_pois["Longitude"][i + 1]],
#             lat=[df_pois["Latitude"][i], df_pois["Latitude"][i + 1]],
#             mode="lines+markers",
#             # line=dict(width=line_width, color="LightGoldenRodYellow", dash="solid"),
#             line=dict(width=line_width + 1, color="black", dash="solid"),
#             marker=dict(size=marker_size + 1),
#             # opacity = max(0.33, 1 - (i/last_idx))#min(0.75, max(1 - (i/50), 0.33))
#         )
#     )
#     fig.add_trace(
#         go.Scattergeo(
#             lon=[df_pois["Longitude"][i], df_pois["Longitude"][i + 1]],
#             lat=[df_pois["Latitude"][i], df_pois["Latitude"][i + 1]],
#             mode="lines+markers",
#             # line=dict(width=line_width, color="LightGoldenRodYellow", dash="solid"),
#             line=dict(width=line_width, color="#ffff99", dash="solid"),
#             marker=dict(size=marker_size),
#             text=[df_pois["Name"][i], df_pois["Name"][i + 1]],
#             # opacity = max(0.33, 1 - (i/last_idx))#min(0.75, max(1 - (i/50), 0.33))
#         )
#     )

# for i in range(last_idx-num_visited, last_idx):
#     fig.add_trace(
#             go.Scattergeo(
#                 lon=[df_pois["Longitude"][i], df_pois["Longitude"][i+1]],
#                 lat=[df_pois["Latitude"][i], df_pois["Latitude"][i+1]],
#                 hoverinfo="none",
#                 mode="lines",
#                 line=dict(width=3, color="Orange"),
#             )
#     )

(positron_land, positron_water) = ("rgb(250,250,248)","rgb(212,218,220)")
(stamen_land, stamen_water) = ("rgb(192,206,158)", "rgb(153,179,204)")
(osm_land, osm_water) = ("tan", "rgb(170,211,223)")
fig.update_layout(
    # title_text="Around the World",
    showlegend=False,
    geo=dict(
        scope="world",
        resolution=50,
        projection_type="equirectangular",
        showland=True,
        landcolor=stamen_land,
        oceancolor=stamen_water,
        lakecolor=stamen_water,
        showcountries=False,
        showocean=True,
    ),
    paper_bgcolor="black",
    width=5120,
    height=2880,
    margin=go.layout.Margin(l=0, r=0, b=0, t=0, pad=0),
    autosize=False,
)
# Center map on the most recent destination
fig.update_geos(projection_rotation={'lon':df_flight_paths["destination_lonx"].tail(1).values[0]})

ratio=16/9
h=8640
w=int(h*ratio)
fig.write_image("./map.png", width=w, height=h)
fig.write_image("./map.svg")
end_plotting = time()

print(f"Path finding took: {end_pathing - start_pathing} seconds")
print(f"Plotting took: {end_plotting - start_plotting} seconds")
print(f"Total time: {end_plotting - start_pathing} seconds")
print(f"Tour progress:")
print(f"Visited POIs: {len(df_visited)}")
print(f"Unvisited POIs: {len(df_pois)}")
total_pois = int(len(df_pois) + len(df_visited))
print(f"Total POIs: {total_pois}")
sigfigs = len(str(total_pois))
pct_complete=round(len(df_visited)/total_pois*100, sigfigs-2)
print(f"Tour Progress: {len(df_visited)} / {total_pois} ({pct_complete}%)")


fig.show()
