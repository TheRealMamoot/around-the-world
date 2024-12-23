from os import path, getcwd

import folium
from folium.plugins import MarkerCluster
import geopandas as gpd

class MapBuilder:
    def __init__(self, initial_data, country_data, geojson):
        self.initial_data = initial_data
        self.country_data = country_data
        self.geojson = geojson

    def city_data(self):
        city_dist = self.initial_data.groupby(['country','country_lat','country_lon','geometry','code']).agg(
            city_count = ('city', lambda x: x.count()),
            population = ('population', lambda x: x.sum()),
        ).reset_index()
        city_dist = gpd.GeoDataFrame(city_dist, geometry=city_dist['geometry'])
        return city_dist
    
    def country_map(self, cmap: str):
        m_country = folium.Map(location=[0, 0], zoom_start=2, tiles='Cartodb dark_matter')
        m_country = self.city_data().explore(m=m_country, column='city_count', cmap=cmap, legend=True)
        folium.GeoJson(
                self.geojson,
                style_function=lambda x: {
                    'fillColor':'none',    
                    'color':'#4C9900',        
                    'weight':2,         
                }).add_to(m_country)
        for _, row in self.country_data.iterrows():
            folium.Marker(
                location=[row['country_lat'], row['country_lon']],
                icon = folium.CustomIcon(f'https://flagcdn.com/w40/{(row["code"]).lower()}.png', icon_size=(23, 11.5)),
                tooltip=row['code']
            ).add_to(m_country)
        return m_country
    
    def city_map(self):
        m_city = folium.Map(location=[0, 0], zoom_start=2, tiles='Cartodb dark_matter')
        marker_cluster = MarkerCluster().add_to(m_city)
        for _, row in self.initial_data.iterrows():
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
            self.geojson,
            style_function=lambda x: {
                'fillColor':'none',    
                'color':'#4C9900',        
                'weight':2,         
            }).add_to(m_city)
        return m_city
        
    @staticmethod
    def save_map(map, name: str, save=False):
        if save:
            map.save(path.join(getcwd(), name))
            print(f'{name} saved at {getcwd()}')