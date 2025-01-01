import utils

class PathExplorer:
    def __init__(self, data, 
                 origin_city: str, 
                 origin_country: str,
                 moving_direction: str,
                 neighbors_times: list,
                 add_hours_country: int,
                 add_hours_population: int,
                 population_limit: int):
        if moving_direction not in ['E', 'W']:
            raise ValueError('Invalid moving direction. Must be "E" (East) or "W" (West).')
        
        self.data = data
        self.origin_city = origin_city
        self.origin_country = origin_country
        self.moving_direction = moving_direction
        self.neighbors_times = neighbors_times
        self.add_hours_country = add_hours_country
        self.add_hours_population = add_hours_population
        self.population_limit = population_limit
        self.origin_index = self._get_origin_index()
        self.explorable_path_df = None
        self.path_limit_thresh = 0.005  # Default path limit threshold
        self.neighbors = []
        self.times = []
        self.all_distances = []

    def _get_origin_index(self):
        origin = self.data.query(f'city == "{self.origin_city}" and code == "{self.origin_country}"')
        if origin.empty:
            raise ValueError('Origin city not found in the dataset!')
        return origin.index[0]

    def prepare_explorable_path(self, valid_neighbors):
        """
        Prepares a general path based on the origin point's all valid neighbors in the target direction. 
        """
        self.explorable_path_df = self.data.loc[valid_neighbors[self.origin_index]].reset_index(drop=True)
        self._sort_longitudes()

    def _sort_longitudes(self):
        """
        Customly sorts longitudes to bypass the wrap-around effect.
        """
        longitudes = self.explorable_path_df['lon'].tolist()
        zero_lons = [lon for lon in longitudes if lon == 0]
        positives_lons = sorted([lon for lon in longitudes if lon > 0])
        negatives_lons = sorted([lon for lon in longitudes if lon < 0])
        sorted_lons = zero_lons + positives_lons + negatives_lons
        
        if self.moving_direction == 'W':
            positives_lons.reverse()
            negatives_lons.reverse()
            sorted_lons = zero_lons + negatives_lons + positives_lons
        
        lon_order_mapping = {lon: i for i, lon in enumerate(sorted_lons)}
        self.explorable_path_df['lon_order'] = self.explorable_path_df['lon'].map(lon_order_mapping)
        self.explorable_path_df.sort_values('lon_order', inplace=True)

    def filter_path(self):
        """
        Filters a number of points based on the percentile of custom-sorted longitudes for each point,
        sets the limit of the percentile to get close points,
        and finally finds the valid #n closests neghbors (adjacent list) and time/distance needed to travel to each point (edges).
        """

        self.neighbors = []
        self.times = []
        self.all_distances = []
        
        for _, row in self.explorable_path_df.iterrows():
            path_df = self.explorable_path_df.copy()

            # shift longitudes and calculate rankings
            lon_rankings, shifted_lons = self._shift_and_rank_longitudes(path_df, row)
            path_df['lon_rank'] = path_df['lon'].map(lon_rankings)
            path_df['lon_rank_pct'] = path_df['lon_rank'].rank(pct=True)

            # apply path limit threshold and filter paths
            filtered_path_df = self._apply_path_limit(path_df)
            
            # find neighbors and calculate time for each path
            current_point_country = row['country']
            self._find_neighbors_and_calculate_time(row, filtered_path_df, current_point_country)

        self.explorable_path_df['adjacency_list'] = self.neighbors
        self.explorable_path_df['time_edges'] = self.times
        self.explorable_path_df['distance_edges'] = self.all_distances

    def _shift_and_rank_longitudes(self, path_df, row):
        origin_sorted_index = list(path_df['lon']).index(row['lon'])
        shifted_lons = path_df['lon'].iloc[origin_sorted_index:].tolist() + path_df['lon'].iloc[:origin_sorted_index].tolist()
        lon_rankings = {value: rank for rank, value in enumerate(shifted_lons)}
        return lon_rankings, shifted_lons

    def _apply_path_limit(self, path_df):
        filtered_path_df = path_df.loc[path_df['lon_rank_pct'] <= self.path_limit_thresh]
        filtered_path_df = filtered_path_df.sort_values('lon_rank_pct').reset_index().rename(columns={'index': 'org_index'})
        while len(filtered_path_df) < 20:
            self.path_limit_thresh += 0.01
            filtered_path_df = path_df.loc[path_df['lon_rank_pct'] <= self.path_limit_thresh]
            filtered_path_df = filtered_path_df.sort_values('lon_rank_pct').reset_index().rename(columns={'index': 'org_index'})
        return filtered_path_df
    
    def _find_neighbors_and_calculate_time(self, row, filtered_path_df, current_point_country):
        points = filtered_path_df[['lat', 'lon']].values
        closest_idxs = utils.determine_closest_points(points, n=len(self.neighbors_times))
        indices_in_explorable_path = filtered_path_df.loc[closest_idxs[0]]['org_index'].values
        self.neighbors.append(indices_in_explorable_path)

        durations, distances = [], []
        for idx, filtered_idx in enumerate(closest_idxs[0]):
            potential_next_point_population = filtered_path_df.loc[filtered_idx]['population']
            potential_next_point_country = filtered_path_df.loc[filtered_idx]['country']
            country_change = current_point_country != potential_next_point_country

            distance = utils.calculate_haversine_distance(
                row['lat_rad'], row['lon_rad'],
                filtered_path_df.loc[filtered_idx]['lat_rad'],
                filtered_path_df.loc[filtered_idx]['lon_rad']
            )
            duration = utils.determine_duration(
                idx, potential_next_point_population, country_change,
                self.neighbors_times, self.add_hours_country, self.add_hours_population, self.population_limit
            )
            durations.append(duration)
            distances.append(round(distance))

        self.times.append(durations)
        self.all_distances.append(distances)

    def get_dataframe(self):
        return self.explorable_path_df