import os
import sys

import streamlit as st
from streamlit_folium import st_folium

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
print(parent_dir)
sys.path.append(parent_dir)

from data_process import download_and_process_data
from plots.maps import MapBuilder

st.set_page_config(page_title='Data', page_icon='📁', layout='wide')

st.markdown(
    '''
    <style>
        .block-container {
            max-width: 1000px; 
            padding-left: 20px;
            padding-right: 20px;
        }
    </style>
    ''',
    unsafe_allow_html=True
)

if 'location_df' not in st.session_state:
    location_df, country_df, geojson_data = download_and_process_data()
    st.session_state.location_df = location_df
    st.session_state.country_df = country_df
    st.session_state.geojson_data = geojson_data
else:
    location_df = st.session_state.location_df
    country_df = st.session_state.country_df
    geojson_data = st.session_state.geojson_data

st.subheader('🗂️ Dataset Preview') 
st.markdown(
    f'''
    <div style="text-align: justify; font-size: 18px; line-height: 1.6; margin-bottom: 20px;">
        The original dataset contains over 3 million rows. However, the majority of these records are not cities; 
        they include neighborhoods, districts, and other locations. Additionally, since population data is necessary 
        for calculating the total travel time, rows without population data have been removed.
        This process leaves us with the following:
        <ul style="list-style-type: disc; margin-left: 20px;">
            <li style="font-size: 18px;">Total Cities: <strong>{(location_df['city'].count()):03,.0f}</strong></li>
            <li style="font-size: 18px;">Total Countries: <strong>{location_df['country'].nunique()}</strong></li>
        </ul>
        A couple other datasets have been merged with the original data to aquire further information for the points,
        such as full country name, country geometry (borders, polygons, etc) and others.
    </div>
    ''',
    unsafe_allow_html=True
)

if 'df_input_number' not in st.session_state:
    st.session_state.df_input_number = 20 
    if 'filtered_data' not in st.session_state:
        st.session_state.filtered_data = location_df.loc[:,~location_df.columns.isin(['geometry'])].head(st.session_state.df_input_number)

col1, _, _, _ = st.columns(4) # for smaller user input
df_input_number = col1.number_input(
    'Enter the sample number for cities:',
    min_value=1,
    max_value=location_df['city'].count(),
    value=st.session_state.df_input_number,
    step=1
)

st.session_state.df_input_number = df_input_number
filtered_data = location_df.head(st.session_state.df_input_number)
st.session_state.filtered_data = filtered_data

st.dataframe(st.session_state.filtered_data) 

st.subheader('🗺️ Interactive Maps') 
st.markdown(
    f'''
    <div style="text-align: justify; font-size: 18px; line-height: 1.6; margin-bottom: 20px;">
        Below, you can see the placement of a random sample of cities from the dataset. 
        Additionally, the population of each country and the number of cities in each country are also displayed.
        You can choose the sample number, however selecting a very high number for the map sample may cause the project to run slowly.
    </div>
    ''',
    unsafe_allow_html=True
)

if 'map_input_number' not in st.session_state:
    st.session_state.map_input_number = 1000
    if 'location_df_filtered' not in st.session_state:
        st.session_state.location_df_filtered = location_df.sample(st.session_state.map_input_number, random_state=42)
        if 'maps' not in st.session_state:
            st.session_state.maps = MapBuilder(st.session_state.location_df_filtered, country_df, geojson_data)

col1, _, _, _ = st.columns(4)
map_input_number = col1.number_input(
    'Enter the number of cities for the map:',
    min_value=1,
    max_value=location_df['city'].count(),
    value=st.session_state.map_input_number,
    step=500
)

st.session_state.map_input_number = map_input_number
location_df_filtered = location_df.sample(st.session_state.map_input_number, random_state=42)
st.session_state.location_df_filtered = location_df_filtered
st.session_state.maps = MapBuilder(st.session_state.location_df_filtered, country_df, geojson_data)

st_folium(st.session_state.maps.city_map(), width=1100, height=500)
st_folium(st.session_state.maps.country_map('Greens'), width=1100, height=500)