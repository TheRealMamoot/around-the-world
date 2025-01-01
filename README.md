Welcome to **around-the-world** repository! This project combines optimization, geography, and exploration. The goal? To determine how quickly one can circumnavigate the globe, starting and ending at a chosen point, while visiting nearby cities and adhering to constraints like distance, population, a change in country and most importantly, travel direction.
Please vist [The Journey App](http://0.0.0.0:8501) for an interactive experience of the final result.

<h1 align="center">Around the World in 80 Days ?!</h1>

<p align="center">
<img src="https://github.com/TheRealMamoot/around-the-world/blob/881011e0130fbd7f4159ad8ff390c7517e92ecd4/journey.gif" width="600" height="600" />
</p>

<p align="center"><em>Like what you see ? You can create your own! Keep reading...</em></p>

## Table of Contents

## 🔍 About

The project explores the feasibility of completing a journey around the world starting from a specific point while calculating the minimum travel time between cities under defined constraints. It leverages Dijkstra’s algorithm and k-dimensional trees (k-D trees), to optimize the travel path efficiently.

The [dataset](https://www.kaggle.com/datasets/max-mind/world-cities-database?select=worldcitiespop.csv) used consists of major cities worldwide, with the assumption that travel is always possible to a number of nearest neighbors (default is 3) either eastward or westward. Constraints are customizable, but the default configuration includes the following:
-	**Base Travel Times**:
    -	2 hours to the nearest city.
    - 4 hours to the second nearest city.
    - 8 hours to the third nearest city.
-	**Additional Conditions**:
	-	+2 hours for crossing into a different country.
	-	+2 hours for traveling to a city with a population exceeding 200,000.

## ✨ Features
- Visualize the path on a 3D globe.
- Experiment with your own starting point and adjust constraints such as travel times and penalties.
- View cities and travel connections on an interactive map.
- Create custom GIFs to showcase your journey and exploration.
- Analyze the chosen path in detail, including every point’s neighbors, distances, and travel times.
- Learn more about the algorithms used.
  
## ⚙️ Usage
1. **Clone the GitHub repository**
```
git clone https://github.com/TheRealMamoot/around-the-world.git
cd around-the-world.git/
```
2. **Install the required dependencies**
```
pip install -r requirements.txt
```
3. **Obtain kaggle API**
	- Download your **kaggle.json** file by creating a new API token [here](https://www.kaggle.com/settings/account).
 	- Place the kaggle.json file in the root directory of the project. Visit the [Kaggle website](https://www.kaggle.com/docs/api#authentication) for more information.
4. **Run the code**
\
There are two ways to run the code:
* ***Streamlit (Recommended)***:
Use Streamlit to launch your own local web application and explore the project interactively, similar to the [Journey App](http://0.0.0.0:8501).
Run the following commands:
```
cd app
streamlit run Home.py
```
While you can deploy the app to Streamlit Cloud, the platform’s memory limits may restrict full functionality. For best results, consider deploying the app on alternative cloud services with higher memory capacity.
The result should be like this:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://<your.private.IP.address:8501>

  For better performance, install the Watchdog module:

  $ xcode-select --install
  $ pip install watchdog
```
The web app is highly customizable—feel free to explore, interact, and share your feedback!
* ***Python***: You can run the project directly using Python, allowing you to customize the code in `main.py`.
```
python main.py
```
To adjust the initial constraints, modify the instantiation of the `PathExplorer` class as needed.
```python
explorable_path = PathExplorer(location_df,
                               origin_city='london', # All lower case letters.
                               origin_country='GB', # ISO2 country name convention.
                               moving_direction='E', # "E" for east and "W" for west.
                               neighbors_times=[2,4,8], # 3 valid close neighbors. 2h hours to reach the first, 4h to second and 8h to the third closest neighbor
                               add_hours_country=2,
                               add_hours_population=2,
                               population_limit=200_000)
```
You can add more viable points and their durations by modifying the ```neighbors_times``` argument. Simply include additional elements with their respective travel times to expand the options. For instance: 
```python 
neighbors_times=[2,3,5,7,9,11]
```
This means that each point can travel to its six closest neighbors, with the travel times corresponding to each index in the list (e.g., 2 hours for the closest neighbor, 3 hours for the second closest, and so on).
You can also create your own GIF! Simply set the ```make_gif``` argument to ```True``` when instantiating the ```JourneyPlanner``` class. ```globe.gif()``` will create the GIF.
```python
globe = JourneyPlanner(result,
		       explorable_path.moving_direction,
   		       explorable_path.origin_city,
 	               frame_dir='frames', # Temporary directory to save each frame of the GIF.
 	               gif_name='journey.gif',
		       make_gif=True)
journey = globe.show()
globe.gif()
```
And last but not least, you can create and save interactive 2D maps (see the ***“Data”*** page in [The Journey App](http://0.0.0.0:8501)) as HTML files by setting ```save=True``` in the last couple of lines of the code.
```python
maps = MapBuilder(location_df, country_df, geojson_data)
map_country = maps.country_map('Greens')
map_city = maps.city_map()
maps.save_map(map_country, 'countries.html', save=True)
maps.save_map(map_city, 'cities.html', save=True)
```
 


