import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import analysis_engine


def _to_plotly_spec(fig) -> dict:
    return fig.to_dict()


def _find_global_max(path: str) -> tuple:
    lat, lon, field = analysis_engine.load_field_2d(path)
    max_val = np.nanmax(field)
    max_idx = np.where(field == max_val)
    if len(max_idx[0]) > 0:
        max_lat = lat[max_idx[0][0]]
        max_lon = lon[max_idx[1][0]]
        return max_val, max_lat, max_lon, lat, lon, field
    return max_val, None, None, lat, lon, field


def _find_india_max(lat, lon, field) -> tuple:
    india_lat_mask = (lat >= 8) & (lat <= 37)
    india_lon_mask = (lon >= 68) & (lon <= 97)
    
    if not np.any(india_lat_mask) or not np.any(india_lon_mask):
        return None, None, None
    
    india_field = field[np.ix_(india_lat_mask, india_lon_mask)]
    india_lats = lat[india_lat_mask]
    india_lons = lon[india_lon_mask]
    
    if india_field.size == 0:
        return None, None, None
    
    max_val = np.nanmax(india_field)
    max_idx = np.where(india_field == max_val)
    if len(max_idx[0]) > 0:
        max_lat = india_lats[max_idx[0][0]]
        max_lon = india_lons[max_idx[1][0]]
        return max_val, max_lat, max_lon
    return None, None, None


def generate_trend_plot(dataset_dir: str | None = None) -> tuple[dict, str]:
    series = analysis_engine.compute_trend(dataset_dir=dataset_dir)
    x = [d.isoformat() for d in series.dates]
    
    mean_val = np.mean(series.values)
    max_val = np.max(series.values)
    min_val = np.min(series.values)
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x, y=series.values,
            mode="lines+markers",
            line=dict(width=3, color='#00E5CC'),
            marker=dict(size=6, color=series.values, colorscale='Turbo', showscale=True,
                       colorbar=dict(title="ppm", thickness=15)),
            name='Daily Average'
        )
    )
    
    fig.add_hline(y=mean_val, line_dash="dash", line_color="white", 
                  annotation_text=f"Mean: {mean_val:.2f}", annotation_position="right")
    
    fig.update_layout(
        title=dict(
            text='Stratospheric Water Vapour Trend (Jan-Mar 2023)<br><sup>Global Daily Average | 90 Days | 36 Pressure Levels</sup>',
            font=dict(size=16)
        ),
        xaxis_title="Date (ISO Format)",
        yaxis_title="Water Vapour Concentration (ppm)",
        template="plotly_dark",
        hovermode="x unified",
        showlegend=True,
        annotations=[
            dict(xref='paper', yref='paper', x=0.02, y=0.98, showarrow=False,
                 text=f'<b>Statistics:</b> Max={max_val:.2f} | Min={min_val:.2f} | Mean={mean_val:.2f} ppm',
                 font=dict(size=11, color='#00E5CC'), align='left')
        ]
    )
    
    description = f"""
    <b>📊 TREND CHART ANALYSIS</b><br><br>
    <b>What it shows:</b> Daily average stratospheric water vapour concentration over the entire 3-month dataset.<br><br>
    <b>Data Coverage:</b><br>
    • Time Period: January 1 - March 31, 2023 (90 days)<br>
    • Spatial Coverage: Global (Lat: -90° to +85°, Lon: -180° to +165°)<br>
    • Vertical Levels: 36 pressure levels (stratosphere)<br>
    • Grid Resolution: 5° latitude × 15° longitude<br><br>
    <b>Key Statistics:</b><br>
    • Maximum: {max_val:.2f} ppm<br>
    • Minimum: {min_val:.2f} ppm<br>
    • Average: {mean_val:.2f} ppm<br><br>
    <b>Interpretation:</b> This chart shows temporal variations in stratospheric water vapour, 
    which plays a crucial role in climate and ozone chemistry.
    """
    
    return _to_plotly_spec(fig), description


def generate_trend_plot_range(start_date, end_date, dataset_dir: str | None = None) -> tuple[dict, str]:
    series = analysis_engine.compute_trend_range(start=start_date, end=end_date, dataset_dir=dataset_dir)
    x = [d.isoformat() for d in series.dates]
    
    mean_val = np.mean(series.values)
    max_val = np.max(series.values)
    min_val = np.min(series.values)
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x, y=series.values,
            mode="lines+markers",
            line=dict(width=3, color='#00E5CC'),
            marker=dict(size=8, color=series.values, colorscale='Turbo', 
                       colorbar=dict(title="ppm")),
            name='Daily Average'
        )
    )
    
    fig.add_hline(y=mean_val, line_dash="dash", line_color="white",
                  annotation_text=f"Mean: {mean_val:.2f}")
    
    fig.update_layout(
        title=dict(
            text=f'Water Vapour Trend ({x[0]} to {x[-1]})<br><sup>{len(series.dates)} Days | Custom Date Range Analysis</sup>',
            font=dict(size=16)
        ),
        xaxis_title="Date",
        yaxis_title="Water Vapour (ppm)",
        template="plotly_dark",
        hovermode="x unified"
    )
    
    description = f"""
    <b>📈 CUSTOM RANGE TREND ANALYSIS</b><br><br>
    <b>Period:</b> {x[0]} to {x[-1]} ({len(series.dates)} days)<br><br>
    <b>Statistics:</b><br>
    • Maximum: {max_val:.2f} ppm<br>
    • Minimum: {min_val:.2f} ppm<br>
    • Average: {mean_val:.2f} ppm<br>
    • Variation: {max_val - min_val:.2f} ppm<br><br>
    <b>Coordinate Info:</b><br>
    • Latitude Range: -90° to +85° (global)<br>
    • Longitude Range: -180° to +165° (global)<br>
    • All 36 stratospheric pressure levels averaged<br><br>
    This shows water vapour trends for your selected time period.
    """
    
    return _to_plotly_spec(fig), description


def generate_heatmap(sample_file: str | None = None, dataset_dir: str | None = None) -> tuple[dict, str]:
    path = sample_file or analysis_engine.pick_sample_file(dataset_dir)
    max_val, max_lat, max_lon, lat, lon, field = _find_global_max(path)
    
    hover_text = [[f"Lat: {lat[i]:.1f}°<br>Lon: {lon[j]:.1f}°<br>Value: {field[i,j]:.3f} ppm" 
                   for j in range(len(lon))] for i in range(len(lat))]
    
    fig = go.Figure(data=go.Heatmap(
        z=field,
        x=lon,
        y=lat,
        colorscale='Turbo',
        colorbar=dict(title="Water Vapour (ppm)", thickness=15),
        hoverongaps=False,
        text=hover_text,
        hovertemplate='%{text}<extra></extra>',
        zmin=np.nanmin(field),
        zmax=np.nanmax(field)
    ))
    
    # Add marker for global max
    if max_lat is not None and max_lon is not None:
        fig.add_trace(go.Scatter(
            x=[max_lon], y=[max_lat],
            mode='markers+text',
            marker=dict(size=15, color='red', symbol='star'),
            text=['Global Max'],
            textposition='top center',
            textfont=dict(color='white', size=10),
            name=f'Global Max: {max_val:.2f} ppm',
            hovertemplate=f'GLOBAL MAX<br>Lat: {max_lat}°<br>Lon: {max_lon}°<br>Value: {max_val:.2f} ppm<extra></extra>'
        ))
    
    fig.update_layout(
        title=dict(
            text='Global Stratospheric Water Vapour Distribution<br><sup>Sample Date Analysis | Grid: 5°×15° | 36 Levels</sup>',
            font=dict(size=16)
        ),
        xaxis_title="Longitude (°E)",
        yaxis_title="Latitude (°N)",
        template="plotly_dark",
        geo=dict(showland=True, landcolor="lightgray"),
        annotations=[
            dict(xref='paper', yref='paper', x=0.02, y=0.02, showarrow=False,
                 text=f'<b>Global Maximum:</b> {max_val:.2f} ppm at ({max_lat}°, {max_lon}°)',
                 font=dict(size=11, color='#FF6B6B'), align='left')
        ]
    )
    
    description = f"""
    <b>🗺️ GLOBAL HEATMAP ANALYSIS</b><br><br>
    <b>Visualization:</b> Geographic distribution of stratospheric water vapour<br><br>
    <b>Coordinate System:</b><br>
    • Latitude: -90° (South Pole) to +85° (North Pole)<br>
    • Longitude: -180° (West) to +165° (East)<br>
    • Grid Resolution: 5° latitude × 15° longitude<br>
    • Total Grid Points: 36 latitudes × 24 longitudes = 864 points<br><br>
    <b>🌟 GLOBAL MAXIMUM DETECTED:</b><br>
    • Value: <b>{max_val:.2f} ppm</b><br>
    • Location: Latitude {max_lat}°, Longitude {max_lon}°<br>
    • Region: {"Northern" if max_lat > 0 else "Southern"} Hemisphere, {"Western" if max_lon < 0 else "Eastern"}<br><br>
    <b>Color Scale:</b> Turbo (blue=low, red=high)<br>
    <b>Interactive:</b> Hover for exact coordinates and values
    """
    
    return _to_plotly_spec(fig), description


def generate_3d_globe(sample_file: str | None = None, dataset_dir: str | None = None) -> tuple[dict, str]:
    path = sample_file or analysis_engine.pick_sample_file(dataset_dir)
    lat, lon, field = analysis_engine.load_field_2d(path)
    max_val, max_lat, max_lon, _, _, _ = _find_global_max(path)
    
    theta = np.linspace(0, 2*np.pi, 50)
    phi = np.linspace(0, np.pi, 50)
    theta_grid, phi_grid = np.meshgrid(theta, phi)
    
    r = 1.0
    x_sphere = r * np.sin(phi_grid) * np.cos(theta_grid)
    y_sphere = r * np.sin(phi_grid) * np.sin(theta_grid)
    z_sphere = r * np.cos(phi_grid)
    
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    
    lon_grid, lat_grid = np.meshgrid(lon_rad, lat_rad)
    
    r_data = 1.02 + (field / np.nanmax(field)) * 0.3
    
    x_data = r_data * np.cos(lat_grid) * np.cos(lon_grid)
    y_data = r_data * np.cos(lat_grid) * np.sin(lon_grid)
    z_data = r_data * np.sin(lat_grid)
    
    fig = go.Figure()
    
    # Add Earth sphere surface (blue-green gradient to look like Earth)
    fig.add_trace(go.Surface(
        x=x_sphere, y=y_sphere, z=z_sphere,
        colorscale=[[0, '#1a5276'], [0.5, '#2d5a27'], [1, '#1a5276']],  # Ocean blue to land green
        showscale=False,
        opacity=0.6,
        hoverinfo='skip',
        name='Earth'
    ))
    
    # Add data points as 3D scatter on sphere
    fig.add_trace(go.Scatter3d(
        x=x_data.flatten(),
        y=y_data.flatten(),
        z=z_data.flatten(),
        mode='markers',
        marker=dict(
            size=3,
            color=field.flatten(),
            colorscale='Turbo',
            showscale=True,
            colorbar=dict(title="Water Vapour (ppm)", thickness=15),
            opacity=0.9
        ),
        hovertemplate='Lat: %{customdata[0]:.1f}°<br>Lon: %{customdata[1]:.1f}°<br>Value: %{marker.color:.3f} ppm<extra></extra>',
        customdata=np.stack([lat_grid.flatten() * 180/np.pi, lon_grid.flatten() * 180/np.pi], axis=-1),
        name='Water Vapour Data'
    ))
    
    # Add global maximum marker
    if max_lat is not None and max_lon is not None:
        max_lat_rad = np.radians(max_lat)
        max_lon_rad = np.radians(max_lon)
        r_max = 1.35
        x_max = r_max * np.cos(max_lat_rad) * np.cos(max_lon_rad)
        y_max = r_max * np.cos(max_lat_rad) * np.sin(max_lon_rad)
        z_max = r_max * np.sin(max_lat_rad)
        
        fig.add_trace(go.Scatter3d(
            x=[x_max], y=[y_max], z=[z_max],
            mode='markers+text',
            marker=dict(
                size=15,
                color='red',
                symbol='diamond',
                line=dict(color='white', width=2)
            ),
            text=['🌟 MAX'],
            textposition='top center',
            textfont=dict(size=12, color='white'),
            hovertemplate=f'<b>🌟 GLOBAL MAXIMUM</b><br>Lat: {max_lat}°<br>Lon: {max_lon}°<br>Value: {max_val:.2f} ppm<extra></extra>',
            name=f'Global Max: {max_val:.2f} ppm'
        ))
    
    # Update layout for globe appearance
    fig.update_layout(
        title=dict(
            text='🌍 3D Earth Globe - Water Vapour Distribution<br><sup>🛰️ NICeS Satellite Data | Stratospheric Levels</sup>',
            font=dict(size=16, color='white')
        ),
        scene=dict(
            xaxis=dict(showgrid=False, showticklabels=False, title='', showbackground=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, title='', showbackground=False, zeroline=False),
            zaxis=dict(showgrid=False, showticklabels=False, title='', showbackground=False, zeroline=False),
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.8, y=1.8, z=1.2),
                center=dict(x=0, y=0, z=0)
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0.9)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(
            yanchor="top", y=0.99, xanchor="left", x=0.01,
            bgcolor='rgba(0,0,0,0.7)',
            bordercolor='white',
            borderwidth=1,
            font=dict(color='white')
        ),
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    description = f"""
    <b>🌍 3D EARTH GLOBE VISUALIZATION</b><br><br>
    
    <b style="color:#FFD700;">🌟 GLOBAL MAXIMUM DETECTED:</b><br>
    📍 <b>Coordinates:</b> {max_lat}°N, {max_lon}°E<br>
    💧 <b>Value:</b> {max_val:.2f} ppm<br><br>
    
    <b>🎮 Interactive Controls:</b><br>
    • 🖱️ <b>Rotate:</b> Click & drag to spin the globe<br>
    • 🔍 <b>Zoom:</b> Scroll wheel to zoom in/out<br>
    • 🖐️ <b>Pan:</b> Right-click & drag to move view<br><br>
    
    <b>📊 Data Representation:</b><br>
    • 🌍 <b>Blue-Green Sphere:</b> Earth surface (ocean/land)<br>
    • 🌈 <b>Colored Points:</b> Water vapour concentration<br>
    • 📏 <b>Elevation:</b> Higher values extend further from surface<br>
    • 🔴 <b>Red Diamond:</b> Global maximum location<br><br>
    
    <b>🗺️ Coverage:</b> Global (all latitudes/longitudes)<br>
    <b>🛰️ Source:</b> NICeS (NRSC/ISRO) Satellite Data<br>
    <b>📅 Period:</b> January-March 2023
    """
    
    return _to_plotly_spec(fig), description



def generate_animation(dataset_dir: str | None = None, max_frames: int = 31) -> tuple[dict, str]:
    paths = analysis_engine.list_nc_files(dataset_dir)
    if max_frames is not None:
        paths = paths[: max(1, int(max_frames))]
    
    from analysis_engine import _parse_date_from_path
    
    dates = []
    frames = []
    for p in paths:
        d = _parse_date_from_path(p)
        if d:
            dates.append(d.strftime("%Y-%m-%d"))
        _lat, _lon, field = analysis_engine.load_field_2d(p)
        frames.append(field)
    
    data = np.stack(frames, axis=0)
    
    fig = px.imshow(
        data,
        animation_frame=0,
        origin="lower",
        aspect="auto",
        color_continuous_scale="Turbo",
        title="Animated Water Vapour Evolution (Jan-Mar 2023)",
        labels={"x": "Longitude Index", "y": "Latitude Index", "color": "Water Vapour (ppm)"},
    )
    
    # Update animation labels
    if dates:
        for i, frame in enumerate(fig.frames):
            if i < len(dates):
                frame.layout.title = f"Water Vapour - {dates[i]}"
    
    fig.update_layout(
        template="plotly_dark",
        title=dict(
            text='⏯️ Water Vapour Time Evolution<br><sup>90-Day Animation | Press Play Button</sup>',
            font=dict(size=16)
        ),
    )
    
    description = f"""
    <b>⏯️ TIME-LAPSE ANIMATION</b><br><br>
    <b>What it shows:</b> Evolution of stratospheric water vapour over 90 days<br><br>
    <b>Animation Details:</b><br>
    • Frames: {len(frames)} days (Jan 1 - Mar 31, 2023)<br>
    • Speed: Adjustable with play/speed controls<br>
    • Direction: Forward through time<br><br>
    <b>Coordinates:</b><br>
    • X-axis: Longitude (-180° to +165°)<br>
    • Y-axis: Latitude (-90° to +85°)<br>
    • Color: Water vapour concentration (ppm)<br><br>
    <b>Controls:</b><br>
    • ▶️ Play: Start animation<br>
    • ⏸️ Pause: Stop animation<br>
    • 🎚️ Speed: Adjust playback speed<br>
    • 📍 Slider: Manual frame selection<br><br>
    <b>Insights:</b> Watch for seasonal patterns and regional variations
    """
    
    return _to_plotly_spec(fig), description


def generate_india_heatmap(dataset_dir: str | None = None, year: int | None = None) -> tuple[dict, str]:
    if year is not None:
        paths = analysis_engine.list_nc_files(dataset_dir)
        path = None
        for p in paths:
            if str(year) in p:
                path = p
                break
        if path is None:
            path = analysis_engine.pick_sample_file(dataset_dir)
    else:
        path = analysis_engine.pick_sample_file(dataset_dir)
    
    lat, lon, field = analysis_engine.load_field_2d(path)
    
    # India region: lat 8-37°N, lon 68-97°E
    india_lat_mask = (lat >= 8) & (lat <= 37)
    india_lon_mask = (lon >= 68) & (lon <= 97)
    
    india_lats = lat[india_lat_mask]
    india_lons = lon[india_lon_mask]
    india_field = field[np.ix_(india_lat_mask, india_lon_mask)]
    
    # Find max in India
    india_max, india_max_lat, india_max_lon = _find_india_max(lat, lon, field)
    
    # Create scatter mapbox with data points
    scatter_lons = []
    scatter_lats = []
    scatter_vals = []
    hover_texts = []
    
    for i in range(len(india_lats)):
        for j in range(len(india_lons)):
            scatter_lons.append(india_lons[j])
            scatter_lats.append(india_lats[i])
            scatter_vals.append(india_field[i, j])
            hover_texts.append(f"📍 Lat: {india_lats[i]:.1f}°N<br>🌐 Lon: {india_lons[j]:.1f}°E<br>💧 Water Vapour: {india_field[i,j]:.3f} ppm")
    
    # Create figure with Mapbox
    fig = go.Figure()
    
    # Add heatmap as scatter points with color
    fig.add_trace(go.Scattermapbox(
        lat=scatter_lats,
        lon=scatter_lons,
        mode='markers',
        marker=dict(
            size=15,
            color=scatter_vals,
            colorscale='Turbo',
            showscale=True,
            colorbar=dict(title="Water Vapour (ppm)", thickness=15, x=0.95),
            opacity=0.8,
        ),
        text=hover_texts,
        hovertemplate='%{text}<extra></extra>',
        name='Water Vapour Data'
    ))
    
    # Add India max location pin marker
    if india_max is not None:
        # Add red pin marker at max location
        fig.add_trace(go.Scattermapbox(
            lat=[india_max_lat],
            lon=[india_max_lon],
            mode='markers+text',
            marker=dict(
                size=30,
                color='#FF0000',
                symbol='marker',  # Mapbox marker symbol
            ),
            text=['🏆 MAX'],
            textposition='top center',
            textfont=dict(size=14, color='white', family='Arial Black'),
            hovertemplate=f'<b>🌟 INDIA MAXIMUM WATER VAPOUR</b><br>📍 Location: {india_max_lat}°N, {india_max_lon}°E<br>💧 Value: {india_max:.2f} ppm<br><br>📌 Highest concentration in India region<extra></extra>',
            name=f'Max: {india_max:.2f} ppm'
        ))
        
        # Add pulsing effect marker (larger, transparent)
        fig.add_trace(go.Scattermapbox(
            lat=[india_max_lat],
            lon=[india_max_lon],
            mode='markers',
            marker=dict(
                size=50,
                color='rgba(255,0,0,0.3)',
                symbol='circle',
            ),
            hoverinfo='skip',
            showlegend=False
        ))
    
    # Update layout with map style
    fig.update_layout(
        mapbox=dict(
            accesstoken=None,  # Use free carto-positron tiles
            style='carto-positron',  # Free light map style
            center=dict(lat=22, lon=80),  # Center on India
            zoom=4,
            bearing=0,
            pitch=0,
        ),
        title=dict(
            text='🇮🇳 INDIA Stratospheric Water Vapour Map<br><sup>🛰️ NICeS Satellite Data | 📍 Max Location Marked</sup>',
            font=dict(size=18)
        ),
        template="plotly_dark",
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(0,0,0,0.7)',
            bordercolor='white',
            borderwidth=1
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        annotations=[
            dict(
                xref='paper', yref='paper', x=0.02, y=0.02, showarrow=False,
                text=f'<b>⭐️ INDIA MAX:</b> {india_max:.2f} ppm @ {india_max_lat}°N, {india_max_lon}°E<br><b>📊 Data Points:</b> {len(scatter_vals)} locations<br><b>🗺️ Coverage:</b> 8°N-37°N, 68°E-97°E' if india_max else '<b>No India data</b>',
                font=dict(size=11, color='white'), align='left',
                bgcolor='rgba(0,0,0,0.7)', bordercolor='white', borderwidth=1,
                borderpad=4
            )
        ]
    )
    
    # Get nearest city info
    nearest_city = _get_nearest_indian_city(india_max_lat, india_max_lon) if india_max else None
    
    description = f"""
    <b>🇮🇳 INDIA WATER VAPOUR MAP WITH LOCATION</b><br><br>
    
    <b style="color:#FFD700;">🌟 MAXIMUM WATER VAPOUR LOCATION DETECTED:</b><br>
    📍 <b>Coordinates:</b> {india_max_lat}°N, {india_max_lon}°E<br>
    💧 <b>Value:</b> {india_max:.2f} ppm<br>
    🏙️ <b>Nearest Region:</b> {nearest_city if nearest_city else 'Central India'}<br><br>
    
    <b>📊 Geographic Coverage:</b><br>
    • 🌐 <b>Latitude:</b> 8°N to 37°N<br>
    • 🌐 <b>Longitude:</b> 68°E to 97°E<br>
    • 📍 <b>Data Points:</b> {len(india_lats)} × {len(india_lons)} = {len(scatter_vals)} locations<br><br>
    
    <b>🗺️ Reference Cities:</b><br>
    • 🔸 Delhi: ~28.6°N, 77.2°E<br>
    • 🔸 Mumbai: ~19.0°N, 72.8°E<br>
    • 🔸 Chennai: ~13.0°N, 80.3°E<br>
    • 🔸 Kolkata: ~22.5°N, 88.3°E<br>
    • 🔸 Bangalore: ~12.9°N, 77.6°E<br><br>
    
    <b>🛰️ Dataset:</b> NICeS (NRSC/ISRO)<br>
    <b>📅 Period:</b> January-March 2023<br>
    <b>🔴 Red Pin:</b> Marks highest water vapour concentration
    """
    
    return _to_plotly_spec(fig), description


def _get_nearest_indian_city(lat: float, lon: float) -> str:
    cities = [
        ("Delhi", 28.6, 77.2),
        ("Mumbai", 19.0, 72.8),
        ("Chennai", 13.0, 80.3),
        ("Kolkata", 22.5, 88.3),
        ("Bangalore", 12.9, 77.6),
        ("Hyderabad", 17.4, 78.5),
        ("Ahmedabad", 23.0, 72.6),
        ("Pune", 18.5, 73.9),
        ("Jaipur", 26.9, 75.8),
        ("Lucknow", 26.8, 80.9),
    ]
    
    nearest = min(cities, key=lambda c: ((lat - c[1])**2 + (lon - c[2])**2)**0.5)
    dist = ((lat - nearest[1])**2 + (lon - nearest[2])**2)**0.5
    
    if dist < 2:
        return f"Near {nearest[0]}"
    elif dist < 5:
        return f"Near {nearest[0]} (~{dist:.1f}° away)"
    else:
        return f"Central India (nearest: {nearest[0]})"



def generate_india_comparison(dataset_dir: str | None = None) -> tuple[dict, str]:
    from analysis_engine import _parse_date_from_path
    
    paths = analysis_engine.list_nc_files(dataset_dir)
    
    india_values = []
    global_values = []
    dates = []
    
    for p in paths[:30]:
        d = _parse_date_from_path(p)
        if not d:
            continue
        dates.append(d.strftime("%m-%d"))
        
        lat, lon, field = load_field_2d(p)
        
        global_avg = np.nanmean(field)
        global_values.append(global_avg)
        
        india_lat_mask = (lat >= 8) & (lat <= 37)
        india_lon_mask = (lon >= 68) & (lon <= 97)
        if np.any(india_lat_mask) and np.any(india_lon_mask):
            india_field = field[np.ix_(india_lat_mask, india_lon_mask)]
            india_avg = np.nanmean(india_field)
            india_values.append(india_avg)
        else:
            india_values.append(None)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates, y=global_values,
        mode='lines+markers',
        name='🌍 Global',
        line=dict(color='#00E5CC', width=3),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=dates, y=india_values,
        mode='lines+markers',
        name='🇮🇳 India',
        line=dict(color='#FF6B6B', width=3),
        marker=dict(size=6, symbol='diamond')
    ))
    
    fig.update_layout(
        title=dict(
            text='🇮🇳 India vs 🌍 Global Comparison<br><sup>Daily Average Water Vapour</sup>',
            font=dict(size=16)
        ),
        xaxis_title="Date (Jan-Mar 2023)",
        yaxis_title="Water Vapour (ppm)",
        template="plotly_dark",
        hovermode="x unified"
    )
    
    india_mean = np.nanmean([v for v in india_values if v is not None])
    global_mean = np.nanmean(global_values)
    
    description = f"""
    <b>🇮🇳 INDIA vs 🌍 GLOBAL</b><br><br>
    • India Avg: <b>{india_mean:.2f} ppm</b><br>
    • Global Avg: <b>{global_mean:.2f} ppm</b><br>
    • Difference: <b>{abs(india_mean - global_mean):.2f} ppm</b><br><br>
    <b>India Region:</b> 8°N-37°N, 68°E-97°E
    """
    
    return _to_plotly_spec(fig), description

