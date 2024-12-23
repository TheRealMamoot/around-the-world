import numpy as np
from scipy.spatial import cKDTree

def calculate_haversine_distance(lat1, lon1, lat2, lon2, R=6371):

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    distance = R * c

    return distance

def determine_duration(nth_closest_point, 
                       population, 
                       change_country=False, 
                       n_neighbors_times=[2,4,8], 
                       add_hours_country=2,
                       add_hours_population=2,
                       population_limit=200000):
    '''
    Deteremines point to point duration based on pre-set criteria.
    Base times: [2,4,8] hours to travel to 1st, 2nd and 3rd closest points. 
    Increments 2h for high population and 2h for country change.
    All criteria adjustable!
    '''
    condition_matrix = np.array(n_neighbors_times) 

    condition_matrix = np.stack((condition_matrix, condition_matrix + add_hours_country), axis=1)
    condition_matrix = np.stack((condition_matrix, condition_matrix + add_hours_population), axis=0)

    high_population = np.where(population <= population_limit, 0, 1)

    return condition_matrix[int(change_country), nth_closest_point, high_population]

def identify_valid_points(points, lat_boundry=2):
    '''
    Identify valid neighbors for each point considering latitude boundaries.
    '''
    lat_condition = np.logical_and(
        points[:, 0][:, None] <= points[:, 0] + lat_boundry,
        points[:, 0][:, None] >= points[:, 0] - lat_boundry 
    )

    return lat_condition

def determine_closest_points(points, n=3):
    '''
    Caclulates closest points based on KDTrees.
    Due to the nature of latitudes and longitudes, 
    this function augments the input to create mirrored points for the other side of the meridian based on longitudes.
    Without this, the points are identified wrongly because of the earth's wrap around effect.
    '''
    points_augmented = np.copy(points)
    points_augmented[:, 1] = np.where(points[:, 1] < 0,
                                      points[:, 1] + 360,
                                      points[:, 1] - 360
                                      )
    points_augmented = np.vstack((points, points_augmented))

    tree = cKDTree(points_augmented)

    # n+1 to exclude the source 
    _, indices = tree.query(points, k=n+1)
    closest_idxs = indices[:,1:n+1]

    # finding the original index before augmentation
    num_original_points = len(points)
    mapped_closest_idxs = np.where(closest_idxs < num_original_points,
                                   closest_idxs,
                                   closest_idxs - num_original_points
                                   )
    return mapped_closest_idxs
