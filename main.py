import warnings

from data_process import download_and_process_data
from path.explorer import PathExplorer
from path.optimizer import Graph, Edge, Vertex
from path.finder import path_finder
from plots.globe import gif_maker
from plots.maps import map_builder
from utils import identify_valid_points

warnings.filterwarnings('ignore')

location_df, country_df, geojson_data = download_and_process_data()

explorable_path = PathExplorer(location_df,
                               origin_city='london',
                               origin_country='GB',
                               moving_direction='E')

valid_neighbors = identify_valid_points(location_df[['lat', 'lon']].values, lat_boundry=0.5)
explorable_path.prepare_explorable_path(valid_neighbors)
explorable_path.filter_path()
explorable_path_df = explorable_path.get_dataframe()

vertices_dict = {index: Vertex(index, row['lon']) for index, row in explorable_path_df.iterrows()}
adjacency_list = {vertex: [] for vertex in vertices_dict.values()}

for idx, row in explorable_path_df.iterrows():
    from_vertex = vertices_dict[idx]
    for adj, time in zip(row['adjacency_list'], row['distance_edges']):
        to_vertex = vertices_dict[adj] 
        adjacency_list[from_vertex].append(Edge(time, to_vertex))

graph = Graph(adjacency_list)

path, cost, result = path_finder(explorable_path, graph, vertices_dict)

gif_maker(result, explorable_path.moving_direction, explorable_path.origin_city, run=False)
map_builder(location_df, country_df, geojson_data, run=True)