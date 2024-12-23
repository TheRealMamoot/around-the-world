from copy import deepcopy
from shutil import rmtree

import os
import pandas as pd
import plotly.graph_objects as go
import imageio

class JourneyPlanner:
    def __init__(self, data: pd.DataFrame, direction='E', origin_city='london', frame_dir='frames', gif_name='journey.gif', make_gif=False):
        self.data = data.copy()
        self.direction = direction
        self.origin_city = origin_city
        self.frame_dir = os.path.join(os.getcwd(), frame_dir)
        self.gif_name = gif_name
        self.make_gif = make_gif
        self.image_paths = []

        self._prepare_data()

    def _prepare_data(self):
        """For visualization purposes."""
        self.data['point_color'] = self.data.apply(
            lambda row: '#ffd500' if row['city'] == self.origin_city else '#2291bd', axis=1)
        self.data['point_symbol'] = self.data.apply(
            lambda row: 'star' if row['city'] == self.origin_city else 'circle', axis=1)
        self.data['point_size'] = self.data.apply(
            lambda row: 32 if row['city'] == self.origin_city else 7, axis=1)
        
    def _check_output_dir(self):
        if not os.path.exists(self.frame_dir):
            os.makedirs(self.frame_dir)
    
    @staticmethod
    def add_figure_grid_lines(fig):
        for lat in range(-90, 91, 10):
            fig.add_trace(go.Scattergeo(
                lat=[lat] * 361,
                lon=list(range(-180, 181)),
                mode='lines',
                line=dict(color='#cacdcf', width=0.18),
                showlegend=False
                ))
        for lon in range(-180, 181, 10):
            fig.add_trace(go.Scattergeo(
                lat=list(range(-90, 91)),
                lon=[lon] * 181,
                mode='lines',
                line=dict(color='#cacdcf', width=0.27, dash='dot'),
                showlegend=False
                ))
            
    def _update_figure_layout(self, fig, title, uptime_title, distance_title):
        fig.update_layout(
            geo=dict(
                showframe=True,
                projection_type='orthographic',
                showcoastlines=True,
                showcountries=True,
                showland=True,
                landcolor='#D3D3D3',
                coastlinecolor='#053e61',
                countrycolor='Black',
                countrywidth=0.8,
                projection_rotation=dict(lon=self.data.iloc[0]['lon'], 
                                         lat=self.data.iloc[0]['lat']),
                projection_scale=0.75,
                bgcolor='#0d1118'
            ),
            width=1000,
            height=1000,
            margin={'r': 0, 't': 0, 'l': 0, 'b': 0},
            showlegend=False,
            title = title,
            title_x=0.5,
            title_y=0.98,
            annotations=[
                dict(
                    x=0.5, 
                    y=0.95,
                    xref='paper',
                    yref='paper',
                    text=uptime_title,
                    showarrow=False,
                    font=dict(color='Black'),
                    align='center',
                    borderpad=4
                    ),
                dict(
                    x=0.5, 
                    y=0.92, 
                    xref='paper',
                    yref='paper',
                    text=distance_title,
                    showarrow=False,
                    font=dict(color='Black'),
                    align='center',
                    borderpad=4
                )],
                paper_bgcolor='#0d1118',
                plot_bgcolor='#0d1118')

    def _add_menus_and_sliders(self, fig, frames):
        menus=[{
            'type': 'buttons',
            'showactive': False,
            'x': 0.5, 
            'xanchor': 'center', 
            'y': 0.1, 
            'yanchor': 'bottom', 
            'direction': 'left', 
            'pad': {'r': 10, 't': 10}, 
            'buttons': [
                {
                    'label': 'Play',
                    'method': 'animate',
                    'args': [None, {
                        'frame': {'duration': 100, 'redraw': True}, 
                        'fromcurrent': True
                    }]
                },
                {
                    'label': 'Pause',
                    'method': 'animate',
                    'args': [[None], {
                        'frame': {'duration': 0, 'redraw': False},
                        'mode': 'immediate',
                        'transition': {'duration': 0}
                    }]
                }
                    ]
                        }]
        slides=[{
            'steps': [{
                'method': 'animate',
                'label': self.data['city'].iloc[i].capitalize(),
                'args': [[f'frame_{i}'], {
                    'frame': {'duration': 100, 'redraw': True}, 
                    'mode': 'immediate'
                }]
            } for i in range(1, len(self.data))],
            'transition': {'duration': 0},
            'x': 0.5, 
            'xanchor': 'center',  
            'y': 0.05,  
            'yanchor': 'bottom', 
            'len': 0.9 
                }] 

        fig.update_layout(
            updatemenus = menus,
            sliders = slides)
        fig.frames = frames

    def create_fig_data(self):
        total_time = self.data['normed_next_point_duration'].tolist()
        total_distance = self.data['next_point_distance'].tolist()

        figures = [] 
        titles = []
        for i in range(len(self.data)):
            title = ('<span style="display: block; font-size: 14px; color: #0d1118;">'
                    f'Journey started from {self.data.iloc[0]["city"].capitalize()}...'
                    '</span>')
            uptime_title = ('<span style="color:white; font-weight:bold;">Time:</span> '
                            f'<span style="color:#2291bd; font-weight:bold;">{int(sum(total_time[: i+1]) // 24):02d}</span> '
                            '<span style="color:white;">days and</span> '
                            f'<span style="color:#2291bd; font-weight:bold;">{int(sum(total_time[: i+1]) % 24):02d}</span> '
                            '<span style="color:white;">hours</span>')
            distance_title = ('<span style="color:white; font-weight:bold;">Distance:</span> '
                             f'<span style="color:#2291bd; font-weight:bold;">{int(sum(total_distance[: i+1])):06,.0f}</span> '
                              '<span style="color:white;">km</span>')
            fig_data = go.Frame(
                    data=[go.Scattergeo(
                            lat=self.data['lat'][: i+1],
                            lon=self.data['lon'][: i+1],
                            text=self.data['accent_city'][: i+1],
                            marker=dict(size=self.data['point_size'][: i+1],
                                        color=self.data['point_color'][: i+1],
                                        symbol=self.data['point_symbol'][: i+1],
                                        opacity=0.8),
                            mode='markers+lines')],
                    name=f'frame_{i}'
                                )        

            if i == len(self.data) - 1:
                title = ('<span style="display: block; font-size: 14px; color: #0d1118;">'
                        f'Reached back to {self.data.iloc[0]["city"].capitalize()}!'
                        '</span>')
                uptime_title = ('<span style="color:white; font-weight:bold;">Time:</span> '
                        f'<span style="color:#dc3a1a; font-weight:bold;">{int(sum(total_time) // 24):02d}</span> '
                        '<span style="color:white;">days and</span> '
                        f'<span style="color:#dc3a1a; font-weight:bold;">{int(sum(total_time) % 24):02d}</span> '
                        '<span style="color:white;">hours</span>')
                distance_title = ('<span style="color:white; font-weight:bold;">Distance:</span> '
                                f'<span style="color:#dc3a1a; font-weight:bold;">{int(sum(total_distance)):06,.0f}</span> '
                                '<span style="color:white;">km</span>')
            figures.append(fig_data)
            titles.append((title, uptime_title, distance_title))

        return figures, titles
    
    def _create_fig(self):
        figures, titles = self.create_fig_data()
        figures_updated = []

        for i, frame in enumerate(figures):
            fig = go.Figure(frame.data)
            self.add_figure_grid_lines(fig)
            self._update_figure_layout(fig, titles[i][0], titles[i][1], titles[i][2])
            figures_updated.append(fig)

        figures_updated.append(deepcopy(fig))
        fig.data[0].marker.color = '#dc3a1a'
        figures_updated.append(fig)
        interactive_fig = deepcopy(fig)
        
        frames = []
        for i, figure in enumerate(figures_updated):
            frames.append(go.Frame(
                data = figure.data,
                layout = figure.layout,
                name = f'frame_{i}'
            ))
        self._add_menus_and_sliders(interactive_fig, frames)
        return fig, interactive_fig, figures_updated
    
    def show(self):
        _, interactive_fig, _ = self._create_fig()
        return interactive_fig
    
    def gif(self, run=None):
        run = run or self.make_gif
        if run:
            gif_path, image_paths = self._frames_to_images()

            with imageio.get_writer(gif_path, mode='I', duration=0.2, loop=0, fps=60) as writer:
                for i, image_path in enumerate(image_paths):
                    image = imageio.imread(image_path)
                    writer.append_data(image)
                    del image
                    if i % 20 == 0:
                        print(f'Image {i}th created!')
            
            rmtree(self.frame_dir)
            print(f'GIF saved as {gif_path}')
        else:
            print('GIF creation skipped!')
    
    def _frames_to_images(self):
        fig, _, frames = self._create_fig()
        image_paths = []
        self._check_output_dir()

        for i, fig in enumerate(frames):
            self._write_image(image_paths, fig, f'frame_{i}.png')
            if i % 20 == 0:
                print(f'frame {i}th created!')

        second_last_frame_path = image_paths[-2]
        last_frame_path = image_paths[-1]
        """repeat the last frames n times for more visibility for results and alternating flashing color!"""
        for _ in range(10): 
            image_paths.append(second_last_frame_path)
            image_paths.append(last_frame_path)
        """repeat the last frame to stay put with, having the second color"""
        image_paths = image_paths + [last_frame_path] * 30 

        gif_rotation = self.Gif(self)
        i, image_paths = gif_rotation._initial_vertical_rotaion(image_paths, fig)
        final_lat, image_paths = gif_rotation._horizontal_rotation(image_paths, fig, i)
        gif_path, image_paths = gif_rotation._reverse_vertical_rotation(image_paths, fig, final_lat)
        
        return gif_path, image_paths
    
    def _write_image(self, image_paths, fig, frame_name, dir=None):
        dir = dir or self.frame_dir
        frame_path = os.path.join(dir, frame_name)
        fig.write_image(frame_path, scale=5)
        image_paths.append(frame_path)

    class Gif:
        def __init__(self, journey_instance):
            self.journey_instance = journey_instance
            self.default_lat = self.journey_instance.data.iloc[0]['lat']
            self.default_lon = self.journey_instance.data.iloc[0]['lon']
            """for the vertical rotation!"""
            self.lat_diff = abs(self.journey_instance.data.iloc[0]['lat']) - 10
            self.lat_division = 3
            """decrease latitude when going south, increases when going north"""
            self.lat_sign = 1 if self.journey_instance.data.iloc[0]['lat'] < 0 else -1
            self.lon_division = 5
            self.lon_sign = 1 if self.journey_instance.direction == 'E' else -1

        @staticmethod
        def frame_multipication(image_paths, n):
            """increases last frames for the visibility of the changes in the GIF"""
            last_frame_path = image_paths[-1]
            image_paths = image_paths + [last_frame_path] * n
            return image_paths

        def _initial_vertical_rotaion(self, image_paths, fig):
            num = int(self.lat_diff / self.lat_division)
            """rotates vertically either up or down based on the initial latitude"""
            for i in range(num+1): 
                fig.update_layout(
                    geo=dict(
                        projection_rotation=dict(lat=self.default_lat + self.lat_sign * i * self.lat_division,
                                                 lon=self.default_lon,),
                    ))
                self.journey_instance._write_image(image_paths, fig, f'frame_100{i}.png')

            image_paths = self.frame_multipication(image_paths, n=10)
            print('Initial vertical rotation done.')
            return i, image_paths

        def _horizontal_rotation(self, image_paths, fig, index):
            num = int(360/self.lon_division)
            final_lat = self.default_lat + self.lat_sign * index * self.lat_division
            """rotates horizontally around the globe"""
            for j in range(num+1):
                fig.update_layout(
                    geo=dict(
                        projection_rotation=dict(lat=final_lat,
                                                 lon=self.default_lon + self.lon_sign * j * self.lon_division),
                    ))
                self.journey_instance._write_image(image_paths, fig, f'frame_200{j}.png')

            print('Horizontal rotation done.')
            image_paths = self.frame_multipication(image_paths, n=10)
            return final_lat, image_paths
        
        def _reverse_vertical_rotation(self, image_paths, fig, final_lat):
            num = int(self.lat_diff / self.lat_division)
            """rotates vertically in the reverse direction"""
            for i in range(num+1): 
                fig.update_layout(
                    geo=dict(
                        projection_rotation=dict(lat=final_lat - self.lat_sign * i * self.lat_division,  # "-" sign for reverse  
                                                 lon=self.default_lon),                 
                    ))
                self.journey_instance._write_image(image_paths, fig, f'frame_300{i}.png')

            print('Reverse vertical rotation done.')
            image_paths = self.frame_multipication(image_paths, n=45)
            gif_path = os.path.join(os.getcwd(), self.journey_instance.gif_name)
            return gif_path, image_paths