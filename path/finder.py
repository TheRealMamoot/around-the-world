import pandas as pd

from path.optimizer import dijkstra
from utils import determine_closest_points

def path_finder(path, graph, vertices):

    data = path.get_dataframe()
    origin_city = path.origin_city
    origin_country = path.origin_country
    origin = data.query(f'city=="{origin_city}" and code=="{origin_country}"')
    origin_lon_order = origin['lon_order'].values[0]
    origin_index = origin.index[0]

    # finding the closest point to the origin to count as end. (closest previous neighbor in the graph)
    destination = data.loc[data['lon_order'].between(origin_lon_order - 20, origin_lon_order),:]
    destination = destination.reset_index().rename(columns={'index':'org_index'})

    previous_neighbors = destination[['lat','lon']].values
    prev_closest_neighbor = determine_closest_points(previous_neighbors, n=1)[-1]

    end_index = destination.loc[prev_closest_neighbor]['org_index'].values[0]

    start = vertices[origin_index]
    end = vertices[end_index]

    path, time = dijkstra(graph, start, end)

    result_df = data.loc[path]
    result_df = result_df.reset_index().rename(columns={'index':'org_index'})
    result_df['org_index'] = result_df['org_index'].shift(-1)
    result_df = result_df.explode(['adjacent_matrix','edges'])

    times = result_df.query('org_index == adjacent_matrix')['edges'].tolist()
    times = times + [2] # final travel duration. from end point in the algorithm back to the origin city.

    result_df = data.loc[path]
    result_df['next_point_duration'] = times

    if len(path) < 2:
        print('No direct path found!')
        print(f'Last reachable point: {data.loc[path[0]]['city']} ({path[0]}) in {(time/24):.2f} days!')
    else:
        print(f'Shortest time from {origin_city.capitalize()} and back: {int(sum(times)//24)} days and {int(sum(times)%24)} hours!')
        print(f'Journey: {result_df["city"].tolist()}')
        print(f'# Cities explored: {len(result_df)}')

    return path, result_df, origin_index