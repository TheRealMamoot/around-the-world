import warnings

import streamlit as st

warnings.filterwarnings('ignore')

st.set_page_config(
    page_title='Around the World',
    page_icon='🌍',
    layout='wide')

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

st.title('🌍 Around the World in How Many Days?!')
st.subheader('Explore, Optimize and Find the best Path!')
st.markdown(
    '''
    <div style="text-align: justify; font-size: 18px; line-height: 1.6; margin-bottom: 20px;">
        Welcome to this exciting project that combines optimization, geography, and exploration. 
        The goal? To determine how quickly one can circumnavigate the globe, starting and 
        ending at a chosen point, while visiting nearby cities and adhering to constraints 
        like distance, population, a change in country and most importantly, travel direction.
    </div>
    ''',
    unsafe_allow_html=True
)

st.markdown(
    '''
    <div style="position: relative; width: 70%; margin: 0 auto; margin-top: 10px; margin-bottom: 15px;">
        <img src="https://thechap.co.uk/wp-content/uploads/2022/01/jules-verne-map.jpg"
            style="width: 100%; height: auto; object-fit: cover; opacity: 0.9;">
        <p style="text-align: center; font-size: 14px; color: gray; margin-top: 10px; font-style: italic;">
            Phileas Fogg's journey in the book "Around the World in 80 Days"
        </p>
    </div>
    ''',
    unsafe_allow_html=True
)
st.subheader('🔍 What is This Project About?')
st.markdown(
    '''
    <div style="text-align: justify; font-size: 18px; line-height: 1.6; margin-bottom: 20px;">
        This project investigates:
        <ul style="list-style-type: disc; margin-left: 20px; font-size: 18px; line-height: 1.6;">
            <li style="font-size: 18px;">Whether it's possible to complete a journey around the world starting at one point.</li>
            <li style="font-size: 18px;">How to calculate the minimum travel time between cities while adhering to constraints.</li>
            <li style="font-size: 18px;">The use of k-dimensional trees (k-D trees) and Dijkstra's algorithm to solve the optimization problem of traveling efficiently.</li>
        </ul>
    </div>
    ''',
    unsafe_allow_html=True
)

st.markdown(
    '''
    <div style="text-align: center; margin-top: 5px;">
        <iframe src="https://giphy.com/embed/fyOoe8Wh0oKdw1XNxh" 
                width="350" height="350" 
                style="border:none; margin: 0 auto;" 
                frameBorder="0" class="giphy-embed" allowFullScreen>
        </iframe>
        <p style="font-size: 14px; color: gray; font-style: italic;">Around the world by Daft Punk!</p>
    </div>
    ''',
    unsafe_allow_html=True
)
video_id = 'K0HSD_i2DvA' # Daft Punk around the world
# YouTube embed URL with autoplay, mute set to false, and controls hidden
video_url = f'https://www.youtube.com/embed/{video_id}?autoplay=1&mute=0&controls=0&loop=1&playlist={video_id}'
# Embed the YouTube video with a tiny size to hide it but still play the audio
st.markdown(f'<iframe src="{video_url}" width="1" height="1" style="border:none;" '
            f'frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>', 
            unsafe_allow_html=True)

st.subheader('⚖️ Journey Constraints')
st.markdown(
    '''
    <div style="text-align: justify; font-size: 18px; line-height: 1.6;">
        This project works with a <a href="https://www.kaggle.com/datasets/max-mind/world-cities-database?select=worldcitiespop.csv" target="_blank" style="color: #1f77b4; text-decoration: none;">dataset</a> of major cities worldwide, assuming it’s always possible to travel 
        from any city to a number of nearest neighbors (Default is 3) to either east or west. 
        All the constraints are adjustable but the default is structured as follows:
        <ul style="list-style-type: disc; margin-left: 20px; font-size: 18px; line-height: 1.6;">
            <li style="font-size: 18px;">2 hours to the nearest city.</li>
            <li style="font-size: 18px;">4 hours to the second nearest city.</li>
            <li style="font-size: 18px;">8 hours to the third nearest city.</li>
        </ul>
        Additional conditions apply:
        <ul style="list-style-type: disc; margin-left: 20px; font-size: 18px; line-height: 1.6;">
            <li style="font-size: 18px;">+2 hours for crossing into a different country.</li>
            <li style="font-size: 18px;">+2 hours for traveling to a city with a population over 200,000.</li>
        </ul>
        The objective is to determine whether it's possible to circumnavigate the globe starting in London, always traveling east, and returning to London within 80 days. The goal is to compute the minimum travel time required for this journey.
    </div>
    ''',
    unsafe_allow_html=True
)
st.markdown('<br>', unsafe_allow_html=True) 
st.subheader('🚀 Get Started!')
st.markdown(
    '''
    <div style="text-align: justify; font-size: 20px; font-weight: bold; line-height: 1.8; margin-bottom: 10px;">
        Ready to Dive In?
    </div>
    <div style="text-align: justify; font-size: 18px; line-height: 1.6;">
        <p style="font-size: 18px;">Use the navigation sidebar to explore different sections:</p>
        <ul style="list-style-type: disc; margin-left: 20px;">
            <li style="font-size: 18px;">Visualize the path on the globe!</li>
            <li style="font-size: 18px;">Experiment with your own starting point and constraints!</li>
            <li style="font-size: 18px;">See the cities on the map!</li>
            <li style="font-size: 18px;">Learn more about the algorithms used!</li>
        </ul>
    </div>
    ''',
    unsafe_allow_html=True
)
st.markdown('---')
st.write(
    'Created with ❤️ by Alireza Mahmoudian.'
)
st.write(
    'Connect with me! 🤝🏼'
)
st.markdown(
    '''
    <div style="text-align: left; font-size: 16px; line-height: 1.6;">
        <div style="display: flex; gap: 15px; align-items: center;">
            <a href="https://www.linkedin.com/in/alireza-mahmoudian-5b0276246/" target="_blank">
                <img src="https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png" 
                    alt="LinkedIn" style="width: 40px; height: 40px;"/>
            </a>
            <a href="https://github.com/TheRealMamoot" target="_blank">
                <img src="https://upload.wikimedia.org/wikipedia/commons/2/24/Github_logo_svg.svg" 
                    alt="GitHub" style="width: 40px; height: 40px;"/>
            </a>
            <a href="mailto:alireza.mahmoudian.am@gmail.com">
                <img src="https://upload.wikimedia.org/wikipedia/commons/0/0b/Logo_Gmail_%282015-2020%29.svg" 
                    alt="Email" style="width: 40px; height: 40px;"/>
            </a>
        </div>
    </div>
    ''',
    unsafe_allow_html=True
)