import os
from turtle import width
import plotly.graph_objects as go
import pandas as pd

df_pois = pd.read_csv(
    os.path.expandvars("%APPDATA%/poi_tracker/data/unvisited_pois.csv")
)
# df_pois = pd.read_csv("total_path.csv")
fig = go.Figure()

last_idx = len(df_pois) - 1
num_visited = 4

for i in range(0, num_visited):
    fig.add_trace(
        go.Scattergeo(
            lon=[df_pois["Longitude"][i], df_pois["Longitude"][i + 1]],
            lat=[df_pois["Latitude"][i], df_pois["Latitude"][i + 1]],
            hoverinfo="none",
            mode="lines+markers",
            line=dict(width=3, color="deeppink"),
            marker=dict(size=3),
        )
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

for i in range(num_visited, last_idx - num_visited):
    fig.add_trace(
        go.Scattergeo(
            lon=[df_pois["Longitude"][i], df_pois["Longitude"][i + 1]],
            lat=[df_pois["Latitude"][i], df_pois["Latitude"][i + 1]],
            hoverinfo="none",
            mode="lines+markers",
            line=dict(width=2, color="skyblue", dash="solid"),
            marker=dict(size=3),
            opacity=max(
                0.33, 1 - (i / (100 * num_visited))
            ),  # min(0.75, max(1 - (i/50), 0.33))
        )
    )

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

fig.update_layout(
    # title_text="Around the World",
    showlegend=False,
    geo=dict(
        scope="world",
        projection_type="equirectangular",
        showland=True,
        landcolor="rgb(243, 243, 243)",
        countrycolor="rgb(204, 204, 204)",
    ),
    width=5120,
    height=2880,
    margin=go.layout.Margin(l=0, r=0, b=0, t=0, pad=0),
    autosize=False,
)

fig.write_image("./plan.png", width=15360, height=8640)
fig.show()
