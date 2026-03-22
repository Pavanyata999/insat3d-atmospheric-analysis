import numpy as np, json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from analysis_engine import load_field_2d, list_nc_files


@dataclass
class AnomalyResult:
    is_anomaly: bool
    anomaly_type: str
    z_score: float
    message: str
    severity: str


@dataclass
class EventPrediction:
    event_type: str
    confidence: float
    description: str
    regions: List[str]
    recommendation: str


class ClimateIntelligenceEngine:
    
    def __init__(self, dataset_dir: str = "./watervapour_dataset"):
        self.dataset_dir = Path(dataset_dir)
        self.yearly_summaries: Dict[int, Dict] = {}
        self.available_years: List[int] = []
        self._load_available_years()
    
    def _load_available_years(self):
        nc_files = list_nc_files(str(self.dataset_dir))
        years = []
        for f in nc_files:
            f_path = Path(f)
            parts = f_path.stem.split('_')
            for part in parts:
                if part.isdigit() and len(part) == 4:
                    years.append(int(part))
                    break
        self.available_years = sorted(list(set(years)))
        
        for year in self.available_years:
            self._load_year_summary(year)
    
    def _load_year_summary(self, year: int) -> bool:
        if year in self.yearly_summaries:
            return True
        
        nc_files = list_nc_files(str(self.dataset_dir))
        target_file = None
        for f in nc_files:
            if str(year) in Path(f).stem:
                target_file = f
                break
        
        if not target_file:
            return False
        
        try:
            lat, lon, field = load_field_2d(str(target_file))
            
            self.yearly_summaries[year] = {
                'lat': lat,
                'lon': lon,
                'field': field,
                'mean': float(np.nanmean(field)),
                'max': float(np.nanmax(field)),
                'min': float(np.nanmin(field)),
                'std': float(np.nanstd(field))
            }
            return True
        except Exception as e:
            print(f"Error loading year {year}: {e}")
            return False
    
    def get_available_years(self) -> List[int]:
        return self.available_years
    
    def _get_year_data(self, year: int) -> Tuple[List, List, List]:
        if year not in self.yearly_summaries:
            return [], [], []
        
        data = self.yearly_summaries[year]
        lat = data['lat']
        lon = data['lon']
        field = data['field']
        
        lon_grid, lat_grid = np.meshgrid(lon, lat)
        
        lats_flat = lat_grid.flatten()
        lons_flat = lon_grid.flatten()
        values_flat = field.flatten()
        
        valid_mask = ~np.isnan(values_flat)
        lats_flat = lats_flat[valid_mask]
        lons_flat = lons_flat[valid_mask]
        values_flat = values_flat[valid_mask]
        
        n_points = len(values_flat)
        if n_points > 5000:
            step = n_points // 5000
            lats_flat = lats_flat[::step]
            lons_flat = lons_flat[::step]
            values_flat = values_flat[::step]
        
        return lats_flat.tolist(), lons_flat.tolist(), values_flat.tolist()
    
    def generate_trend_timeseries(self, end_year: int) -> Dict:
        years = []
        values = []
        
        for year in sorted(self.yearly_summaries.keys()):
            if year <= end_year:
                years.append(year)
                values.append(self.yearly_summaries[year]['mean'])
        
        if not years:
            return {}
        
        fig = make_subplots(rows=1, cols=1)
        
        fig.add_trace(go.Scatter(
            x=years,
            y=values,
            mode='lines+markers',
            name='Mean WV',
            line=dict(color='#00d4ff', width=3),
            marker=dict(size=8, color='#00d4ff', line=dict(color='white', width=1))
        ))
        
        if len(years) > 1:
            z = np.polyfit(years, values, 1)
            p = np.poly1d(z)
            fig.add_trace(go.Scatter(
                x=years,
                y=p(years),
                mode='lines',
                name='Trend',
                line=dict(color='rgba(255, 100, 100, 0.7)', width=2, dash='dash')
            ))
        
        if end_year in years:
            idx = years.index(end_year)
            fig.add_trace(go.Scatter(
                x=[end_year],
                y=[values[idx]],
                mode='markers',
                name=f'{end_year}',
                marker=dict(size=15, color='#ff4444', symbol='star',
                           line=dict(color='yellow', width=2))
            ))
        
        fig.update_layout(
            title=f'Water Vapour Trend (2009-{end_year})',
            xaxis_title='Year',
            yaxis_title='Mean WV (ppm)',
            paper_bgcolor='rgba(5, 10, 25, 0.9)',
            plot_bgcolor='rgba(0,0,0,0.3)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white')),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white')),
            legend=dict(font=dict(color='white'), bgcolor='rgba(0,0,0,0.5)'),
            margin=dict(l=50, r=50, t=80, b=50),
            autosize=True
        )
        
        return fig.to_dict()
    
    def detect_anomaly(self, year: int) -> AnomalyResult:
        if year not in self.yearly_summaries:
            return AnomalyResult(
                is_anomaly=False,
                anomaly_type='unknown',
                z_score=0.0,
                message='DATA UNAVAILABLE FOR ANALYSIS',
                severity='normal'
            )
        
        all_means = [s['mean'] for s in self.yearly_summaries.values()]
        overall_mean = np.mean(all_means)
        overall_std = np.std(all_means) if len(all_means) > 1 else 1.0
        
        current_mean = self.yearly_summaries[year]['mean']
        z_score = (current_mean - overall_mean) / overall_std if overall_std > 0 else 0
        
        if z_score > 2.0:
            return AnomalyResult(
                is_anomaly=True,
                anomaly_type='extreme_high',
                z_score=float(z_score),
                message='CRITICAL WATER VAPOUR SURGE',
                severity='critical'
            )
        elif z_score > 1.5:
            return AnomalyResult(
                is_anomaly=True,
                anomaly_type='high',
                z_score=float(z_score),
                message='ELEVATED MOISTURE',
                severity='warning'
            )
        elif z_score < -2.0:
            return AnomalyResult(
                is_anomaly=True,
                anomaly_type='extreme_low',
                z_score=float(z_score),
                message='SEVERE DRY CONDITION',
                severity='critical'
            )
        elif z_score < -1.5:
            return AnomalyResult(
                is_anomaly=True,
                anomaly_type='low',
                z_score=float(z_score),
                message='REDUCED MOISTURE',
                severity='warning'
            )
        else:
            return AnomalyResult(
                is_anomaly=False,
                anomaly_type='normal',
                z_score=float(z_score),
                message='STABLE ATMOSPHERIC STATE',
                severity='normal'
            )
    
    def predict_event(self, year: int) -> EventPrediction:
        if year not in self.yearly_summaries:
            return EventPrediction(
                event_type='unknown',
                confidence=0.0,
                description='Insufficient data',
                regions=[],
                recommendation='Await data'
            )
        
        data = self.yearly_summaries[year]
        field = data['field']
        lat = data['lat']
        lon = data['lon']
        mean_val = data['mean']
        
        regions = {
            'bay_of_bengal': {'lat': (15, 22), 'lon': (85, 95), 'thresh': mean_val * 1.3},
            'arabian_sea': {'lat': (8, 20), 'lon': (65, 75), 'thresh': mean_val * 1.2},
            'indian_ocean': {'lat': (0, 15), 'lon': (70, 95), 'thresh': mean_val * 1.25}
        }
        
        region_status = {}
        for name, bounds in regions.items():
            lat_mask = (lat >= bounds['lat'][0]) & (lat <= bounds['lat'][1])
            lon_mask = (lon >= bounds['lon'][0]) & (lon <= bounds['lon'][1])
            if np.any(lat_mask) and np.any(lon_mask):
                region_field = field[np.ix_(lat_mask, lon_mask)]
                region_mean = np.nanmean(region_field)
                region_status[name] = {
                    'mean': region_mean,
                    'exceeds': region_mean > bounds['thresh'],
                    'anomaly': region_mean > mean_val * 1.4
                }
        
        bob = region_status.get('bay_of_bengal', {})
        arabian = region_status.get('arabian_sea', {})
        ocean = region_status.get('indian_ocean', {})
        
        if bob.get('exceeds', False) and bob.get('anomaly', False):
            return EventPrediction(
                event_type='monsoon_surge',
                confidence=0.85,
                description='MONSOON SURGE DETECTED',
                regions=['Bay of Bengal', 'Eastern India'],
                recommendation='Prepare for heavy precipitation'
            )
        elif (ocean.get('exceeds', False) and ocean.get('anomaly', False)) or \
             (arabian.get('exceeds', False) and arabian.get('anomaly', False)):
            return EventPrediction(
                event_type='cyclonic_buildup',
                confidence=0.75,
                description='CYCLONIC MOISTURE BUILD-UP',
                regions=['Indian Ocean', 'Arabian Sea'],
                recommendation='Monitor for cyclone development'
            )
        elif data['max'] > mean_val * 2.5:
            return EventPrediction(
                event_type='atmospheric_instability',
                confidence=0.70,
                description='ATMOSPHERIC INSTABILITY',
                regions=['Global hotspots'],
                recommendation='Severe weather possible'
            )
        elif mean_val < np.mean([s['mean'] for s in self.yearly_summaries.values()]) * 0.8:
            return EventPrediction(
                event_type='dry_phase',
                confidence=0.80,
                description='DRY PHASE SIGNAL',
                regions=['Indian Subcontinent'],
                recommendation='Prepare for drought monitoring'
            )
        else:
            return EventPrediction(
                event_type='stable',
                confidence=0.90,
                description='STABLE ATMOSPHERIC CONDITION',
                regions=['Global'],
                recommendation='Normal monitoring'
            )
    
    def generate_advanced_3d_globe(self, year: int) -> Dict:
        lats, lons, values = self._get_year_data(year)
        
        if len(values) == 0:
            return {}
        
        colorscale = [[0, "rgb(0,0,80)"], [0.25, "rgb(0,100,150)"], 
                      [0.5, "rgb(0,200,200)"], [0.75, "rgb(255,200,0)"], [1, "rgb(255,50,50)"]]
        
        data_trace = go.Scattergeo(
            lat=lats,
            lon=lons,
            mode='markers',
            marker=dict(
                size=3,
                color=values,
                colorscale=colorscale,
                showscale=True,
                colorbar=dict(title='WV (ppm)', titleside='right', titlefont=dict(color='white'),
                             tickfont=dict(color='white'), thickness=15, len=0.5),
                opacity=0.8
            ),
            text=[f"Lat: {lat:.1f}°<br>Lon: {lon:.1f}°<br>WV: {v:.1f} ppm" for lat, lon, v in zip(lats, lons, values)],
            hoverinfo='text',
            name='Water Vapour'
        )
        
        max_idx = np.argmax(values)
        max_lat, max_lon, max_val = lats[max_idx], lons[max_idx], values[max_idx]
        
        max_trace = go.Scattergeo(
            lat=[max_lat],
            lon=[max_lon],
            mode='markers',
            marker=dict(size=15, color='red', symbol='star', line=dict(color='yellow', width=2)),
            text=f"<b>MAXIMUM</b><br>Lat: {max_lat:.1f}°<br>Lon: {max_lon:.1f}°<br>WV: {max_val:.1f} ppm",
            hoverinfo='text',
            name='Maximum'
        )
        
        layout = dict(
            title=dict(text=f'NICES WATER VAPOUR | {year}', font=dict(size=18, color='white'), x=0.5),
            geo=dict(
                projection=dict(type='orthographic', rotation=dict(lon=80, lat=20)),
                showland=True,
                landcolor='rgb(30, 40, 50)',
                showocean=True,
                oceancolor='rgb(5, 15, 35)',
                showcountries=True,
                countrycolor='rgb(60, 80, 100)',
                showcoastlines=True,
                coastlinecolor='rgb(80, 100, 120)',
                bgcolor='rgba(0,0,0,0)',
                lonaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                lataxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            ),
            paper_bgcolor='rgba(5, 10, 25, 0.95)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01,
                       bgcolor='rgba(0,0,0,0.7)', font=dict(color='white')),
            margin=dict(l=0, r=0, t=60, b=0),
            autosize=True
        )
        
        return dict(data=[data_trace, max_trace], layout=layout)
    
    def get_climate_intelligence(self, year: int) -> Dict[str, Any]:
        globe = self.generate_advanced_3d_globe(year)
        trend = self.generate_trend_timeseries(year)
        anomaly = self.detect_anomaly(year)
        event = self.predict_event(year)
        
        stats = self.yearly_summaries.get(year, {})
        
        return {
            'status': 'success',
            'year': year,
            'globe': globe,
            'trend': trend,
            'anomaly': asdict(anomaly),
            'event': asdict(event),
            'statistics': {
                'mean': stats.get('mean', 0),
                'max': stats.get('max', 0),
                'min': stats.get('min', 0),
                'std': stats.get('std', 0)
            }
        }


climate_engine = ClimateIntelligenceEngine()

def initialize_climate_engine():
    return climate_engine

def get_climate_data(year: int):
    return climate_engine.get_climate_intelligence(year)
