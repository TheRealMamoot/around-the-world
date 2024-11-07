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
from geopy.distance import geodesic
from geopy.point import Point

pd.set_option('display.max_columns', None)
warnings.filterwarnings('ignore')

dataset = 'max-mind/world-cities-database'
download_path = os.path.join(os.getcwd(), 'data')
country_url = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json'
#%%
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
#%%
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
#%%
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
def calculate_closest_points(points, n=20):
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

def identify_direction(bearings, angle=45):
    conditions=[((bearings <= 0 + angle) | (bearings > 360 - angle)),
                ((bearings > 90 - angle) & (bearings < 90 + angle)),
                ((bearings >= 180 - angle) & (bearings < 180 + angle)),
                ((bearings >= 270 - angle) & (bearings <= 270 + angle)),
                ]
    results=['N','E','S','W']
    direction = np.select(conditions, results)
    return direction

def is_points_in_cone(lats, lons, start_lat, start_lon, center_bearing=90, angle=90):
    if center_bearing not in (90, 270):
        raise ValueError('Invalid center_bearing! It must be either 90 (East) or 270 (West).')
    bearings = calculate_bearing(np.radians(start_lat), np.radians(start_lon), np.radians(lats), np.radians(lons))
    left_bearing = (center_bearing - angle / 2) % 360
    right_bearing = (center_bearing + angle / 2) % 360
    in_cone = (bearings >= left_bearing) & (bearings <= right_bearing)
    if center_bearing == 90:  
        valid_longitude = np.logical_or(
            (lons > start_lon) | (lons < start_lon - 180),   
            (lons < 0) if start_lon > 0 else (lons > 0))
    elif center_bearing == 270: 
        valid_longitude = np.logical_or(
            (lons < start_lon) | (lons > start_lon + 180),  
            (lons > 0) if start_lon < 0 else (lons < 0))
    return in_cone & valid_longitude

def determine_time_spent(index, population, change_country):
    condition_matrix = np.array([2,4,8,10])
    condition_matrix = np.stack((condition_matrix, condition_matrix+2), axis=1)
    condition_matrix = np.stack((condition_matrix, condition_matrix+2), axis=0)
    col = np.where(population <= 200000, 0, 1)
    row = np.minimum(index, 3)
    return condition_matrix[change_country.astype(int), row, col]
#%%
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
directions = identify_direction(np.vstack(loc_df['bearings']))
loc_df['directions'] = directions.tolist()
#%%
start_city = 'london'
start_country = 'GB'
start_df = loc_df.query(f'city=="{start_city}" and code=="{start_country}"')
start_point = start_df['loc'].values[0]
step = 0
moving_direction = 'E'
moving_angles = {'E':90, 'W':270}
nth_chosen_point, country_changes, populations, checkpoints = [], [], [], [] 
cones = {}
circumnavigated = False
path_locs_idx = [start_df['loc'].index[0]]
closest_points_in_direction = [idx for idx, direction in enumerate(start_df['directions'].values[0]) if direction==moving_direction]
closest_point_idx = start_df['closest_idxs'].values[0][closest_points_in_direction[0]]
next_point_country = loc_df.loc[closest_point_idx]['code']
next_point_population = loc_df.loc[closest_point_idx]['population']
nth_chosen_point.append(closest_points_in_direction[0])
path_locs_idx.append(closest_point_idx)
country_changes.append(next_point_country != start_country) 
populations.append(next_point_population)
lats = loc_df['lat'].values
lons = loc_df['lon'].values

while step <= 370:
    checkpoints.append({'step': step,
                        'path_locs_idx': path_locs_idx[:],      
                        'country_changes': country_changes[:],
                        'populations': populations[:],
                        'nth_chosen_point': nth_chosen_point[:]})
    df = loc_df.loc[[path_locs_idx[-1]]]
    latest_point = df['loc'].values[0]
    latest_point_country = df['code'].values[0]
    latest_point_population = df['population'].values[0]
    directions = df['directions'].values[0]
    closest_points_in_direction = [idx for idx, direction in enumerate(directions) if direction==moving_direction]
    if len(closest_points_in_direction) != 0:
        closest_point_in_direction = closest_points_in_direction[0]
        next_point_idx = df['closest_idxs'].values[0][closest_point_in_direction]
    else:
        latest_point_lat, latest_point_lon = latest_point
        points_in_cone = is_points_in_cone(lats, lons, latest_point_lat, latest_point_lon, 
                                           center_bearing=moving_angles[moving_direction], angle=90)
        cone_df = loc_df[points_in_cone]
        cone_df = pd.concat([cone_df, df])
        cones[f'{df['city'].values[0]}'] = cone_df
        latitudes = cone_df['lat_rad'].values
        longitudes = cone_df['lon_rad'].values
        lat_augmented = np.concatenate([latitudes, latitudes])
        lon_shifted = np.where(longitudes > 0, longitudes - 2 * np.pi, longitudes + 2 * np.pi)
        lon_augmented = np.concatenate([longitudes, lon_shifted])
        all_points = np.vstack([lat_augmented, lon_augmented]).T
        cone_df['lon_rad_shifted'] = lon_shifted
        closest_point_idx, closest_point_dist = calculate_closest_points(all_points, n=1)
        closest_idx_in_cone = closest_point_idx[-1][0]
        closest_lat_in_cone = all_points[closest_idx_in_cone,:][0]
        closest_lon_in_cone = all_points[closest_idx_in_cone,:][1]
        lat_condition = f'lat_rad == {closest_lat_in_cone}'
        lon_condition = f' and lon_rad_shifted == {closest_lon_in_cone}'
        result = cone_df.query(lat_condition + lon_condition)
        if result.empty:
            lon_condition = f' and lon_rad == {closest_lon_in_cone}'
            result = cone_df.query(lat_condition + lon_condition)
        next_point_idx = result.index[0]
    next_point_country = loc_df.loc[next_point_idx]['code']
    next_point_population = loc_df.loc[next_point_idx]['population']
    country_changes.append(next_point_country != latest_point_country)
    populations.append(next_point_population)
    nth_chosen_point.append(closest_points_in_direction[0] if closest_points_in_direction else -1)
    time_spent = determine_time_spent(np.array(nth_chosen_point),
                                      np.array(populations),
                                      np.array(country_changes))
    total_time_spent = np.sum(time_spent)
    path_locs_idx.append(next_point_idx)
    step += 1
    if path_locs_idx[-1] == start_df.index[0]:
        print('Returned to London!')
        break

#%%
globe = loc_df.loc[path_locs_idx]
globe['point_color'] = globe['city'].apply(lambda x: '#dc3a1a' if x in cones.keys() else '#ffd500' if x==start_city else '#2291bd')
globe['point_symbol'] = globe['city'].apply(lambda x: 'diamond' if x in cones.keys() else 'star' if x == start_city else 'circle') 
globe['point_size'] = globe['city'].apply(lambda x: 6 if x in cones.keys() else 16 if x == start_city else 4) 
fig = go.Figure(go.Scattergeo(lat=globe['lat'], 
                              lon=globe['lon'],
                              text=globe['accent_city'],
                              marker=dict(size=globe['point_size'],
                                          color=globe['point_color'],
                                          symbol=globe['point_symbol']),
                              line=dict(color='#0d41a9'),
                              mode='markers+lines'))
fig.update_geos(showframe=True,
                projection_type='orthographic',
                showcoastlines=True,
                showcountries=True,
                showland=True,
                landcolor='#61f179',
                coastlinecolor='DarkBlue',
                countrycolor='Black',
                countrywidth=0.8)
fig.update_layout(width= 700, height=700, margin={'r':0,'t':0,'l':0,'b':0})
# fig.write_html("3d_plot.html")
fig.show()
# %%
