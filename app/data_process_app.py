import os
import requests
import tempfile

import country_converter as coco
import glob
import geopandas as gpd
from kaggle.api.kaggle_api_extended import KaggleApi
import numpy as np
import pandas as pd
from shapely.geometry import shape
import streamlit as st

def download_and_process_data():
    '''
    Downloads a world cities dataset from Kaggle, processes the city and country data, 
    and merges them with country centroids and world map data.
    Requires Kaggle API credentials stored in Streamlit secrets.
    '''
    dataset = 'max-mind/world-cities-database'
    country_url = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json'

    if not st.secrets.get('kaggle'):
        raise FileNotFoundError('Kaggle API credentials not found in Streamlit secrets.')

    kaggle_username = st.secrets['kaggle']['username']
    kaggle_key = st.secrets['kaggle']['key']
    os.environ['KAGGLE_USERNAME'] = kaggle_username
    os.environ['KAGGLE_KEY'] = kaggle_key

    api = KaggleApi()
    api.authenticate()

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f'Downloading dataset "{dataset}" to temporary directory...')
        api.dataset_download_files(dataset, path=temp_dir, unzip=True)
        print('Download complete!')

        try:
            data = pd.read_csv(glob.glob(f'{temp_dir}/*.csv')[0])
        except IndexError:
            raise FileNotFoundError('No CSV file found in the temporary directory.')

        loc_df = data.copy()
        loc_df.columns = [col.lower() for col in loc_df.columns]
        loc_df.rename(columns={'country': 'code', 
                               'accentcity': 'accent_city', 
                               'latitude': 'lat', 
                               'longitude': 'lon'}, inplace=True)
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