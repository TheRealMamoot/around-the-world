import os
from shutil import rmtree

import plotly.graph_objects as go
import imageio

def gif_maker(data, direction, origin_city, run=False):
    
    if not run:
        print('GIF creation skipped!')

    else:
        globe = data.copy()
        globe['point_color'] = globe.apply(lambda row: '#ffd500' if row['city'] == origin_city else '#2291bd', axis=1)
        globe['point_symbol'] = globe.apply(lambda row: 'star' if row['city'] == origin_city else 'circle', axis=1)
        globe['point_size'] = globe.apply(lambda row: 32 if row['city'] == origin_city else 7, axis=1)

        total_time = globe['normed_next_point_duration'].tolist()
        total_distance = globe['next_point_distance'].tolist()

        frame_dir = os.path.join(os.getcwd(), 'frames') 

        if not os.path.exists(frame_dir):
            os.makedirs(frame_dir)

        frames = []
        num_frames = len(globe)

        for i in range(1, num_frames):
            frame = go.Frame(
                data=[go.Scattergeo(
                    lat=globe['lat'][:i+1], # incrementally include more points
                    lon=globe['lon'][:i+1],
                    text=globe['accent_city'][:i+1],
                    marker=dict(
                        size=globe['point_size'][:i+1],
                        color=globe['point_color'][:i+1],
                        symbol=globe['point_symbol'][:i+1],
                        opacity=0.8 
                    ),
                    mode='markers+lines'
                )],
                name=f'frame_{i}'
            )
            frames.append(frame)

        image_paths = []

        for i in range(len(frames)):

            if i != len(frames) - 1:
                title = f'Journey started from {globe.iloc[0]['city'].capitalize()}...'

                uptime = ('<span style="color:black; font-weight:bold;">Time:</span> '
                        f'<span style="color:blue; font-weight:bold;">{int(sum(total_time[:i+1]) // 24):02d}</span> '
                        '<span style="color:black;">days and</span> '
                        f'<span style="color:blue; font-weight:bold;">{int(sum(total_time[:i+1]) % 24):02d}</span> '
                        '<span style="color:black;">hours</span>')

                distance_text = ('<span style="color:black; font-weight:bold;">Distance:</span> '
                                f'<span style="color:blue; font-weight:bold;">{int(sum(total_distance[:i+1])):06,.0f}</span> '
                                '<span style="color:black;">km</span>')
                
            else:
                title = f'Reached back to {globe.iloc[0]['city'].capitalize()}!' # for the return to the initial point.
                
                uptime = ('<span style="color:black; font-weight:bold;">Time:</span> '
                        f'<span style="color:red; font-weight:bold;">{int(sum(total_time) // 24):02d}</span> '
                        '<span style="color:black;">days and</span> '
                        f'<span style="color:red; font-weight:bold;">{int(sum(total_time) % 24):02d}</span> '
                        '<span style="color:black;">hours</span>')
                
                distance_text = ('<span style="color:black; font-weight:bold;">Distance:</span> '
                                f'<span style="color:red; font-weight:bold;">{int(sum(total_distance)):06,.0f}</span> '
                                '<span style="color:black;">km</span>')

            fig = go.Figure(frames[i].data)

            for lat in range(-90, 91, 10):
                fig.add_trace(go.Scattergeo(
                    lat=[lat] * 361,
                    lon=list(range(-180, 181)),
                    mode='lines',
                    line=dict(color='gray', width=0.15),
                    showlegend=False
                    ))

            for lon in range(-180, 181, 10):
                fig.add_trace(go.Scattergeo(
                    lat=list(range(-90, 91)),
                    lon=[lon] * 181,
                    mode='lines',
                    line=dict(color='gray', width=0.25, dash='dot'),
                    showlegend=False
                    ))
            
            fig.update_layout(
                geo=dict(
                    showframe=True,
                    projection_type='orthographic',
                    showcoastlines=True,
                    showcountries=True,
                    showland=True,
                    landcolor='#61f179',
                    coastlinecolor='DarkBlue',
                    countrycolor='Black',
                    countrywidth=0.8,
                    projection_rotation=dict(lon=globe.iloc[0]['lon'], 
                                                lat=globe.iloc[0]['lat']),
                    projection_scale=0.75
                ),
                width=770,
                height=770,
                margin={'r': 0, 't': 0, 'l': 0, 'b': 0},
                showlegend=False,
                title = title,
                title_x=0.5,
                title_y=0.97,

                annotations=[
                dict(
                    x=0.5, 
                    y=0.95,
                    xref='paper',
                    yref='paper',
                    text=uptime,
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
                    text=distance_text,
                    showarrow=False,
                    font=dict(color='Black'),
                    align='center',
                    borderpad=4
                )])

            frame_path = os.path.join(frame_dir, f'frame_{i}.png')
            fig.write_image(frame_path, scale=5)
            image_paths.append(frame_path)

            if i % 10 == 0:
                print(f'frame {i}th created!')

        last_frame = fig
        last_frame.data[0].marker.color = '#dc3a1a'
        frame_path = os.path.join(frame_dir, f'frame_{i+1}.png')
        last_frame.write_image(frame_path, scale=5)
        image_paths.append(frame_path)

        second_last_frame_path = image_paths[-2]
        last_frame_path = image_paths[-1]
        
        for _ in range(10): # repeat the last frames n times for more visibility for results and alternating flashing color!
            image_paths.append(second_last_frame_path)
            image_paths.append(last_frame_path)

        image_paths = image_paths + [last_frame_path] * 30 # repeat the last frame to stay put with, having the second color

        lon_division = 5 # for the number of rotations to move around the earth!
        lon_sign = 1 if direction == 'E' else -1 # decrease longitude when going west, increases when going east

        lat_diff = abs(globe.iloc[0]['lat']) - 10 # for the vertical rotation!
        lat_division = 3
        lat_sign = 1 if globe.iloc[0]['lat'] < 0 else -1 # decrease latitude when going south, increases when going north

        for i in range(int(lat_diff/lat_division)+1): # rotates vertically either up or down based on the initial latitude
            fig.update_layout(
                geo=dict(
                    projection_rotation=dict(lon=globe.iloc[0]['lon'], 
                                            lat=globe.iloc[0]['lat'] + lat_sign * i * lat_division
                                            ),
                ))
            frame_path = os.path.join(frame_dir, f'frame_100{i}.png')
            fig.write_image(frame_path, scale=5)
            image_paths.append(frame_path)

        last_frame_path = image_paths[-1]
        image_paths = image_paths + [last_frame_path] * 10

        print('Initial vertical rotation done.')

        for j in range(int(360/lon_division)+1): # rotates horizontally around the globe
            fig.update_layout(
                geo=dict(
                    projection_rotation=dict(lon=globe.iloc[0]['lon'] + lon_sign * j * lon_division, 
                                            lat=globe.iloc[0]['lat'] + lat_sign * i * lat_division
                                            ),
                ))
            frame_path = os.path.join(frame_dir, f'frame_200{j}.png')
            fig.write_image(frame_path, scale=5)
            image_paths.append(frame_path)

        final_lat = globe.iloc[0]['lat'] + lat_sign * i * lat_division
        print('Horizontal rotation done.')

        last_frame_path = image_paths[-1]
        image_paths = image_paths + [last_frame_path] * 10

        for i in range(int(lat_diff/lat_division)+1): # rotates vertically in the reverse direction
            fig.update_layout(
                geo=dict(
                    projection_rotation=dict(lon=globe.iloc[0]['lon'], 
                                            lat=final_lat - lat_sign * i * lat_division # - sign for reverse
                                            ),
                ))
            frame_path = os.path.join(frame_dir, f'frame_300{i}.png')
            fig.write_image(frame_path, scale=5)
            image_paths.append(frame_path)

        print('Reverse vertical rotation done.')

        last_frame_path = image_paths[-1]
        image_paths = image_paths + [last_frame_path] * 45

        gif_path = os.path.join(os.getcwd(), 'journey.gif')

        with imageio.get_writer(gif_path, mode='I', duration=0.2, loop=0, fps=60) as writer:
            for i, image_path in enumerate(image_paths):
                image = imageio.imread(image_path)
                writer.append_data(image)
                del image
                if i % 20 == 0:
                    print(f'Image {i}th created!')
        
        rmtree(frame_dir)

        print(f'GIF saved as {gif_path}')