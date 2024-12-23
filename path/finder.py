import numpy as np

from path.optimizer import dijkstra
from utils import determine_closest_points

def path_finder(explorable_path, graph, vertices):
    '''
    Finds the shortest route (based on distance) with dijkstra and then adjusts the time needed for each point.
    Final distances in the reult dataframe are sorted, normalized and durations are adjusted using normalized distances.
    Input:
        explorable_path: PathExplorer(data, origin_city, origin_country, moving_direction)
        graph: Graph(adjacency_list)
        vertices (dict): dictionary containing Vertex(index, longitude)
    Output:
        chosen_path: shortest path found by dijkstra
        cost: total cost (distance) for the chosen_path
        result_df: final dataframe containing information for the shortest path found
    '''
    data = explorable_path.get_dataframe()
    origin_city = explorable_path.origin_city
    origin_country = explorable_path.origin_country
    origin = data.query(f'city=="{origin_city}" and code=="{origin_country}"')
    origin_lon_order = origin['lon_order'].values[0]
    origin_index = origin.index[0]

    '''finding the closest point to the origin to count as end. (closest previous neighbor in the graph)'''
    destination = data.loc[data['lon_order'].between(origin_lon_order - 20, origin_lon_order),:]
    destination = destination.reset_index().rename(columns={'index':'org_index'})

    previous_neighbors = destination[['lat','lon']].values
    prev_closest_neighbor = determine_closest_points(previous_neighbors, n=1)[-1]

    end_index = destination.loc[prev_closest_neighbor]['org_index'].values[0]

    start = vertices[origin_index]
    end = vertices[end_index]

    chosen_path, cost = dijkstra(graph, start, end)

    if len(chosen_path) < 2:
        print(f'Last reachable point: {data.loc[chosen_path[0]]["city"]} ({chosen_path[0]})')
        return
    
    result_df = data.loc[chosen_path]
    result_df = result_df.reset_index().rename(columns={'index':'org_index'})
    result_df['org_index'] = result_df['org_index'].shift(-1)
    result_df = result_df.explode(['adjacency_list','time_edges','distance_edges'])

    times = result_df.query('org_index == adjacency_list')['time_edges'].tolist()
    distances = result_df.query('org_index == adjacency_list')['distance_edges'].tolist()
    times = times + [min(times)] # final travel duration. from end point in the algorithm back to the origin city.
    distances = distances + [min(distances)] # adding final travel distance.

    result_df = data.loc[chosen_path]
    result_df['next_point_duration'] = times
    result_df['next_point_distance'] = distances

    result_df['normed_next_point_duration'] = result_df['next_point_distance'].rank(method='dense')
    max_dist = result_df['normed_next_point_duration'].max()
    min_dist = result_df['normed_next_point_duration'].min()
    result_df['distance_normalized'] = - 1 + ((result_df['normed_next_point_duration'] - min_dist) / (max_dist - min_dist)) * 2 # normalized to [-1,+1]
    result_df['normed_next_point_duration'] = np.ceil(result_df['next_point_duration'] + (result_df['next_point_duration'] * result_df['distance_normalized'])) # to adjust times based on the actual distance
    result_df['normed_next_point_duration'] = np.where(result_df['normed_next_point_duration'] < 1, 1, result_df['normed_next_point_duration'])
    
    new_times = result_df['normed_next_point_duration'].sum()
    distances = result_df['next_point_distance'].sum()

    print(f'Shortest time from {origin_city.capitalize()} and back: {int(new_times // 24)} days and {int(new_times % 24)} hours!')
    print(f'Distance traveled: {int(distances):,} KM')
    print(f'# Cities explored: {len(result_df)}')

    return chosen_path, cost, result_df