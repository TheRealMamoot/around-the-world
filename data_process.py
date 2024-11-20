import os
import requests

import country_converter as coco
import glob
import geopandas as gpd
from kaggle.api.kaggle_api_extended import KaggleApi
import numpy as np
import pandas as pd
from shapely.geometry import shape

def download_and_process_data():
    '''
    Downloads a world cities dataset from Kaggle, processes the city and country data, 
    and merges them with country centroids and world map data.
    Must have a kaggle api present in .kaggle folder.
    '''
    dataset='max-mind/world-cities-database'
    country_url='https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json'

    # Check Kaggle credentials and create directory if needed
    download_path = os.path.join(os.getcwd(), 'data')
    if not os.path.exists(os.path.expanduser('~/.kaggle/kaggle.json')):
        raise FileNotFoundError('Kaggle API key not found. Please place your kaggle.json in the ~/.kaggle folder.')

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    # Download the dataset if the directory is empty
    if len(os.listdir(download_path)) == 0:
        api = KaggleApi()
        api.authenticate()
        print(f'Downloading dataset "{dataset}" to "{download_path}"...')
        api.dataset_download_files(dataset, path=download_path, unzip=True)
        print('Download complete!')
    
    try:
        data = pd.read_csv(glob.glob(f'{download_path}/*.csv')[0])
    except IndexError:
        raise FileNotFoundError('No CSV file found in the data directory.')

    # Process city data
    loc_df = data.copy()
    loc_df.columns = [col.lower() for col in loc_df.columns]
    loc_df.rename(columns={'country': 'code', 
                           'accentcity': 'accent_city', 
                           'latitude': 'lat', 
                           'longitude': 'lon'
                           }, inplace=True)
    loc_df.sort_values('population', ascending=False, inplace=True)
    loc_df.drop_duplicates(subset=['lat', 'lon'], keep='first', inplace=True)
    loc_df['lat_rad'] = np.radians(loc_df['lat'])
    loc_df['lon_rad'] = np.radians(loc_df['lon'])
    loc_df['code'] = loc_df['code'].apply(lambda x: x.upper())
    loc_df.dropna(subset=['population'], inplace=True)

    geojson_data = requests.get(country_url).json()
    country_df = pd.DataFrame()

    for index, feature in enumerate(geojson_data['features']):
        geometry = shape(feature['geometry'])
        centroid = geometry.centroid
        country_df.loc[index, 'country'] = feature['properties']['name']
        country_df.loc[index, 'country_lat'] = centroid.y
        country_df.loc[index, 'country_lon'] = centroid.x

    country_df['code'] = coco.convert(names=country_df['country'], to='ISO2')

    world_gdf = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    world_gdf['code'] = coco.convert(names=world_gdf['iso_a3'], to='ISO2')
    country_df = pd.merge(country_df, 
                          world_gdf.drop(['name', 'iso_a3', 'gdp_md_est'], axis=1).query('code != "not found"'), 
                          on='code')

    loc_df = pd.merge(loc_df, country_df, on='code')

    return loc_df, country_df, geojson_data