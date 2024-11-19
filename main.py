#%%
import os, warnings, shutil

import plotly.graph_objects as go
import imageio

from data_process import download_and_process_data
from path.explorer import PathExplorer
from path.optimizer import Graph, Edge, Vertex
from path.finder import path_finder
from utils import identify_valid_points

warnings.filterwarnings('ignore')

location_df, country_df, geojson_data = download_and_process_data()

explorable_path = PathExplorer(location_df,
                               origin_city='london',
                               origin_country='GB',
                               moving_direction='E')

origin_city = explorable_path.origin_city
origin_country = explorable_path.origin_country
direction = explorable_path.moving_direction

valid_neighbors = identify_valid_points(location_df[['lat', 'lon']].values, lat_boundry=0.5)
explorable_path.prepare_explorable_path(valid_neighbors)
explorable_path.filter_path()
explorable_path_df = explorable_path.get_dataframe()

vertices_dict = {index: Vertex(index, row['lon']) for index, row in explorable_path_df.iterrows()}
adjacency_list = {vertex: [] for vertex in vertices_dict.values()}

for idx, row in explorable_path_df.iterrows():
    from_vertex = vertices_dict[idx]
    for adj, time in zip(row['adjacent_matrix'], row['edges']):
        to_vertex = vertices_dict[adj] 
        adjacency_list[from_vertex].append(Edge(time, to_vertex))

graph = Graph(adjacency_list)

path, result, origin_index = path_finder(explorable_path, graph, vertices_dict)

globe = result
globe['point_color'] = globe.apply(lambda row: '#ffd500' if row['city'] == origin_city else '#2291bd', axis=1)
globe['point_symbol'] = globe.apply(lambda row: 'star' if row['city'] == origin_city else 'circle', axis=1)
globe['point_size'] = globe.apply(lambda row: 32 if row['city'] == origin_city else 10, axis=1)
total_time = globe['next_point_duration'].tolist()

frame_dir = os.path.join(os.getcwd(), 'frames') 

if not os.path.exists(frame_dir):
    os.makedirs(frame_dir)

frames = []
num_frames = len(globe)

for i in range(1, num_frames):
    frame = go.Frame(
        data=[go.Scattergeo(
            lat=globe['lat'][:i+1], # incrementally include more points
            lon=globe['lon'][:i+1],
            text=globe['accent_city'][:i+1],
            marker=dict(
                size=globe['point_size'][:i+1],
                color=globe['point_color'][:i+1],
                symbol=globe['point_symbol'][:i+1],
                opacity=0.8 
            ),
            mode='markers+lines'
        )],
        name=f'frame_{i}'
    )
    frames.append(frame)

image_paths = []

for i in range(len(frames)):

    print(i)
    if i != len(frames) - 1:
        title = f'Journey started from {globe.iloc[0]['city'].capitalize()}...'
        uptime = f'Uptime: {int(sum(total_time[:i+1]) // 24)} days and {int(sum(total_time[:i+1]) % 24)} hours...' 
    else:
        title = f'Reached back to {globe.iloc[0]['city'].capitalize()}!'
        
        uptime = ('<span style="color:black; font-weight:bold;">Final Time:</span> '
                 f'<span style="color:red; font-weight:bold;">{int(sum(total_time) // 24)}</span> '
                  '<span style="color:black;">days and</span> '
                 f'<span style="color:red; font-weight:bold;">{int(sum(total_time) % 24)}</span> '
                  '<span style="color:black;">hours!</span>')

    fig = go.Figure(frames[i].data)

    for lat in range(-90, 91, 10):
        fig.add_trace(go.Scattergeo(
            lat=[lat] * 361,
            lon=list(range(-180, 181)),
            mode='lines',
            line=dict(color='gray', width=0.15),
            showlegend=False
            ))

    for lon in range(-180, 181, 10):
        fig.add_trace(go.Scattergeo(
            lat=list(range(-90, 91)),
            lon=[lon] * 181,
            mode='lines',
            line=dict(color='gray', width=0.25, dash='dot'),
            showlegend=False
            ))
    
    fig.update_layout(
        geo=dict(
            showframe=True,
            projection_type='orthographic',
            showcoastlines=True,
            showcountries=True,
            showland=True,
            landcolor='#61f179',
            coastlinecolor='DarkBlue',
            countrycolor='Black',
            countrywidth=0.8,
            projection_rotation=dict(lon=globe.loc[origin_index]['lon'], 
                                         lat=globe.loc[origin_index]['lat']),
            projection_scale=0.8
        ),
        width=700,
        height=700,
        margin={'r': 0, 't': 0, 'l': 0, 'b': 0},
        showlegend=False,
        title = title,
        title_x=0.5,
        title_y=0.97,

        annotations=[
        dict(
            x=0.5, 
            y=0.95,
            xref='paper',
            yref='paper',
            text=uptime,
            showarrow=False,
            font=dict(color='Black'),
            align='center',
            borderpad=4
            )]
    )

    frame_path = os.path.join(frame_dir, f'frame_{i}.png')
    fig.write_image(frame_path, scale=5)
    image_paths.append(frame_path)

last_frame = fig
last_frame.data[0].marker.color = '#dc3a1a'
frame_path = os.path.join(frame_dir, f'frame_{i+1}.png')
last_frame.write_image(frame_path, scale=5)
image_paths.append(frame_path)

second_last_frame_path = image_paths[-2]
last_frame_path = image_paths[-1]
for _ in range(20):  # repeat the last frames 50 times (25 each) for more visibility for results and alternating color!
    image_paths.append(second_last_frame_path)
    image_paths.append(last_frame_path)

gif_path = os.path.join(os.getcwd(), 'journey.gif')
images = [imageio.imread(image_path) for image_path in image_paths]

shutil.rmtree(frame_dir)

imageio.mimsave(gif_path, images, duration=0.2, loop=0, fps=60)

print(f'GIF saved as {gif_path}')

#%%
#~~~~~ NOTEBOOK
# import geopandas as gpd
# import folium
# from folium.plugins import MarkerCluster
# import geopandas as gpd

# city_dist = location_df.groupby(['country','country_lat','country_lon','geometry','code']).agg(
#     city_count = ('city', lambda x: x.count()),
#     population = ('population', np.sum),
# ).reset_index()
# city_dist = gpd.GeoDataFrame(city_dist, geometry=city_dist['geometry'])

# m_country = folium.Map(location=[0, 0], zoom_start=2.2)
# m_country = city_dist.explore(m=m_country, column='city_count', cmap='Greens',legend=True)
# folium.GeoJson(
#     geojson_data,
#     style_function=lambda x: {
#         'fillColor':'none',    
#         'color':'#4C9900',        
#         'weight':2           
#     }
# ).add_to(m_country)
# for _, row in country_df.iterrows():
#     folium.Marker(
#         location=[row['country_lat'], row['country_lon']],
#         icon = folium.CustomIcon(f'https://flagcdn.com/w40/{(row["code"]).lower()}.png', icon_size=(23, 11.5)),
#         tooltip=row['code']
#     ).add_to(m_country)

# m_city = folium.Map(location=[0, 0], zoom_start=2.2)
# marker_cluster = MarkerCluster().add_to(m_city)
# for _, row in location_df.iterrows():
#     folium.CircleMarker(
#         location=[row['lat'], row['lon']],
#         radius=5,
#         color='green',
#         fill=True,
#         fill_color='green',
#         fill_opacity=0.3,
#         popup=row['accent_city'],
#     ).add_to(marker_cluster)
# folium.GeoJson(
#     geojson_data,
#     style_function=lambda x: {
#         'fillColor':'none',    
#         'color':'#4C9900',        
#         'weight':2,         
#     }
# ).add_to(m_city)

#------------------------------------------------