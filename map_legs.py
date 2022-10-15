import plotly.graph_objects as go
import pandas as pd
import sqlite3 as sql
import os

con = sql.connect(
    os.path.expandvars(
        "%APPDATA%\ABarthel\little_navmap_db\little_navmap_logbook.sqlite"
    )
)
# cur = con.cur()
# cur.execute("SELECT * FROM LOGBOOK WHERE description LIKE '%WT L%' ORDER BY departure_time DESC")
df_flight_paths = pd.read_sql_query(
    "SELECT * FROM LOGBOOK WHERE description LIKE '%WT L%' ORDER BY departure_time ASC",
    con,
)
print(df_flight_paths["departure_ident"].head(5))

fig = go.Figure()

# fig.add_trace(go.Scattergeo(
#     lon = df_flight_paths['Longitude'],
#     lat = df_flight_paths['Latitude'],
#     hoverinfo = 'text',
#     text = df_flight_paths['Name'],
#     mode = 'markers',
#     marker = dict(
#         size = 7,
#         color = 'rgb(255, 0, 0)',
#         line = dict(
#             width = 1,
#             color = 'rgba(68, 68, 68, 0)'
#         )
#     )))

# fig.add_trace(go.Scattergeo(
#     lon = df_flight_paths['Longitude'],
#     lat = df_flight_paths['Latitude'],
#     hoverinfo = 'text',
#     text = df_flight_paths['Name'],
#     mode = 'markers',
#     marker = dict(
#         size = 7,
#         color = 'rgb(255, 0, 0)',
#         line = dict(
#             width = 1,
#             color = 'rgba(68, 68, 68, 0)'
#         )
#     )))

fpl_string = [
    dep + " - " + dest
    for dep, dest in zip(
        df_flight_paths["departure_ident"], df_flight_paths["destination_ident"]
    )
]

for i in range(0, len(df_flight_paths) - 1):
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
            text=fpl_string[i],
            line=dict(width=2, color="lightslategray"),
            marker=dict(size=3),
            opacity=max(0.5, i / len(df_flight_paths))
            # opacity = float(df_flight_paths['cnt'][i]) / float(df_flight_paths['cnt'].max()),
        )
    )
# Most recent leg
fig.add_trace(
    go.Scattergeo(
        locationmode="USA-states",
        lon=[
            df_flight_paths["departure_lonx"][len(df_flight_paths) - 1],
            df_flight_paths["destination_lonx"][len(df_flight_paths) - 1],
        ],
        lat=[
            df_flight_paths["departure_laty"][len(df_flight_paths) - 1],
            df_flight_paths["destination_laty"][len(df_flight_paths) - 1],
        ],
        mode="lines+markers",
        text=fpl_string[-1],
        line=dict(width=2, color="deeppink"),
        marker=dict(size=3),
        # opacity = float(df_flight_paths['cnt'][i]) / float(df_flight_paths['cnt'].max()),
    )
)

fig.update_layout(
    # title_text = 'Around the World',
    showlegend=False,
    geo=dict(
        scope="world",
        projection_type="equirectangular",
        showland=True,
        landcolor="rgb(243, 243, 243)",
    ),
    width=5120,
    height=2880,
    margin=go.layout.Margin(l=0, r=0, b=0, t=0, pad=0),
    autosize=True,
)

fig.write_image("./legs.png", width=15360, height=8640)
# write_image(fig, "./plan.svg", 'svg', width=2560, height=1440)
fig.show()
