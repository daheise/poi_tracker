import plotly.graph_objects as go
import pandas as pd

df_pois = pd.read_csv('total_path.csv')
fig = go.Figure()

fig.add_trace(go.Scattergeo(
    lon = df_pois['Longitude'],
    lat = df_pois['Latitude'],
    hoverinfo = 'text',
    text = df_pois['Name'],
    mode = 'markers',
    marker = dict(
        size = 7,
        color = 'rgb(255, 0, 0)',
        line = dict(
            width = 1,
            color = 'rgba(68, 68, 68, 0)'
        )
    )))

for i in range(len(df_pois)-1):
    fig.add_trace(
        go.Scattergeo(
            lon = [df_pois['Longitude'][i], df_pois['Longitude'][i+1]],
            lat = [df_pois['Latitude'][i], df_pois['Latitude'][i+1]],
            hoverinfo = 'none',
            mode = 'lines',
            line = dict(width = 1,color = 'red'),
        )
    )

fig.update_layout(
    title_text = 'Around the World',
    showlegend = False,
    geo = dict(
        scope = 'world',
        projection_type = 'equirectangular',
        showland = True,
        landcolor = 'rgb(243, 243, 243)',
        countrycolor = 'rgb(204, 204, 204)',
    ),
    width=5120,
    height=2880,
    margin=go.layout.Margin(
        l=50,
        r=50,
        b=100,
        t=100,
        pad = 4
    ),
    autosize=False

)

fig.show()