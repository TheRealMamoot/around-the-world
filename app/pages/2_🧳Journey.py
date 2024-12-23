import os
import sys
import time

import streamlit as st

from data_process import download_and_process_data
from path.explorer import PathExplorer
from path.finder import path_finder
from path.optimizer import Graph, Edge, Vertex
from plots.globe import JourneyPlanner
from utils import identify_valid_points

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(parent_dir)

st.set_page_config(page_title='Journey', page_icon='🧳', layout='wide')

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

st.subheader('🚶‍♂️ "It’s not about the destination, it’s about the journey."') 
st.markdown(
    '''
    <div style="text-align: justify; font-size: 18px; line-height: 1.6; margin-bottom: 20px;">
        Let's embark on this journey! You can begin from any city in the dataset such as London, Paris, Berlin, etc...
    </div>
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

location_df['display'] = location_df['accent_city'] + ', ' + location_df['country']
city_list = location_df['display'].sort_values().tolist()
default_city = 'London' 

if 'selected_option' not in st.session_state:
    default_option = f'{default_city}, {location_df.loc[location_df["accent_city"] == default_city, "country"].iloc[0]}'
    st.session_state.selected_option = default_option

col1, _, _ = st.columns(3)
selected_option = col1.selectbox(
    'Choose your starting city:',
    options=city_list,
    index=city_list.index(st.session_state.selected_option),
    help='Select a (city, country) to start your journey.'
)

st.session_state.selected_option = selected_option

selected_city, selected_country = selected_option.split(', ')
selected = location_df.query(f'accent_city == "{selected_city}" and country == "{selected_country}"').drop(columns=['geometry','display'])
st.dataframe(selected)
selected = selected.index[0]

st.markdown(
    '''
    <div style="text-align: justify; font-size: 18px; line-height: 1.6; margin-bottom: 20px;">
        Now, let’s talk about the direction of movement. You can either travel from east to west or vice versa. 
        When traveling due east or west, you are essentially moving along the same longitude. 
        Additionally, you can set a tolerance limit for how far the path can deviate north or south, 
        ensuring that the journey stays within a specified latitude boundary.
    </div>
    ''',
    unsafe_allow_html=True
)

if 'direction' not in st.session_state:
    st.session_state.direction = 'E'

cols = st.columns(6)
user_choice = cols[0].radio('Pick your direction', ['E', 'W'], index=['E', 'W'].index(st.session_state.direction))
st.session_state.direction = user_choice 
direction = st.session_state.direction

if 'latiude_boundary' not in st.session_state:
    st.session_state.latiude_boundary = 0.5

user_choice = cols[1].number_input('Latitude boundary', 
                                   step=0.5, 
                                   min_value=0.1, 
                                   max_value=10.0, 
                                   value=st.session_state.latiude_boundary,
                                   help='The boundary is in degrees.')

st.session_state.latiude_boundary = user_choice
latiude_boundary = st.session_state.latiude_boundary

st.markdown(
    '''
    <div style="text-align: justify; font-size: 18px; line-height: 1.6; margin-bottom: 20px;">
        The concept is to travel to a set number of nearby points from the origin city and onward, following the chosen direction of movement.
        Here, you can specify this number and adjust the travel time in <strong><em>hours</em></strong> to each point. Furthermore,
        you can tune the following constraints:
    </div>
        <ul style="list-style-type: disc; margin-left: 20px;">
            <li style="font-size: 18px;"><strong>Number of nearby points</strong>: Specify how many nearby points you can to travel to from each origin point and their times.</li>
            <li style="font-size: 18px;"><strong>Country change penalty</strong>: Apply additional time for traveling to a different country.</li>
            <li style="font-size: 18px;"><strong>High population penalty</strong>: Apply additional time for cities with high population density.</li>
            <li style="font-size: 18px;"><strong>High population limit</strong>: Limit for the population to count as high.</li>
        </ul>
    ''',
    unsafe_allow_html=True
)

cols = st.columns(4)

if 'number_of_neighbors' not in st.session_state:
    st.session_state.number_of_neighbors = 3
    st.session_state.added_country_hours = 2
    st.session_state.added_population_hours = 2
    st.session_state.population_limit = 200_000

number_of_neighbors = cols[0].number_input('Number of nearby points', step=1, min_value=3, max_value=10, value=st.session_state.number_of_neighbors)
added_country_hours = cols[1].number_input('Country change penalty', step=1, min_value=1, max_value=12, value=st.session_state.added_country_hours)
added_population_hours = cols[2].number_input('High population penalty', step=1, min_value=1, max_value=12, value=st.session_state.added_population_hours)
population_limit = cols[3].number_input('High population limit', step=5000, min_value=5000, max_value=1_000_000, value=st.session_state.population_limit)

st.session_state.number_of_neighbors = number_of_neighbors
st.session_state.added_country_hours = added_country_hours
st.session_state.added_population_hours = added_population_hours
st.session_state.population_limit = population_limit

cols = st.columns(number_of_neighbors) 

suffix = ['st', 'nd', 'rd', 'th']
inputs = {}

if 'inputs' not in st.session_state:
    st.session_state.inputs = {}

for i, col in enumerate(cols):
    value = 2 ** (i + 1)
    if value > 24:
        value = 16
    suf = suffix[i] if i <= 2 else suffix[-1]
    if i not in st.session_state.inputs:
        st.session_state.inputs[i] = value
    
    inputs[i] = col.number_input(f'{i+1}{suf} nearest point', step=1, min_value=1, max_value=24, value=st.session_state.inputs[i])
    st.session_state.inputs[i] = inputs[i]

conditions = []
for i in range(len(inputs.keys())-1):
    conditions.append(inputs[i+1] >= inputs[i])
        
if not all(conditions):
    st.warning('⚠️ Warning! Closer points must have lower times. Please review the inputs.')

st.markdown('<br>', unsafe_allow_html=True) 
st.markdown(
    '''
    <div style="text-align: center; font-size: 24px; line-height: 1.6; margin-bottom: 20px;">
        <strong>That's it! Only one more step and the journey begins! 🚀</strong>
    </div>
    ''',
    unsafe_allow_html=True
)

st.markdown(
    '''
    <div style="text-align: center; font-size: 24px; line-height: 1.6; margin-bottom: 20px;">
        Review your choices
    </div>
    ''',
    unsafe_allow_html=True
)
points = ''
for i, (key, value) in enumerate(inputs.items()):
    suf = suffix[i] if i <= 2 else suffix[-1]
    point = f'{i+1}{suf} Closest Point Time: <strong><em>{value} H</em></strong><br>\n'
    if i == number_of_neighbors - 1:
        point = f'{i+1}{suf} Closest Point Time: <strong><em>{value} H</em></strong><br>'
    points += point

cols = st.columns([1,1,1])
with cols[1].expander(f'Select to see the chosen criteria'):
    st.markdown(
    f'''
    <div style="text-align: left; font-size: 17px; line-height: 1.6; margin-bottom: 20px;">
        Origin City: <strong><em>{selected_city}, {selected_country}</em></strong><br>
        Direction: <strong><em>{"East" if direction=='E' else "West"}</em></strong><br>
        Latitude Boundary: ± <strong><em>{latiude_boundary}°</em></strong><br>
        Number of Valid Neighbors: <strong><em>{number_of_neighbors}</em></strong><br>
        {points}
        Country Change Penalty: <strong><em>{added_country_hours} H</em></strong><br>
        Population Limit: <strong><em>{added_population_hours} H</em></strong><br>
        Population Penalty: <strong><em>{population_limit:,.0f}</em></strong><br>
    </div>
    ''',
    unsafe_allow_html=True
)

cols = st.columns([1, 1, 1])

if 'ready_to_proceed' not in st.session_state:
    st.session_state.ready_to_proceed = False

ready_to_proceed = cols[1].checkbox("I am Ready!", value=st.session_state.ready_to_proceed)
st.session_state.ready_to_proceed = ready_to_proceed

cols = st.columns([1, 1, 1, 2, 1, 1, 1, 1, 1, 1])
if st.session_state.ready_to_proceed:
    proceed_button = cols[4].button("GO!")
    cols = st.columns([1, 2, 1])
    if proceed_button:
        progress = st.progress(0)
        status_text = st.empty() 

        total_steps = 6
        step_increment = 100 // total_steps 

        explorable_path = PathExplorer(location_df,
                                    origin_city=location_df.loc[selected]['city'],
                                    origin_country=location_df.loc[selected]['code'],
                                    moving_direction=direction,
                                    neighbors_times=list(inputs.values()),
                                    add_hours_country=added_country_hours,
                                    add_hours_population=added_population_hours,
                                    population_limit=population_limit
                                    )
        
        status_text.text('Exploring the Path...')
        progress.progress(step_increment)

        time.sleep(0.5) 

        valid_neighbors = identify_valid_points(location_df[['lat', 'lon']].values, lat_boundry=0.5)
        status_text.text('Identifying Valid Points...')
        progress.progress(step_increment * 2)

        time.sleep(0.5)

        explorable_path.prepare_explorable_path(valid_neighbors)
        status_text.text('Staying on Course...')
        progress.progress(step_increment * 3)

        time.sleep(0.5)

        explorable_path.filter_path()
        status_text.text('Findng Closer Neighbors ...')
        progress.progress(step_increment * 4)

        time.sleep(0.5)

        explorable_path_df = explorable_path.get_dataframe()
        status_text.text('Creating Potential Path Dataframe...')
        progress.progress(step_increment * 5)

        time.sleep(0.5)

        vertices_dict = {index: Vertex(index, row['lon']) for index, row in explorable_path_df.iterrows()}
        adjacency_list = {vertex: [] for vertex in vertices_dict.values()}

        for idx, row in explorable_path_df.iterrows():
            from_vertex = vertices_dict[idx]
            for adj, cost in zip(row['adjacency_list'], row['distance_edges']):
                to_vertex = vertices_dict[adj] 
                adjacency_list[from_vertex].append(Edge(cost, to_vertex))

        graph = Graph(adjacency_list)

        status_text.text('Creating the Graph and Finding the Path...')
        progress.progress(100) 

        time.sleep(1)

        path, cost, result = path_finder(explorable_path, graph, vertices_dict)

        status_text.text('Best Path Found!')

        time.sleep(1)

        status_text.text('')
        st.success('Journey Complete!')

        time.sleep(0.5)

        final_result = result.loc[:,~result.columns.isin(['code','city','geometry','display','lon_order',
                                                          'region','lat_rad','lon_rad'])]
        final_result.rename(columns= {'accent_city':'city', 'pop_est':'country_population'}, inplace=True)
        final_result['pace'] = final_result['next_point_distance'] / final_result['normed_next_point_duration']
        final_result['#'] = [i+1 for i in range(len(final_result))]

        total_time_days = int(final_result['normed_next_point_duration'].sum() // 24)
        total_time_hours = int(final_result['normed_next_point_duration'].sum() % 24)
        total_distance = final_result['next_point_distance'].sum()
        final_pace = total_distance / (total_time_days + total_time_hours)
        cities_explored = len(final_result)
        countries_explored = final_result['country'].nunique()
        average_pace = (final_result['pace']).mean()

        st.markdown(
            '''
            <div style="text-align: left; font-size: 24px; line-height: 1.6; margin-bottom: 10px;">
                <strong>📄 Report Metrics</strong>
            </div>
            ''',
            unsafe_allow_html=True
        )
        st.markdown('<hr style="border: 1px solid #D3D3D3; margin-top: 0px; margin-bottom: 2px;">', unsafe_allow_html=True)

        report_cols = st.columns([2,1,1,1,2])
        report_cols[0].metric(label='Total Distance Traveled', value=f'{total_distance:,} km')
        report_cols[0].metric(label='Total Time Spent', value=f'{total_time_days} days\n{total_time_hours} hours')
        report_cols[2].metric(label='Cities Explored', value = cities_explored)
        report_cols[2].metric(label='Countries Explored', value=countries_explored)
        report_cols[-1].metric(label='Final Pace', value=f'{final_pace:.2f} km/h')
        report_cols[-1].metric(label='Average Pace', value=f'{average_pace:.2f} km/h')

        st.markdown('<hr style="border: 1px solid #D3D3D3; margin-top: 0px; margin-bottom: 2px;">', unsafe_allow_html=True)

        st.markdown(
            '''
            <div style="text-align: left; font-size: 24px; line-height: 1.6; margin-bottom: 12px;">
                <strong>🛣️ The Shortest Path</strong>
            </div>
            ''',
            unsafe_allow_html=True
        )

        st.dataframe(final_result[['#','city','country','population','lat','lon','country_lat',
                                'country_lon','country_population','continent','adjacency_list','time_edges',
                                'distance_edges','next_point_duration','next_point_distance',
                                'normed_next_point_duration','distance_normalized','pace']])
        
        with st.expander(f'More info on the path dataframe'):
            st.markdown(
            f'''
            <div style="text-align: left; font-size: 15px; line-height: 1.6; margin-bottom: 20px;">
                <strong><em>adjacency_list:</em></strong> Indexes of the closest neighbors for each node in the graph within the dataframe.<br>
                <strong><em>time_edges:</em></strong> Time required to travel from each node to its neighbors,<br>
                <strong><em>distance_edges:</em></strong> Distance required to travel from each node to its neighbors.<br>
                <strong><em>distance_normalized:</em></strong> Values range between -1 and 1, representing the normalized distance.<br>
                <strong><em>normed_next_point_duration:</em></strong> Normalized duration based on the normalized distance, calculated as <code>norm_dur = dur + (dur * norm_dist)</code>.<br>
            </div>
            ''',
            unsafe_allow_html=True
        )
            
        st.markdown(
            '''
            <div style="text-align: left; font-size: 24px; line-height: 1.6; margin-bottom: 10px;">
                <strong>🌏 Full Circle</strong>
            </div>
            ''',
            unsafe_allow_html=True
        )

        globe = JourneyPlanner(result, 
                                explorable_path.moving_direction,
                                explorable_path.origin_city)
        
        status_text = st.empty() 
        status_text.text('Please wait for the globe...')
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        total_steps = 10 
        step_increment = 100 // total_steps

        for step in range(total_steps-1):
            progress_bar.progress(step_increment * (step + 1))
            status_text.text(f'Processing...')
            time.sleep(0.5) 

        journey = globe.show()

        status_text.text('')
        st.success('Globe Complete!')
        progress_bar.progress(100)
        st.plotly_chart(journey, use_container_width=False)

    else:
        cols[1].info('Click to start the Journey and find the best Path!')