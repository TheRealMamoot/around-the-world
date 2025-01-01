Welcome to **around-the-world** repository! This project combines optimization, geography, and exploration. The goal? To determine how quickly one can circumnavigate the globe, starting and ending at a chosen point, while visiting nearby cities and adhering to constraints like distance, population, a change in country and most importantly, travel direction.
Please vist [The Journey App](http://13.49.21.144:8501) for an interactive experience of the final result.

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
1. **Clone the GitHub repository**:
```
git clone https://github.com/TheRealMamoot/around-the-world.git
cd around-the-world.git/
```
2. **Install the required dependencies**:
```
pip install -r requirements.txt
```
3. **Obtain kaggle API**:
	- Download your **kaggle.json** file by creating a new API token [here](https://www.kaggle.com/settings/account).
 	- Place the kaggle.json file in the root directory of the project. Visit the [Kaggle website](https://www.kaggle.com/docs/api#authentication) for more information.

