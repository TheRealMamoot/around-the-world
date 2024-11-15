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
from scipy.spatial import cKDTree
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
loc_df.rename(columns={'country':'code', 'accentcity':'accent_city', 'latitude':'lat', 'longitude':'lon'}, inplace=True)
loc_df.sort_values('population', ascending=False, inplace=True)
loc_df.drop_duplicates(subset=['lat','lon'],keep='first', inplace=True)
loc_df['lat_rad'] = np.radians(loc_df['lat'])
loc_df['lon_rad'] = np.radians(loc_df['lon'])
loc_df['loc_rad'] = (np.vstack([loc_df['lat_rad'], loc_df['lon_rad']]).T).tolist()
loc_df['loc'] = (np.vstack([loc_df['lat'], loc_df['lon']]).T).tolist()
loc_df['code'] = loc_df['code'].apply(lambda x: x.upper())
loc_df.dropna(subset=['population'],inplace=True)

geojson_data = requests.get(country_url).json()
country_df = pd.DataFrame()
for index, feature in enumerate(geojson_data['features']):
    geometry = shape(feature['geometry'])
    centroid = geometry.centroid
    country_df.loc[index, 'country'] = feature['properties']['name']
    country_df.loc[index, 'country_lat'] = centroid.y
    country_df.loc[index, 'country_lon'] = centroid.x

cc = coco.CountryConverter() 
country_df['code'] = (coco.convert(names=country_df['country'], to='ISO2'))
world_gdf = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
world_gdf['code'] = (coco.convert(names=world_gdf['iso_a3'], to='ISO2'))
country_df = pd.merge(country_df, world_gdf.drop(['name','iso_a3','gdp_md_est'], axis=1).query('code != "not found"'), on='code') 
loc_df = pd.merge(loc_df, country_df, on=['code'])

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
#%%
def calculate_closest_points(points, n=500):
    tree = cKDTree(points)
    distances, indices = tree.query(points, k=n+1)
    closest_idxs = indices[:,1:n+1]
    closest_dists = distances[:,1:n+1]
    return closest_idxs, closest_dists

def calculate_bearing(lat1, lon1, lat2, lon2):
    delta_lon = lon2 - lon1
    x = np.sin(delta_lon) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(delta_lon)
    initial_bearing = np.arctan2(x, y)
    initial_bearing = np.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360
    return compass_bearing

# def haversine_distance(lat1, lon1, lat2, lon2):
#     R = 6371.0
#     dlat = np.radians(lat2 - lat1)
#     dlon = np.radians(lon2 - lon1)
#     a = np.sin(dlat / 2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2)**2
#     c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
#     return R * c

def identify_direction(bearings, angle=90):
    if angle > 180:
        raise ValueError('Invalid angle! It can not exceed 180 degrees.')
    conditions=[((bearings > 90 - angle / 2) & (bearings < 90 + angle / 2)),
                ((bearings >= 270 - angle / 2) & (bearings <= 270 + angle / 2)),
                ((bearings <= 0 + angle / 2) | (bearings > 360 - angle / 2)),
                ((bearings >= 180 - angle / 2) & (bearings < 180 + angle / 2))]
    results=['E','W','N','S']
    direction = np.select(conditions, results)
    return direction

def is_points_in_cone(start_lat, start_lon, lats, lons, center_bearing=90, angle=90):
    if center_bearing not in (90, 270):
        raise ValueError('Invalid center_bearing! It must be either 90 (East) or 270 (West).')
    bearings = calculate_bearing(np.radians(start_lat), np.radians(start_lon), np.radians(lats), np.radians(lons))
    left_bearing = (center_bearing - angle / 2) % 360
    right_bearing = (center_bearing + angle / 2) % 360
    in_cone = (bearings >= left_bearing) & (bearings <= right_bearing)

    if center_bearing == 90: # for crossing the meridian (when 180 degress becomes -180) for both east and west.
        valid_longitude = np.logical_or(
            (lons > start_lon) | (lons < start_lon - 180),   
            (lons < 0) if start_lon > 0 else (lons > 0))
        
    elif center_bearing == 270: 
        valid_longitude = np.logical_or(
            (lons < start_lon) | (lons > start_lon + 180),  
            (lons > 0) if start_lon < 0 else (lons < 0))
    
    # points_in_cone = in_cone & valid_longitude
    # if max_distance is not None:
    #     distances = haversine_distance(start_lat, start_lon, lats, lons)
    #     within_distance = distances <= max_distance
    #     points_in_cone = points_in_cone & within_distance
    return in_cone & valid_longitude

def determine_duration(nth_closest_point, population, change_country=False):
    condition_matrix = np.array([2,4,8,10,12,14]) # base criteria for time spent.
    condition_matrix = np.stack((condition_matrix, condition_matrix+2), axis=1)
    condition_matrix = np.stack((condition_matrix, condition_matrix+2), axis=0) # condition matrix with shape (2,4,2):[country, distance (index), population]
    col = np.where(population <= 200000, 0, 1)
    # row = np.minimum(nth_closest_point, 6)
    row = nth_closest_point
    return condition_matrix[int(change_country), row, col]

def include_previous_neighbor(neighbors, durations): # to construct the adjacent matrix. 
    new_neighbors = neighbors.copy()
    new_durations = durations.copy()
    for i, n in enumerate(neighbors):
        for j, neighbor in enumerate(n):
            if i not in new_neighbors[neighbor]:
                new_neighbors[neighbor] = np.append(new_neighbors[neighbor], i)
                new_durations[neighbor] = np.append(new_durations[neighbor], durations[i][j])
    return new_neighbors, new_durations # adding the previous points to next points to count as valid.

closest_idxs, closest_dists = calculate_closest_points(points=loc_df[['lat_rad', 'lon_rad']].values)
loc_df['closest_idxs'] = list(closest_idxs)
loc_df['closest_dists'] = list(closest_dists)
latitudes = loc_df['lat_rad'].values[closest_idxs]
longitudes = loc_df['lon_rad'].values[closest_idxs]
loc_df['points_loc'] = list(np.stack((latitudes,longitudes), axis=-1))
points_arr = np.stack(loc_df['points_loc'].values)
lat1 = loc_df['lat_rad'].values[:, np.newaxis]
lon1 = loc_df['lon_rad'].values[:, np.newaxis] 
lat2 = points_arr[:, :, 0] 
lon2 = points_arr[:, :, 1] 
bearings = calculate_bearing(lat1, lon1, lat2, lon2)
loc_df['bearings'] = list(bearings.round(2))
directions = identify_direction(np.vstack(loc_df['bearings']), angle=90)
loc_df['directions'] = directions.tolist()
#%%
moving_angles = {'E':90,'W':270}
moving_direction = 'E'
valid_points_indices, durations = [], []
cones = {}

for index, row in loc_df.iterrows():
    current_country = row['code']
    if moving_direction not in row['directions']: 
        points_in_cone = is_points_in_cone(row['lat'], row['lon'],
                                           loc_df['lat'].values, 
                                           loc_df['lon'].values, 
                                           center_bearing=moving_angles[moving_direction])
        cone_df = loc_df[points_in_cone]
        cone_df = pd.concat([cone_df, row.to_frame().T])
        latitudes = cone_df['lat_rad'].values
        longitudes = cone_df['lon_rad'].values
        lat_augmented = np.concatenate([latitudes, latitudes])
        lon_shifted = np.where(longitudes > 0, longitudes - 2 * np.pi, longitudes + 2 * np.pi)
        lon_augmented = np.concatenate([longitudes, lon_shifted]) # the cone has to understand the wrap around effect!
        all_points = np.vstack([lat_augmented, lon_augmented]).T
        cone_df['lon_rad_shifted'] = lon_shifted
        cones[f'{row['city']}'] = cone_df
        closest_point_idx, closest_point_dist = calculate_closest_points(all_points, n=6)
        closest_idx_in_cone = closest_point_idx[-1]
        valid_indices = []
        for point in closest_idx_in_cone:
            closest_lat_in_cone = all_points[point,:][0]
            closest_lon_in_cone = all_points[point,:][1]
            lat_condition = f'lat_rad == {closest_lat_in_cone}'
            lon_condition = f' and lon_rad_shifted == {closest_lon_in_cone}'
            result = cone_df.query(lat_condition + lon_condition)
            if result.empty:
                lon_condition = f' and lon_rad == {closest_lon_in_cone}'
                result = cone_df.query(lat_condition + lon_condition)
            temp_valid_indices = result.index[0]
            valid_indices.append(temp_valid_indices)
        valid_indices = np.array(valid_indices)
    else:
        direction_indices = np.array([i for i, d in enumerate(row['directions']) if d == moving_direction])
        valid_indices = np.array(row['closest_idxs'][direction_indices[:6]])  

    time_required = []
    for i, point in enumerate(valid_indices):
        next_point_country = loc_df.loc[point]['code']
        change_country = current_country != next_point_country
        population = loc_df.loc[point]['population']
        duration = determine_duration(i, population, change_country)
        time_required.append(duration)
    valid_points_indices.append(valid_indices)
    durations.append(time_required)

loc_df['adjacent_list'] = valid_points_indices
loc_df['edges'] = durations
loc_df['valid_neighbors'], loc_df['durations_to_neighbors'] = include_previous_neighbor(loc_df['adjacent_list'], loc_df['edges'])
#%%
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
#%%
vertices_dict = {index: Vertex(index, row['lon']) for index, row in loc_df.iterrows()}
# vertices_dict = {index: Vertex(index) for index, _ in loc_df.iterrows()}
adjacency_list = {vertex: [] for vertex in vertices_dict.values()}

for idx, row in loc_df.iterrows():
    from_vertex = vertices_dict[idx]
    for adj, time in zip(row['adjacent_list'], row['edges']):
        to_vertex = vertices_dict[adj] 
        adjacency_list[from_vertex].append(Edge(time, to_vertex))

graph = Graph(adjacency_list)
start_city = 'london'
start_country = 'GB'
start = loc_df.query(f'city=="{start_city}" and code=="{start_country}"').index[0]
start = vertices_dict[start]
# start = vertices_dict[30331]
end_city = 'torbay'
end_index = loc_df.query(f'city=="{end_city}"').index[0]
# end_index = 23709
end = vertices_dict[end_index]
path, time = dijkstra(graph, start, end)
if len(path) < 2:
    print(f'Last reachable point: {loc_df.loc[path[0]]['city']} ({path[0]}) in {(time/24):.2f} days!')
else:
    print(f'Shortest time to {loc_df.loc[end_index]['city']}: {(time/24):.2f} days!')
    print(f'Path to {loc_df.loc[end_index]['city']}: {path}')
    print(f'# Cities explored: {len(path)}')
#%%
globe = loc_df.loc[loc_df.loc[24705]['closest_idxs'].tolist()]
# globe = loc_df.loc[cones['torbay'].sample(500).index]
# globe = loc_df.loc[loc_df.query('continent=="Africa"').sample(600).index]
globe['point_color'] = globe['city'].apply(lambda x: '#dc3a1a' if x in cones else '#ffd500' if x==start_city else '#2291bd')
globe['point_symbol'] = globe['city'].apply(lambda x: 'diamond' if x in cones else 'star' if x == start_city else 'circle') 
globe['point_size'] = globe['city'].apply(lambda x: 12 if x in cones else 24 if x == start_city else 8) 

fig = go.Figure(go.Scattergeo(lat=globe['lat'], 
                              lon=globe['lon'],
                              text=globe['accent_city'],
                              marker=dict(size=globe['point_size'],
                                          color=globe['point_color'],
                                          symbol=globe['point_symbol']),
                              line=dict(color='#0d41a9'),
                              mode='markers',
                              name='Path'
                              ))

for lat in range(-90, 90, 10):
    fig.add_trace(go.Scattergeo(
        lat=[lat] * 361,
        lon=list(range(-180, 181)),
        mode='lines',
        line=dict(color='gray', width=0.15),
        showlegend=False
    ))

for lon in range(-180, 181, 10):
    fig.add_trace(go.Scattergeo(
        lat=list(range(-80, 81)),
        lon=[lon] * 161,
        mode='lines',
        line=dict(color='gray', width=0.15),
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

fig.update_layout(width= 700, height=700, margin={'r':0,'t':0,'l':0,'b':0}, showlegend=False)
# fig.write_html("3d_plot.html")
fig.show()

# %%
