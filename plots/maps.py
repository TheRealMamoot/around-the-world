from os import path, getcwd

import folium
from folium.plugins import MarkerCluster
import geopandas as gpd

def map_builder(initial_data, country_data, geojson, run=False):

    if not run:
        print('Map creation skipped!')
    
    else:
        city_dist = initial_data.groupby(['country','country_lat','country_lon','geometry','code']).agg(
            city_count = ('city', lambda x: x.count()),
            population = ('population', lambda x: x.sum()),
        ).reset_index()
        city_dist = gpd.GeoDataFrame(city_dist, geometry=city_dist['geometry'])

        m_country = folium.Map(location=[0, 0], zoom_start=2.2)
        m_country = city_dist.explore(m=m_country, column='city_count', cmap='Greens',legend=True)
        folium.GeoJson(
            geojson,
            style_function=lambda x: {
                'fillColor':'none',    
                'color':'#4C9900',        
                'weight':2           
            }
        ).add_to(m_country)

        for _, row in country_data.iterrows():
            folium.Marker(
                location=[row['country_lat'], row['country_lon']],
                icon = folium.CustomIcon(f'https://flagcdn.com/w40/{(row["code"]).lower()}.png', icon_size=(23, 11.5)),
                tooltip=row['code']
            ).add_to(m_country)

        m_city = folium.Map(location=[0, 0], zoom_start=2.2)

        marker_cluster = MarkerCluster().add_to(m_city)
        for _, row in initial_data.iterrows():
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
            geojson,
            style_function=lambda x: {
                'fillColor':'none',    
                'color':'#4C9900',        
                'weight':2,         
            }
        ).add_to(m_city)

        m_country.save(path.join(getcwd(), 'countries.html'))
        m_city.save(path.join(getcwd(), 'cities.html'))

        print(f'Maps saved at {getcwd()}')