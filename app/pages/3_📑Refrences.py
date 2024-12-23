import streamlit as st

st.set_page_config(
    page_title='Refrences',
    page_icon='📑',
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

st.subheader('📚 The Reference Expedition')
st.markdown(
    f'''
    <div style="text-align: justify; font-size: 18px; line-height: 1.6; margin-bottom: 20px;">
        Thank you for exploring and engaging with this project. 
        Below, you’ll find the references for the concepts discussed and explored throughout.
        <div style="margin-top: 10px;"> 
        <ul style="list-style-type: disc; margin-left: 20px;">
            <li style="font-size: 18px;">
                <strong>
                    <a href="https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm" target="_blank">
                        Dijkstra's Algorithm - Wikipedia
                    </a>
                </strong>
            </li>
            <li style="font-size: 18px;">
                <strong>
                    <a href="https://www.youtube.com/watch?v=_B5cx-WD5EA" target="_blank">
                        Dijkstra's Algorithm - A Step-by-Step Analysis, with Sample Python Code
                    </a>
                </strong>
            </li>
            <li style="font-size: 18px;">
                <strong>
                    <a href="https://www.udacity.com/blog/2021/10/implementing-dijkstras-algorithm-in-python.html" target="_blank">
                        Implementing Dijkstra's Algorithm in Python - Udacity Blog
                    </a>
                </strong>
            </li>
            <li style="font-size: 18px;">
                <strong>
                    <a href="https://en.wikipedia.org/wiki/Haversine_formula" target="_blank">
                        Haversine Formula - Wikipedia
                    </a>
                </strong>
            </li>
            <li style="font-size: 18px;">
                <strong>
                    <a href="https://www.youtube.com/watch?v=Glp7THUpGow" target="_blank">
                        KD-Tree Nearest Neighbor Data Structure - YouTube
                    </a>
                </strong>
            </li>
            <li style="font-size: 18px;">
                <strong>
                    <a href="https://www.youtube.com/watch?v=ivdmGcZo6U8&t=245s" target="_blank">
                        K-D Tree: Build and Search for the Nearest Neighbor - YouTube
                    </a>
                </strong>
            </li>
            <li style="font-size: 18px;">
                <strong>
                    <a href="https://en.wikipedia.org/wiki/K-d_tree" target="_blank">
                        K-D Tree - Wikipedia
                    </a>
                </strong>
            </li>
            <li style="font-size: 18px;">
                <strong>
                    <a href="https://en.wikipedia.org/wiki/Rhumb_line" target="_blank">
                        Rhumb Line - Wikipedia
                    </a>
                </strong>
            </li>
            <li style="font-size: 18px;">
                <strong>
                    <a href="https://igorcomune.medium.com/data-science-how-to-plot-3d-interactive-globe-map-4dfba1b6e070" target="_blank">
                        How To Plot 3D Interactive Globe Map
                    </a>
                </strong>
            </li>
        </ul>
    </div>
    ''',
    unsafe_allow_html=True
)