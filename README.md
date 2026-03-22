# INSAT-3D Atmospheric Water Vapour Analysis

A complete system for analyzing atmospheric water vapour data from INSAT-3D satellite.

## Features

- **Data Processing**: Extract and process NetCDF atmospheric data
- **Visualization**: Generate heatmaps, 3D globes, trend charts, and animations
- **AI Chatbot**: Natural language interface for climate queries
- **Climate Intelligence**: Anomaly detection and event prediction
- **Web Interface**: Interactive dashboard for data exploration

## Project Structure

- `analysis_engine.py` - Core data analysis functions
- `chatbot_server.py` - FastAPI backend for chatbot
- `climate_intelligence_engine.py` - AI/ML climate analysis
- `visualization_engine.py` - Plotly visualization generators
- `nices_visualization_platform.py` - Scientific platform backend
- `preprocess_dataset.py` - Data preprocessing pipeline
- `trend_fast.py` - Trend analysis with caching
- `webpage.html` - Main web interface
- `climate_intelligence_ui.js` - Climate UI JavaScript
- `nices_platform_ui.js` - Platform UI JavaScript

## Quick Start

```bash
pip install -r requirements.txt
python chatbot_server.py
```

Then open `webpage.html` in browser.

## Data Source

INSAT-3D atmospheric water vapour measurements from NetCDF files.

## Tech Stack

Python (FastAPI, xarray, numpy, plotly) + JavaScript (Plotly.js)
