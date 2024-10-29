#%%
import os
import pandas as pd
import numpy as np
import pycountry
import country_converter as coco
import glob
from kaggle.api.kaggle_api_extended import KaggleApi
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
import requests

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

city_df = data.copy()
city_df.columns = [x.lower() for x in city_df.columns]
city_df.rename(columns={'country':'code', 'accentcity':'accent_city', 'latitude':'lat', 'longitude':'lon'}, inplace=True)

geojson_data = requests.get(country_url).json()
country_df = pd.DataFrame()
for index,feature in enumerate(geojson_data['features']):
    country_name = feature['properties']['name']
    geometry = shape(feature['geometry'])
    centroid = geometry.centroid
    country_df.loc[index,'country'] = country_name
    country_df.loc[index,'country_lat'] = centroid.y,
    country_df.loc[index,'country_lon'] = centroid.x

cc = coco.CountryConverter() 
country_df['code'] = coco.convert(names=country_df['country'], to='ISO2')
country_df['code'] = country_df['code'].apply(lambda x: x.lower())
#%%        
m = folium.Map(location=[0, 0], zoom_start=2.2)
marker_cluster = MarkerCluster().add_to(m)

for _, row in country_df.iterrows():
    folium.Marker(
        location=[row['country_lat'], row['country_lon']],
        icon = folium.CustomIcon(f'https://flagcdn.com/w40/{row["code"]}.png', icon_size=(23, 12)),
        tooltip=row['country'],
    ).add_to(m)

for _, row in city_df.sample(5000).iterrows():
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=3,
        color='green',
        fill=True,
        fill_color='green',
        fill_opacity=0.3,
        popup=row['accent_city'],
    ).add_to(marker_cluster)

folium.GeoJson(
    geojson_data,
    style_function=lambda x: {
        'fillColor': 'none',    
        'color': '#4C9900',        
        'weight': 2           
    }
).add_to(m)
m

#%%
