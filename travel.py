#%%
import os, warnings, requests
import pandas as pd
import numpy as np
import country_converter as coco
import glob
import plotly.graph_objects as go
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from kaggle.api.kaggle_api_extended import KaggleApi
from shapely.geometry import shape
from scipy.spatial import cKDTree, distance_matrix
# from dijkstra import dijkstra, Graph, Vertex, Edge

pd.set_option('display.max_columns', None)
warnings.filterwarnings('ignore')

dataset = 'max-mind/world-cities-database'
download_path = os.path.join(os.getcwd(), 'data')
country_url = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json'

if os.path.exists(os.path.expanduser('~/.kaggle/kaggle.json')):
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    if len(os.listdir(download_path))==0:
        api = KaggleApi()
        api.authenticate()
        print(f'Downloading dataset "{dataset}" to "{download_path}"...')
        api.dataset_download_files(dataset, path=download_path, unzip=True)
        print('Download complete!')
    else:
        print('Data found. No download needed!')
    try:
        data = pd.read_csv(glob.glob(f'{download_path}/*.csv')[0])
    except IndexError:
        raise IndexError('No CSV file found in the data!') from None
else:
    print('Kaggle API key not found. Please place your kaggle.json file in the .kaggle folder.')
    if not os.path.exists(os.path.expanduser('~/.kaggle')):
        os.makedirs('/.kaggle')
        print('.kaggle folder created!')

loc_df = data.copy()
loc_df.columns = [x.lower() for x in loc_df.columns]
loc_df.rename(columns={'country':'code', 
                       'accentcity':'accent_city', 
                       'latitude':'lat', 
                       'longitude':'lon'
                       }, inplace=True)
loc_df.sort_values('population', ascending=False, inplace=True)
loc_df.drop_duplicates(subset=['lat','lon'],keep='first', inplace=True)
loc_df['lat_rad'] = np.radians(loc_df['lat'])
loc_df['lon_rad'] = np.radians(loc_df['lon'])
loc_df['code'] = loc_df['code'].apply(lambda x: x.upper())
loc_df.dropna(subset=['population'],inplace=True)

geojson_data = requests.get(country_url).json()
country_df = pd.DataFrame()
for index, feature in enumerate(geojson_data['features']):
    geometry = shape(feature['geometry'])
    centroid = geometry.centroid
    country_df.loc[index,'country'] = feature['properties']['name']
    country_df.loc[index,'country_lat'] = centroid.y
    country_df.loc[index,'country_lon'] = centroid.x

cc = coco.CountryConverter() 
country_df['code'] = (coco.convert(names = country_df['country'], to='ISO2'))
world_gdf = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
world_gdf['code'] = (coco.convert(names = world_gdf['iso_a3'], to='ISO2'))
country_df = pd.merge(country_df, 
                      world_gdf.drop(['name','iso_a3','gdp_md_est'], axis=1).query('code != "not found"'), on = 'code'
                      ) 
loc_df = pd.merge(loc_df, country_df, on = ['code'])

city_dist = loc_df.query('population != 0').groupby(['country','country_lat','country_lon','geometry','code']).agg(
    city_count = ('city', lambda x: x.count()),
    population = ('population', np.sum),
).reset_index()
city_dist = gpd.GeoDataFrame(city_dist, geometry=city_dist['geometry'])

m_country = folium.Map(location=[0, 0], zoom_start=2.2)
m_country = city_dist.explore(m=m_country, column='city_count', cmap='Greens',legend=True)
folium.GeoJson(
    geojson_data,
    style_function=lambda x: {
        'fillColor':'none',    
        'color':'#4C9900',        
        'weight':2           
    }
).add_to(m_country)
for _, row in country_df.iterrows():
    folium.Marker(
        location=[row['country_lat'], row['country_lon']],
        icon = folium.CustomIcon(f'https://flagcdn.com/w40/{(row["code"]).lower()}.png', icon_size=(23, 11.5)),
        tooltip=row['code']
    ).add_to(m_country)

m_city = folium.Map(location=[0, 0], zoom_start=2.2)
marker_cluster = MarkerCluster().add_to(m_city)
for _, row in loc_df.iterrows():
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=5,
        color='green',
        fill=True,
        fill_color='green',
        fill_opacity=0.3,
        popup=row['accent_city'],
    ).add_to(marker_cluster)
folium.GeoJson(
    geojson_data,
    style_function=lambda x: {
        'fillColor':'none',    
        'color':'#4C9900',        
        'weight':2,         
    }
).add_to(m_city)

def determine_duration(nth_closest_point, population, change_country=False, is_great_distance=False):
    condition_matrix = np.array([2,4,8]) # base criteria for time spent.
    condition_matrix = np.stack((condition_matrix, condition_matrix+2), axis=1)
    condition_matrix = np.stack((condition_matrix, condition_matrix+2), axis=0)
    condition_matrix = np.stack((condition_matrix, condition_matrix+4), axis=1) # condition matrix with shape (2,2,3,2):[country, great distance, distance based on closest point (index), population]
    high_population = np.where(population <= 200_000, 0, 1)
    return condition_matrix[int(change_country), int(is_great_distance), nth_closest_point, high_population]

def identify_valid_neighbors(points, lat_boundry=2):
    '''
    Identify valid neighbors for each point considering latitude boundaries.
    '''
    lat_condition = np.logical_and(
        points[:, 0][:, None] <= points[:, 0] + lat_boundry,
        points[:, 0][:, None] >= points[:, 0] - lat_boundry 
    )

    return lat_condition

def calculate_haversine_distance(lat1, lon1, lat2, lon2, R=6371):

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    distance = R * c
    is_great_distance = distance > R/2

    return distance, is_great_distance

def calculate_closest_points(points, n=3):

    points_augmented = np.copy(points)
    points_augmented[:, 1] = np.where(points[:, 1] < 0,
                                      points[:, 1] + 360,
                                      points[:, 1] - 360
                                      )
    points_augmented = np.vstack((points, points_augmented))

    tree = cKDTree(points_augmented)
    _, indices = tree.query(points, k=n+1)

    closest_idxs = indices[:,1:n+1]

    num_original_points = len(points)
    mapped_closest_idxs = np.where(closest_idxs < num_original_points,
                                   closest_idxs,
                                   closest_idxs - num_original_points
                                   )
    return mapped_closest_idxs

origin_city = 'shiraz'
origin_country = 'IR'
origin = loc_df.query(f'city=="{origin_city}" and code=="{origin_country}"')
origin_index = origin.index[0]
moving_direction = 'W'

points = loc_df[['lat', 'lon']].values
valid_nieghbors = identify_valid_neighbors(points, lat_boundry=0.5)

general_path_df = loc_df.loc[valid_nieghbors[origin_index]].reset_index(drop=True)

longitudes = general_path_df['lon'].tolist()
zero_lons = [lon for lon in longitudes if lon == 0]
positives_lons = sorted([lon for lon in longitudes if lon > 0])
negatives_lons = sorted([lon for lon in longitudes if lon < 0])

if moving_direction == 'W':
    positives_lons.reverse()
    negatives_lons.reverse()
    sorted_lons = zero_lons + negatives_lons + positives_lons
elif moving_direction == 'E':
    sorted_lons = zero_lons + positives_lons + negatives_lons

lon_order_mapping = {lon: i for i, lon in enumerate(sorted_lons)}
general_path_df['lon_order'] = general_path_df['lon'].map(lon_order_mapping)
general_path_df.sort_values('lon_order', inplace=True)

path_limit_thresh = 0.005
neighbors, times, all_distances = [], [], []

for index, row in general_path_df.iterrows():

    current_point_country = row['country']

    path_df = general_path_df.copy()
    origin_sorted_index = sorted_lons.index(row['lon'])
    shifted_lons = sorted_lons[origin_sorted_index:] + sorted_lons[:origin_sorted_index]
    lon_rankings = {value: rank for rank, value in enumerate(shifted_lons)}
    path_df['lon_rank'] = path_df['lon'].map(lon_rankings)
    path_df['lon_rank_pct'] = path_df['lon_rank'].rank(pct=True)

    filtered_path_df = path_df.loc[path_df['lon_rank_pct'] <= path_limit_thresh]
    filtered_path_df = filtered_path_df.sort_values('lon_rank_pct').reset_index().rename(columns={'index':'org_index'})
    path_limit_thresh = 0.02

    while len(filtered_path_df) < 20:
        path_limit_thresh += 0.01
        filtered_path_df = path_df.loc[path_df['lon_rank_pct'] <= path_limit_thresh]
        filtered_path_df = filtered_path_df.sort_values('lon_rank_pct').reset_index().rename(columns={'index':'org_index'})

    points = filtered_path_df[['lat','lon']].values
    closest_idxs = calculate_closest_points(points, n=3)
    indices_in_general_path = filtered_path_df.loc[closest_idxs[0]]['org_index'].values
    neighbors.append(indices_in_general_path)
    durations, distances = [], []
    for idx, filtered_idx in enumerate(closest_idxs[0]):
        potential_next_point_population = filtered_path_df.loc[filtered_idx]['population']
        potential_next_point_country = filtered_path_df.loc[filtered_idx]['country']
        country_change = current_point_country != potential_next_point_country
        distance, is_great_distance = calculate_haversine_distance(row['lat_rad'], row['lon_rad'],
                                                filtered_path_df.loc[filtered_idx]['lat_rad'],
                                                filtered_path_df.loc[filtered_idx]['lon_rad'],
                                                )
        nth_closest_point = idx
        duration = determine_duration(nth_closest_point,
                                      potential_next_point_population,
                                      country_change,
                                      is_great_distance
                                      )
        durations.append(duration)
        distances.append(round(distance))
    times.append(durations)
    all_distances.append(distances)

general_path_df['adjacent_matrix'] = neighbors
general_path_df['edges'] = times
general_path_df['distances'] = all_distances


import itertools
from heapq import heappush, heappop

class Graph:
    def __init__(self, adjacency_list):
        self.adjacency_list = adjacency_list

class Vertex:
    def __init__(self, value, longitude):
        self.value = value
        self.longitude = longitude

class Edge:
    def __init__(self, time, vertex):
        self.time = time
        self.vertex = vertex

def dijkstra(graph, start, end):
    previous = {v: None for v in graph.adjacency_list.keys()}
    visited = {v: False for v in graph.adjacency_list.keys()}
    times = {v: float('inf') for v in graph.adjacency_list.keys()}
    times[start] = 0
    queue = PriorityQueue()
    queue.add_task(0, start)
    path = []
    last_visited = None 
    
    while queue:
        removed_time, removed = queue.pop_task()
        visited[removed] = True
        last_visited = removed  # Update the last visited vertex

        if removed is end:
            while previous[removed]:
                path.append(removed.value)
                removed = previous[removed]
            path.append(start.value)
            return path[::-1], times[end]

        for edge in graph.adjacency_list[removed]:
            if visited[edge.vertex]:
                continue

            new_time = removed_time + edge.time
            if new_time < times[edge.vertex]:
                times[edge.vertex] = new_time
                previous[edge.vertex] = removed
                queue.add_task(new_time, edge.vertex)
    # if no path is found.
    print(f'No complete path found!')
    return [last_visited.value], times[last_visited]

# slightly modified heapq implementation from https://docs.python.org/3/library/heapq.html
class PriorityQueue:
    def __init__(self):
        self.pq = []  # list of entries arranged in a heap
        self.entry_finder = {}  # mapping of tasks to entries
        self.counter = itertools.count()  # unique sequence count

    def __len__(self):
        return len(self.pq)

    def add_task(self, priority, task):
        # add a new task or update the priority of an existing task.
        if task in self.entry_finder:
            self.update_priority(priority, task)
            return self
        count = next(self.counter)
        entry = [priority, count, task]
        self.entry_finder[task] = entry
        heappush(self.pq, entry)

    def update_priority(self, priority, task):
        # update the priority of a task in place.
        entry = self.entry_finder[task]
        count = next(self.counter)
        entry[0], entry[1] = priority, count

    def pop_task(self):
        # remove and return the lowest priority task. Raise KeyError if empty.
        while self.pq:
            priority, count, task = heappop(self.pq)
            del self.entry_finder[task]
            return priority, task
        raise KeyError('pop from an empty priority queue')

vertices_dict = {index: Vertex(index, row['lon']) for index, row in general_path_df.iterrows()}
adjacency_list = {vertex: [] for vertex in vertices_dict.values()}

for idx, row in general_path_df.iterrows():
    from_vertex = vertices_dict[idx]
    for adj, time in zip(row['adjacent_matrix'], row['edges']):
        to_vertex = vertices_dict[adj] 
        adjacency_list[from_vertex].append(Edge(time, to_vertex))

graph = Graph(adjacency_list)

origin = general_path_df.query(f'city=="{origin_city}" and code=="{origin_country}"')
origin_lon_order = origin['lon_order'].values[0]
origin_index = origin.index[0]
destination = general_path_df.loc[general_path_df['lon_order'].between(origin_lon_order - 20, origin_lon_order),:]
destination = destination.reset_index().rename(columns={'index':'org_index'})
previous_neighbors = destination[['lat','lon']].values
prev_closest_neighbor = calculate_closest_points(previous_neighbors, n=1)[-1]
end_index = destination.loc[prev_closest_neighbor]['org_index'].values[0]

start = vertices_dict[origin_index]
end = vertices_dict[end_index]
path, time = dijkstra(graph, start, end)
if len(path) < 2:
    print(f'Last reachable point: {general_path_df.loc[path[0]]['city']} ({path[0]}) in {(time/24):.2f} days!')
else:
    print(f'Shortest time to {origin_city.capitalize()} and back: {(time/24):.2f} days!')
    print(f'Journey: {path}')
    print(f'# Cities explored: {len(path)}')

globe = general_path_df.loc[path]
globe['point_color'] = globe['city'].apply(lambda x: '#ffd500' if x=='london' else '#2291bd')
globe['point_symbol'] = globe['city'].apply(lambda x: 'star' if x == 'london' else 'circle') 
globe['point_size'] = globe['city'].apply(lambda x: 24 if x == 'london' else 4) 

fig = go.Figure(go.Scattergeo(lat=globe['lat'], 
                              lon=globe['lon'],
                              text=globe['accent_city'],
                              marker=dict(size=globe['point_size'],
                                          color=globe['point_color'],
                                          symbol=globe['point_symbol']),
                              line=dict(color='#0d41a9'),
                              mode='markers+lines',
                              name='Path'
                              ))

for lat in range(-90, 91, 5):
    fig.add_trace(go.Scattergeo(
        lat=[lat] * 361,
        lon=list(range(-180, 181)),
        mode='lines',
        line=dict(color='gray', width=0.15),
        showlegend=False
    ))

for lon in range(-180, 181, 5):
    fig.add_trace(go.Scattergeo(
        lat=list(range(-90, 91)),
        lon=[lon] * 181,
        mode='lines',
        line=dict(color='gray', width=0.2, dash='dot'),
        showlegend=False
    ))

fig.update_geos(showframe=True,
                projection_type='orthographic',
                showcoastlines=True,
                showcountries=True,
                showland=True,
                landcolor='#61f179',
                coastlinecolor='DarkBlue',
                countrycolor='Black',
                countrywidth=0.8
                )

fig.update_layout(width= 750, height=750, margin={'r':0,'t':0,'l':0,'b':0}, showlegend=False)
# fig.write_html("3d_plot.html")
fig.show()

# %%

