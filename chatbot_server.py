from pathlib import Path
import os
import re
from datetime import date, datetime, timedelta
import google.generativeai as genai

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import analysis_engine
from trend_fast import (
    get_year_range_trend,
    get_difference_between_years,
    find_extreme_years,
    get_largest_change,
    format_trend_response,
    format_difference_response,
    summaries_available,
    load_yearly_summary,
)
# New analysis modules
import sys
sys.path.append('analysis_engine')
from max_min_detection import (
    find_global_maximum,
    find_global_minimum,
    find_global_maximum_for_year,
    find_global_minimum_for_year,
    find_global_maximum_for_year_range,
    find_global_minimum_for_year_range,
    format_max_min_response,
)
from event_detection import (
    detect_biggest_event,
    format_event_response,
)
from anomaly_analysis import (
    compute_anomaly_map,
    detect_anomaly_regions,
    format_anomaly_response,
)
from spatial_hotspots import (
    detect_water_vapour_hotspots,
    cluster_hotspots,
    format_hotspots_response,
)
from visualization_engine import (
    generate_3d_globe,
    generate_animation,
    generate_heatmap,
    generate_trend_plot,
    generate_trend_plot_range,
    generate_india_heatmap,
    generate_india_comparison,
)
from visualization_engine_advanced import (
    generate_world_map_with_markers,
    generate_difference_visualization,
    generate_hotspot_map,
    generate_anomaly_visualization,
)
from visualization_engine_enhanced import (
    generate_enhanced_globe_with_markers,
    generate_world_map_with_continents,
)
from visualization_engine_fixed import (
    generate_clear_world_map,
    generate_event_analysis_map,
)
from visualization_engine_full_world import (
    generate_full_world_map_with_continents,
)
from visualization_engine_complete_world import (
    generate_complete_world_map,
)
from visualization_engine_true_full_world import (
    generate_true_full_world_map,
)
from visualization_engine_3d_globe import (
    generate_3d_globe_with_continents,
)
from visualization_engine_matplotlib_globe import (
    generate_matplotlib_globe_alternative,
)
from visualization_engine_simple_full_world import (
    generate_simple_full_world_map,
)
from visualization_engine_ultra_light import (
    generate_ultra_light_world_map,
)
from climate_intelligence_engine import (
    initialize_climate_engine,
    get_climate_data,
    ClimateIntelligenceEngine,
)
from nices_visualization_platform import (
    get_full_analysis,
    get_available_years as get_viz_years,
    nices_platform,
)

DATASET_DIR = Path(__file__).resolve().parent / "watervapour_dataset"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
async def read_root():
    return FileResponse("webpage.html", media_type="text/html")

@app.get("/debug")
async def debug_page():
    return FileResponse("debug.html", media_type="text/html")

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/get_climate_intelligence")
async def get_climate_intelligence(year: int = 2009):
    try:
        climate_data = get_climate_data(year, str(DATASET_DIR))
        
        return {
            "status": "success",
            "year": year,
            "globe": climate_data.get('globe', {}),
            "trend": climate_data.get('trend', {}),
            "value": climate_data.get('current_value', 0),
            "mean": climate_data.get('mean_value', 0),
            "std": climate_data.get('std_value', 0),
            "anomaly": climate_data.get('anomaly', {}),
            "event": climate_data.get('event', {}),
            "stats": climate_data.get('stats', {}),
            "message": "Climate intelligence data retrieved successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "year": year,
            "message": str(e),
            "globe": {},
            "trend": {},
            "anomaly": {},
            "event": {}
        }

@app.get("/get_available_years")
async def get_available_years():
    try:
        years = get_viz_years()
        return {
            "status": "success",
            "years": years,
            "count": len(years)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/get_full_analysis")
async def get_full_analysis_endpoint(year: int = 2023):
    try:
        analysis = get_full_analysis(year)
        return analysis
    except Exception as e:
        return {
            "status": "error",
            "year": year,
            "message": str(e),
            "spatial_map": {},
            "globe_map": {},
            "animation_frames": {},
            "trend_graph": {},
            "vertical_profile": {},
            "insight": {"summary": "Error", "recommendation": str(e), "alert_level": "error"}
        }
    try:
        paths = analysis_engine.list_nc_files(str(DATASET_DIR))
        years = []
        for p in paths:
            match = re.search(r'(19\d{2}|20\d{2})', p)
            if match:
                year = int(match.group(1))
                if year not in years:
                    years.append(year)
        years.sort()
        
        return {
            "status": "success",
            "years": years,
            "count": len(years),
            "range": f"{min(years)}-{max(years)}" if years else "N/A"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "years": []
        }

def _classify_question(question: str) -> dict:
    q = question.lower()
    
    dates = _extract_dates(question)
    month_year = _extract_month_year(question)
    has_date_range = _extract_date_range(question) is not None
    
    if any(kw in q for kw in ("which area has maximum", "where is maximum", "maximum location", "highest location", "area with maximum", "maximum globe", "tell me the maximum", "maximum globe vapours", "maximum vapour in world map", "maximum vapour year", "give me the maximum")):
        if "world map" in q:
            return {"intent": "world_map_max", "source": "dataset"}
        else:
            return {"intent": "max_location", "source": "dataset"}
    if any(kw in q for kw in ("where is minimum", "minimum location", "lowest location", "area with minimum", "minimum vapour in world map", "minimum vapour year", "give me the minimum")):
        if "world map" in q:
            return {"intent": "world_map_min", "source": "dataset"}
        else:
            return {"intent": "min_location", "source": "dataset"}
    
    if any(kw in q for kw in ("biggest event", "largest event", "major event", "significant event", "climate event", "give me the event", "the event between")):
        return {"intent": "biggest_event", "source": "dataset"}
    
    if any(kw in q for kw in ("hotspot", "hotspots", "moisture hotspot", "vapour hotspot", "show hotspots")):
        return {"intent": "hotspot_detection", "source": "dataset"}
    
    if any(kw in q for kw in ("global map", "world map", "show global", "earth map", "full map")):
        return {"intent": "global_map", "source": "dataset"}
    
    if any(g in q for g in ("hi", "hello", "hey", "good morning", "good afternoon", "good evening", "thanks", "thank you", "bye", "goodbye")):
        return {"intent": "greeting", "source": "api"}
    
    if dates or month_year or has_date_range:
        if "average" in q or "mean" in q:
            return {"intent": "average", "source": "dataset"}
        if "trend" in q or "timeseries" in q or "time series" in q:
            return {"intent": "trend", "source": "dataset"}
        if "compare" in q or "difference" in q:
            return {"intent": "compare", "source": "dataset"}
    
    if "heatmap" in q or "heat map" in q or "distribution" in q:
        return {"intent": "heatmap", "source": "dataset"}
    if "globe" in q or "3d" in q or "earth" in q:
        return {"intent": "globe", "source": "dataset"}
    if "animation" in q or "animate" in q:
        return {"intent": "animation", "source": "dataset"}
    
    if "india" in q:
        if "max" in q or "highest" in q or "maximum" in q or "location" in q:
            return {"intent": "india_heatmap", "source": "dataset"}
        if "map" in q or "heatmap" in q or "heat map" in q:
            return {"intent": "india_heatmap", "source": "dataset"}
        if "comparison" in q or "compare" in q or "vs" in q or "versus" in q:
            return {"intent": "india_comparison", "source": "dataset"}
        return {"intent": "india_heatmap", "source": "dataset"}
    
    if any(kw in q for kw in ("spatial trend", "trend map", "trend pattern")):
        return {"intent": "spatial_trend", "source": "dataset"}
    
    if "average" in q or "mean" in q:
        return {"intent": "average", "source": "dataset"}
    if "trend" in q:
        return {"intent": "trend", "source": "dataset"}
    
    return {"intent": "general", "source": "api"}


_MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def _extract_dates(question: str) -> list[date]:
    q = question.lower()
    out: list[date] = []
    
    # ISO format: 2023-01-15 or 2023/01/15
    for m in re.findall(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b", q):
        y, mo, d = (int(m[0]), int(m[1]), int(m[2]))
        try:
            out.append(date(y, mo, d))
        except ValueError:
            pass
    
    # Compact: 20230115
    for s in re.findall(r"\b(20\d{6})\b", q):
        try:
            out.append(date(int(s[0:4]), int(s[4:6]), int(s[6:8])))
        except ValueError:
            pass
    
    return out


def _extract_month_year(question: str) -> tuple[int, int] | None:
    q = question.lower()
    
    # Pattern: month year (e.g., "feb 2023")
    m = re.search(r"\b([a-z]{3,9})\s+(20\d{2})\b", q)
    if m:
        month_name = m.group(1)
        year = int(m.group(2))
        month = _MONTHS.get(month_name)
        if month:
            return (year, month)
    
    # Pattern: year month (e.g., "2023 feb")
    m = re.search(r"\b(20\d{2})\s+([a-z]{3,9})\b", q)
    if m:
        year = int(m.group(1))
        month_name = m.group(2)
        month = _MONTHS.get(month_name)
        if month:
            return (year, month)
    
    return None


def _extract_date_range(question: str) -> tuple[date, date] | None:
    q = question.lower()
    
    # Try to find two dates
    dates = _extract_dates(q)
    if len(dates) >= 2:
        return (dates[0], dates[1])
    
    # Pattern: month day to month day
    range_match = re.search(
        r"(?:from\s+)?([a-z]{3,9})\s+(\d{1,2})(?:\s*,?\s+(20\d{2}))?(?:\s+to\s+|\s*-\s*)([a-z]{3,9})\s+(\d{1,2})(?:\s*,?\s+(20\d{2}))?",
        q
    )
    
    if range_match:
        start_month = _MONTHS.get(range_match.group(1))
        start_day = int(range_match.group(2))
        start_year = int(range_match.group(3)) if range_match.group(3) else 2023
        
        end_month = _MONTHS.get(range_match.group(4))
        end_day = int(range_match.group(5))
        end_year = int(range_match.group(6)) if range_match.group(6) else 2023
        
        try:
            start_date = date(start_year, start_month, start_day)
            end_date = date(end_year, end_month, end_day)
            return (start_date, end_date)
        except ValueError:
            pass
    
    # Try single month as range
    month_year = _extract_month_year(question)
    if month_year:
        year, month = month_year
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        return (date(year, month, 1), date(year, month, last_day))
    
    return None


def _call_openai_api(prompt: str, context: str = "") -> str | None:
    """Call OpenAI API with short timeout to avoid hanging."""
    api_key = os.getenv("GEMINI_API_KEY")  # Using same env var for compatibility
    if not api_key:
        return None
    
    try:
        import socket
        from openai import OpenAI
        
        # Set socket timeout to avoid hanging
        socket.setdefaulttimeout(10)
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.unli.dev/v1"  # Unli.dev API endpoint
        )
        
        full_prompt = f"""You are a climate research assistant for NICeS (NRSC/ISRO) Stratospheric Water Vapour project.

User question: {prompt}
{f'Context: {context}' if context else ''}

Provide a helpful, scientifically accurate response in 3-8 sentences."""
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful climate research assistant."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        text = resp.choices[0].message.content if resp.choices else None
        
        # Reset socket timeout
        socket.setdefaulttimeout(None)
        
        if text:
            return str(text).strip()
    except Exception as e:
        print(f"API error (expected if offline): {type(e).__name__}: {e}")
    
    return None


def _greeting_reply(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ("hi", "hello", "hey")):
        return "Hello! I'm your NICeS Water Vapour Research Assistant. I can help you analyze stratospheric water vapour data from Jan-Mar 2023, or answer general questions about the dataset and atmospheric science. What would you like to explore?"
    if any(w in q for w in ("good morning", "good afternoon", "good evening")):
        return "Good day! I'm ready to assist with your water vapour analysis. Ask me about specific dates, trends, visualizations, or general atmospheric science questions."
    if any(w in q for w in ("thanks", "thank you")):
        return "You're welcome! Happy to help with your research. Let me know if you need more analysis or have other questions."
    if any(w in q for w in ("bye", "goodbye")):
        return "Goodbye! Feel free to return anytime for more insights. Have a great day!"
    return "Hi! I'm here to help with the NICeS stratospheric water vapour dataset. What can I do for you today?"


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    index_path = Path(__file__).resolve().parent / "frontend" / "index.html"
    if not index_path.exists():
        return HTMLResponse(
            "<h3>Frontend not found</h3><p>Create frontend/index.html to use the demo UI.</p>",
            status_code=404,
        )
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/chat")
def chat(question: str):
    classification = _classify_question(question)
    intent = classification["intent"]
    source = classification["source"]
    
    dates = _extract_dates(question)
    month_year = _extract_month_year(question)
    date_range = _extract_date_range(question)
    
    try:
        # GREETING
        if intent == "greeting":
            local_reply = _greeting_reply(question)
            gemini_reply = _call_openai_api(question) if source == "api" else None
            final = gemini_reply or local_reply
            return {
                "answer": final,
                "source": "api" if gemini_reply else "local",
                "visualization": None,
                "visualization_plotly": None,
            }
        
        # GENERAL KNOWLEDGE
        if intent == "general_knowledge":
            gemini_reply = _call_openai_api(question)
            if gemini_reply:
                return {
                    "answer": gemini_reply,
                    "source": "api",
                    "visualization": None,
                    "visualization_plotly": None,
                }
            # Comprehensive local fallback
            q_lower = question.lower()
            if "water vapour" in q_lower or "water vapor" in q_lower:
                local_response = """Water vapour (H₂O) is water in its gaseous state and is a critical component of Earth's atmosphere. In the stratosphere (10-50 km altitude), water vapour plays several key roles:

1. Greenhouse Effect: It traps outgoing infrared radiation, contributing to atmospheric warming
2. Ozone Chemistry: Water vapour affects the formation and destruction of stratospheric ozone
3. Climate Feedback: Changes in stratospheric water vapour can amplify or dampen climate change
4. Radiative Forcing: It directly influences Earth's energy balance

The NICeS dataset provides stratospheric water vapour profiles measured by satellite instruments (likely MLS or similar) during January-March 2023. The data includes 36 pressure levels, covering latitudes -90° to +90° and longitudes -180° to +165°, with daily temporal resolution."""
            elif "stratosphere" in q_lower:
                local_response = """The stratosphere is the second major layer of Earth's atmosphere, located above the troposphere and below the mesosphere, at altitudes of approximately 10-50 km (6-31 miles).

Key characteristics:
• Temperature increases with altitude due to ozone absorption of UV radiation
• Contains the ozone layer which protects life from harmful UV radiation  
• Very dry compared to the troposphere (water vapour ~3-5 ppmv vs ~1-4%)
• Home to commercial jet aircraft and weather balloons
• Stratospheric water vapour is a potent greenhouse gas and affects ozone chemistry

The NICeS dataset focuses specifically on stratospheric water vapour measurements."""
            elif "atmosphere" in q_lower:
                local_response = """Earth's atmosphere is divided into five main layers:

1. Troposphere (0-10 km): Where weather occurs, contains ~80% of atmospheric mass
2. Stratosphere (10-50 km): Contains ozone layer, dry, temperature increases with altitude
3. Mesosphere (50-85 km): Temperature decreases, coldest layer, meteors burn up here
4. Thermosphere (85-600 km): Very hot but thin, auroras occur, ISS orbits here
5. Exosphere (>600 km): Transitions to space, extremely thin

Water vapour is concentrated in the troposphere but the small amounts in the stratosphere are climatically significant. The NICeS project monitors stratospheric water vapour using satellite remote sensing."""
            else:
                local_response = "Water vapour is water in gaseous form and plays a crucial role in Earth's climate system. The NICeS dataset provides stratospheric water vapour measurements from Jan-Mar 2023. Ask about specific dates for detailed analysis."
            
            return {
                "answer": local_response,
                "source": "local",
                "visualization": None,
                "visualization_plotly": None,
            }
        
        # PROJECT INFO
        if intent == "project_info":
            gemini_reply = _call_openai_api(question, "NICeS = NRSC ISRO Consolidated Earth Observation System")
            if gemini_reply:
                return {
                    "answer": gemini_reply,
                    "source": "api",
                    "visualization": None,
                    "visualization_plotly": None,
                }
            
            local_response = """NICeS (NRSC ISRO Consolidated Earth Observation System)

About the Project:
• NICeS is an initiative by the National Remote Sensing Centre (NRSC), Indian Space Research Organisation (ISRO)
• It consolidates satellite-based Earth observation data for research and applications
• This specific dataset focuses on stratospheric water vapour measurements

Dataset Details (Jan-Mar 2023):
• Temporal Coverage: January 1 - March 31, 2023 (90 days)
• Spatial Coverage: Global (lat: -90° to +90°, lon: -180° to +165°)
• Vertical Levels: 36 pressure levels (stratosphere focus)
• Data Source: Satellite remote sensing (likely Microwave Limb Sounder or similar)
• Format: NetCDF (.nc) files, one per day
• Variables: water_vapor_profile, point_counts, std_values, quality_flag

Available Analysis:
• Daily/monthly average calculations
• Time-series trend analysis  
• Spatial distribution maps (heatmap, 3D globe)
• Temporal animations
• Date range comparisons

Ask about specific dates, trends, or request visualizations to explore the data!"""
            
            return {
                "answer": local_response,
                "source": "local",
                "visualization": None,
                "visualization_plotly": None,
            }
        
        # AVERAGE
        if intent == "average":
            if len(dates) == 1:
                value = analysis_engine.compute_daily_average_vapour(dates[0])
                base = f"Dataset Analysis (Jan-Mar 2023): Daily mean water vapour on {dates[0].strftime('%B %d, %Y')} is {value:.2f} units. This value represents the stratospheric water vapour concentration averaged across all pressure levels and geographic locations for that specific day."
                return {
                    "answer": base,
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
            
            if month_year is not None:
                y, m = month_year
                value = analysis_engine.compute_monthly_average_vapour(y, m)
                month_name = ["January", "February", "March"][m-1] if m <= 3 else "Month"
                base = f"Dataset Analysis (Jan-Mar 2023): Monthly mean water vapour for {month_name} {y} is {value:.2f} units. This represents the average stratospheric water vapour concentration across all days in {month_name}."
                return {
                    "answer": base,
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
            
            if date_range is not None:
                start, end = date_range
                series = analysis_engine.compute_trend_range(start, end)
                avg_value = sum(series.values) / len(series.values) if series.values else 0
                base = f"Dataset Analysis (Jan-Mar 2023): Average water vapour from {start.strftime('%B %d, %Y')} to {end.strftime('%B %d, %Y')} is {avg_value:.2f} units. Analysis covers {len(series.dates)} days of stratospheric water vapour data."
                return {
                    "answer": base,
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
            
            value = analysis_engine.compute_average_vapour()
            available_dates = analysis_engine.list_available_dates()
            base = f"Dataset Analysis (Jan-Mar 2023): Overall average water vapour for the entire dataset is {value:.2f} units. This average is computed from {len(available_dates)} daily NetCDF files spanning January 1 to March 31, 2023, covering all stratospheric pressure levels and geographic regions."
            return {
                "answer": base,
                "source": "dataset",
                "visualization": None,
                "visualization_plotly": None,
            }
        
        # TREND - Use fast trend analysis with pre-computed summaries
        if intent == "trend":
            # Check if we have year range in question
            years_in_q = [int(y) for y in re.findall(r'\b(20\d{2})\b', question)]
            
            if summaries_available() and len(years_in_q) >= 2:
                # Use fast trend analysis
                start_year, end_year = years_in_q[0], years_in_q[1]
                trend = get_year_range_trend(start_year, end_year)
                
                if trend:
                    response = format_trend_response(trend)
                    
                    # Create simple trend visualization
                    import plotly.graph_objects as go
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=trend.years,
                        y=trend.values,
                        mode='lines+markers',
                        name='Mean Water Vapour',
                        line=dict(color='#00E5CC', width=2)
                    ))
                    
                    # Add trend line
                    fit_values = [trend.slope * y + (trend.values[0] - trend.slope * trend.years[0]) 
                                  for y in trend.years]
                    fig.add_trace(go.Scatter(
                        x=trend.years,
                        y=fit_values,
                        mode='lines',
                        name=f'Trend: {trend.slope:+.4f} ppm/year',
                        line=dict(color='#FF6B6B', width=2, dash='dash')
                    ))
                    
                    fig.update_layout(
                        title=f"Water Vapour Trend ({start_year}-{end_year})",
                        xaxis_title="Year",
                        yaxis_title="Mean Water Vapour (ppm)",
                        template="plotly_dark"
                    )
                    
                    spec = fig.to_dict()
                    
                    return {
                        "answer": response,
                        "source": "dataset",
                        "visualization": "trend",
                        "visualization_plotly": spec,
                    }
            
            # Handle single year - show yearly data or compare with previous year
            if summaries_available() and len(years_in_q) == 1:
                # Single year requested - show that year's data or compare with previous
                target_year = years_in_q[0]
                
                # Load yearly summary
                df = load_yearly_summary()
                if df is not None:
                    # Get data for requested year and create a simple trend with surrounding years
                    year_data = df[df['year'] == target_year]
                    if len(year_data) > 0:
                        # Get surrounding years for context (±2 years)
                        surrounding = df[(df['year'] >= target_year - 2) & (df['year'] <= target_year + 2)]
                        
                        if len(surrounding) >= 2:
                            years = surrounding['year'].tolist()
                            values = surrounding['mean_vapour'].tolist()
                            
                            # Create visualization
                            import plotly.graph_objects as go
                            fig = go.Figure()
                            
                            # Highlight the requested year
                            colors = ['#00E5CC' if y == target_year else '#506784' for y in years]
                            sizes = [12 if y == target_year else 8 for y in years]
                            
                            fig.add_trace(go.Scatter(
                                x=years,
                                y=values,
                                mode='lines+markers',
                                name='Mean Water Vapour',
                                line=dict(color='#00E5CC', width=2),
                                marker=dict(size=sizes, color=colors)
                            ))
                            
                            fig.update_layout(
                                title=f"Water Vapour Context Around {target_year}",
                                xaxis_title="Year",
                                yaxis_title="Mean Water Vapour (ppm)",
                                template="plotly_dark",
                                annotations=[dict(
                                    x=target_year,
                                    y=year_data['mean_vapour'].iloc[0],
                                    text=f"{target_year}: {year_data['mean_vapour'].iloc[0]:.3f} ppm",
                                    showarrow=True,
                                    arrowhead=2,
                                    ax=0,
                                    ay=-40
                                )]
                            )
                            
                            spec = fig.to_dict()
                            
                            response = f"""📊 <b>YEAR {target_year} - WATER VAPOUR ANALYSIS</b><br><br>

<b>📈 Statistics for {target_year}:</b><br>
• Mean Value: <b>{year_data['mean_vapour'].iloc[0]:.3f} ppm</b><br>
• Maximum: <b>{year_data['max_vapour'].iloc[0]:.3f} ppm</b><br>
• Minimum: <b>{year_data['min_vapour'].iloc[0]:.3f} ppm</b><br><br>

<i>⚠️ Note: Trend analysis requires at least 2 years. Showing {target_year} data in context with surrounding years.</i><br><br>

<b>For trend analysis, try:</b><br>
• "trend from 2005 to 2009"<br>
• "water vapour trend 2006-2010"""""
                            
                            return {
                                "answer": response,
                                "source": "dataset",
                                "visualization": "trend",
                                "visualization_plotly": spec,
                            }
            if date_range is not None or len(dates) >= 2:
                start = dates[0] if len(dates) >= 2 else date_range[0]
                end = dates[1] if len(dates) >= 2 else date_range[1]
                spec, description = generate_trend_plot_range(start, end)
                base = description
            else:
                spec, description = generate_trend_plot()
                base = description
            
            return {
                "answer": base,
                "source": "dataset",
                "visualization": "trend",
                "visualization_plotly": spec,
            }
        
        # COMPARE
        if intent == "compare":
            if len(dates) >= 2:
                val1 = analysis_engine.compute_daily_average_vapour(dates[0])
                val2 = analysis_engine.compute_daily_average_vapour(dates[1])
                diff = val2 - val1
                pct = ((val2 - val1) / val1 * 100) if val1 else 0
                base = f"Comparison Analysis: {dates[0].strftime('%B %d, %Y')}: {val1:.2f} units | {dates[1].strftime('%B %d, %Y')}: {val2:.22f} units | Difference: {diff:+.2f} units ({pct:+.1f}%) | {'Increased' if diff > 0 else 'Decreased'} water vapour concentration observed between these dates."
                return {
                    "answer": base,
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
            return {
                "answer": "To compare water vapour values, specify two dates. For example: 'compare Jan 15 and Feb 20' or 'difference between 2023-01-15 and 2023-02-20'",
                "source": "local",
                "visualization": None,
                "visualization_plotly": None,
            }
        
        # HEATMAP
        if intent == "heatmap":
            spec, description = generate_heatmap()
            return {
                "answer": description,
                "source": "dataset",
                "visualization": "heatmap",
                "visualization_plotly": spec,
            }
        
        # GLOBE
        if intent == "globe":
            spec, description = generate_3d_globe()
            return {
                "answer": description,
                "source": "dataset",
                "visualization": "globe",
                "visualization_plotly": spec,
            }
        
        # ANIMATION
        if intent == "animation":
            spec, description = generate_animation()
            return {
                "answer": description,
                "source": "dataset",
                "visualization": "animation",
                "visualization_plotly": spec,
            }
        
        # INDIA HEATMAP with year support
        if intent == "india_heatmap":
            years_full = re.findall(r'\b(19\d{2}|20\d{2})\b', question)
            target_year = int(years_full[0]) if years_full else None
            
            spec, description = generate_india_heatmap(str(DATASET_DIR), year=target_year)
            year_text = f" (Year: {target_year})" if target_year else ""
            return {
                "answer": f"🇮🇳 <b>INDIA WATER VAPOUR MAP{year_text}</b><br><br>" + description,
                "source": "dataset",
                "visualization": "india_heatmap",
                "visualization_plotly": spec,
            }
        
        # INDIA COMPARISON
        if intent == "india_comparison":
            spec, description = generate_india_comparison()
            return {
                "answer": description,
                "source": "dataset",
                "visualization": "india_comparison",
                "visualization_plotly": spec,
            }
        
        # MAX VALUE - Read actual data and show
        if intent == "max_value":
            stats = analysis_engine.compute_max_min_values(dataset_dir=DATASET_DIR)
            max_response = f"""🌟 <b>MAXIMUM WATER VAPOUR ANALYSIS</b><br><br>
            
<b>📊 Maximum Value Detected:</b><br>
• <b>Value:</b> {stats['max_value']:.2f} ppm<br>
• <b>📍 Location:</b> {stats['max_lat']}°N, {stats['max_lon']}°E<br>
• <b>🌡️ Mean Value (Global):</b> {stats['mean_value']:.2f} ppm<br>
• <b>📈 Above Mean:</b> +{((stats['max_value']/stats['mean_value']-1)*100):.1f}%<br><br>

<b>📉 Minimum Value (for comparison):</b><br>
• <b>Value:</b> {stats['min_value']:.2f} ppm<br>
• <b>📍 Location:</b> {stats['min_lat']}°N, {stats['min_lon']}°E<br><br>

<b>🗺️ Spatial Coverage:</b><br>
• <b>Latitude Range:</b> {stats['lat_range'][0]}° to {stats['lat_range'][1]}°<br>
• <b>Longitude Range:</b> {stats['lon_range'][0]}° to {stats['lon_range'][1]}°<br>
• <b>Grid Size:</b> {stats['grid_shape'][0]} × {stats['grid_shape'][1]} points<br><br>

<b>💡 Insights:</b><br>
• Maximum typically occurs in tropical regions<br>
• High values near equator due to warm temperatures<br>
• Seasonal variations affect these values<br><br>

Type <b>'heatmap'</b> to see where this maximum is located!"""
            return {
                "answer": max_response,
                "source": "dataset",
                "visualization": None,
                "visualization_plotly": None,
            }
        
        # MIN VALUE - Read actual data and show
        if intent == "min_value":
            stats = analysis_engine.compute_max_min_values(dataset_dir=DATASET_DIR)
            min_response = f"""📉 <b>MINIMUM WATER VAPOUR ANALYSIS</b><br><br>
            
<b>📊 Minimum Value Detected:</b><br>
• <b>Value:</b> {stats['min_value']:.2f} ppm<br>
• <b>📍 Location:</b> {stats['min_lat']}°N, {stats['min_lon']}°E<br>
• <b>🌡️ Mean Value (Global):</b> {stats['mean_value']:.2f} ppm<br>
• <b>📉 Below Mean:</b> -{((1-stats['min_value']/stats['mean_value'])*100):.1f}%<br><br>

<b>📈 Maximum Value (for comparison):</b><br>
• <b>Value:</b> {stats['max_value']:.2f} ppm<br>
• <b>📍 Location:</b> {stats['max_lat']}°N, {stats['max_lon']}°E<br><br>

<b>🗺️ Spatial Coverage:</b><br>
• <b>Latitude Range:</b> {stats['lat_range'][0]}° to {stats['lat_range'][1]}°<br>
• <b>Longitude Range:</b> {stats['lon_range'][0]}° to {stats['lon_range'][1]}°<br>
• <b>Grid Size:</b> {stats['grid_shape'][0]} × {stats['grid_shape'][1]} points<br><br>

<b>💡 Insights:</b><br>
• Minimum typically occurs in polar regions<br>
• Low values due to cold temperatures and low humidity<br>
• Stratospheric air is very dry at high latitudes<br><br>

Type <b>'heatmap'</b> to see where this minimum is located!"""
            return {
                "answer": min_response,
                "source": "dataset",
                "visualization": None,
                "visualization_plotly": None,
            }
        
        # LAT/LON INFO - Show coordinates info with actual data
        if intent == "lat_lon_info":
            stats = analysis_engine.compute_max_min_values(dataset_dir=DATASET_DIR)
            lat_lon_response = f"""📍 <b>DATASET COORDINATE INFORMATION</b><br><br>
            
<b>🌍 Global Coverage:</b><br>
• <b>Latitude Range:</b> {stats['lat_range'][0]}° to {stats['lat_range'][1]}°<br>
• <b>Longitude Range:</b> {stats['lon_range'][0]}° to {stats['lon_range'][1]}°<br>
• <b>Grid Resolution:</b> 5° latitude × 15° longitude<br>
• <b>Grid Points:</b> {stats['grid_shape'][0]} lat × {stats['grid_shape'][1]} lon = {stats['grid_shape'][0] * stats['grid_shape'][1]} points<br><br>

<b>🇮🇳 India Region Coverage:</b><br>
• <b>Latitude Range:</b> 8°N to 37°N<br>
• <b>Longitude Range:</b> 68°E to 97°E<br>
• <b>Major Cities Mapped:</b> Delhi, Mumbai, Chennai, Kolkata, Bengaluru, Hyderabad<br><br>

<b>� Key Coordinates with High Water Vapour:</b><br>
• <b>Global Max:</b> {stats['max_lat']}°N, {stats['max_lon']}°E ({stats['max_value']:.2f} ppm)<br>
• <b>Global Min:</b> {stats['min_lat']}°N, {stats['min_lon']}°E ({stats['min_value']:.2f} ppm)<br>
• <b>Tropics:</b> ±20° latitude show highest values (6-7 ppm)<br>
• <b>Polar:</b> ±80°+ show lowest values (3-4 ppm)<br><br>

Type <b>'globe'</b> or <b>'heatmap'</b> to see the spatial distribution!"""
            return {
                "answer": lat_lon_response,
                "source": "dataset",
                "visualization": None,
                "visualization_plotly": None,
            }
        
        # COVERAGE INFO - Show coverage with actual data
        if intent == "coverage_info":
            stats = analysis_engine.compute_max_min_values(dataset_dir=DATASET_DIR)
            coverage_response = f"""🗺️ <b>DATASET COVERAGE & RESOLUTION</b><br><br>
            
<b>⏰ Temporal Coverage (20-Year Dataset):</b><br>
• <b>Period:</b> 2004 - 2024 (20 years)<br>
• <b>Files:</b> ~7,800 NetCDF files (zipped)<br>
• <b>Daily Files:</b> One file per day across 20 years<br><br>

<b>🌐 Spatial Coverage:</b><br>
• <b>Type:</b> Global<br>
• <b>Lat:</b> {stats['lat_range'][0]}° to {stats['lat_range'][1]}°<br>
• <b>Lon:</b> {stats['lon_range'][0]}° to {stats['lon_range'][1]}°<br>
• <b>Grid:</b> {stats['grid_shape'][0]} × {stats['grid_shape'][1]} = {stats['grid_shape'][0] * stats['grid_shape'][1]} points<br>
• <b>Resolution:</b> 5° × 15°<br><br>

<b>📊 Data Statistics:</b><br>
• <b>Mean Value:</b> {stats['mean_value']:.2f} ppm<br>
• <b>Max Value:</b> {stats['max_value']:.2f} ppm at ({stats['max_lat']}°, {stats['max_lon']}°)<br>
• <b>Min Value:</b> {stats['min_value']:.2f} ppm at ({stats['min_lat']}°, {stats['min_lon']}°)<br><br>

<b>📏 Vertical Levels:</b> 36 pressure levels (stratosphere: 10-50 km)<br><br>
<b>💧 Variables:</b> water_vapor_profile, point_counts, std_values<br><br>
<b>📈 Capabilities:</b> Heatmaps, 3D globe, 20-year trends, India analysis, animation"""
            return {
                "answer": coverage_response,
                "source": "dataset",
                "visualization": None,
                "visualization_plotly": None,
            }
        
        # GENERAL - try API first
        if intent == "general":
            gemini_reply = _call_openai_api(question)
            if gemini_reply:
                return {
                    "answer": gemini_reply,
                    "source": "api",
                    "visualization": None,
                    "visualization_plotly": None,
                }
        
        # TREND ANALYSIS - Mann-Kendall test and Sen's slope
        if intent == "trend_analysis":
            from climate_chatbot.analysis_engine.trend_analysis import analyze_dataset_trend
            from climate_chatbot.visualization_engine import generate_trend_analysis_plot
            
            result = analyze_dataset_trend(DATASET_DIR)
            
            if "error" in result:
                return {
                    "answer": f"Error in trend analysis: {result['error']}",
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
            
            # Generate visualization
            trend_viz_data = {
                "time_series": [],  # Will be populated from result
                "times": [],
                "mann_kendall": result["mann_kendall"],
                "sens_slope": result["sens_slope"]
            }
            spec, _ = generate_trend_analysis_plot(trend_viz_data)
            
            mk = result["mann_kendall"]
            sens = result["sens_slope"]
            
            response = f"""📈 <b>STATISTICAL TREND ANALYSIS</b><br><br>
            
<b>Mann-Kendall Test:</b><br>
• Trend: <b>{mk['trend'].title()}</b><br>
• p-value: <b>{mk['p_value']:.4f}</b> ({'significant' if mk['significant'] else 'not significant'})<br>
• Kendall's τ: <b>{mk['tau']:.3f}</b><br><br>

<b>Sen's Slope Estimator:</b><br>
• Rate: <b>{sens['slope']:+.4f} ppm/year</b><br>
• Decadal trend: <b>{sens['trend_per_decade']:+.3f} ppm/decade</b><br>
• 95% CI: [{sens['confidence_interval'][0]:.4f}, {sens['confidence_interval'][1]:.4f}]<br><br>

<b>Summary:</b><br>
{result['summary']}"""
            
            return {
                "answer": response,
                "source": "dataset",
                "visualization": "trend_analysis",
                "visualization_plotly": spec,
            }
        
        # CHANGE POINT DETECTION - PELT algorithm
        if intent == "change_detection":
            from climate_chatbot.analysis_engine.change_point_detection import analyze_dataset_change_points
            from climate_chatbot.visualization_engine import generate_change_point_plot
            
            result = analyze_dataset_change_points(DATASET_DIR)
            
            if "error" in result:
                return {
                    "answer": f"Error in change point detection: {result['error']}",
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
            
            # Generate visualization (simplified)
            spec = {}  # Placeholder
            
            response = f"""🔄 <b>CHANGE POINT DETECTION (PELT)</b><br><br>
            
{result.get('summary', 'Analysis completed')}<br><br>

<b>Detected Regimes:</b> {result.get('num_segments', 0)}<br>
<b>Time Range:</b> {result.get('time_range', 'N/A')}"""
            
            return {
                "answer": response,
                "source": "dataset",
                "visualization": "change_point",
                "visualization_plotly": spec,
            }
        
        # ANOMALY MAP
        if intent == "anomaly_map":
            from climate_chatbot.analysis_engine.anomaly_detection import analyze_dataset_anomalies
            from climate_chatbot.visualization_engine import generate_anomaly_map
            
            # Try to extract year from question
            years_in_q = [int(y) for y in re.findall(r'\b(20\d{2})\b', question)]
            target_year = years_in_q[0] if years_in_q else 2016
            
            result = analyze_dataset_anomalies(DATASET_DIR, target_year=target_year)
            
            if "error" in result:
                return {
                    "answer": f"Error in anomaly analysis: {result['error']}",
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
            
            # Generate anomaly map
            anomaly_data = {
                "lat": result["lat"],
                "lon": result["lon"],
                "anomaly_map": result["anomaly_map"]
            }
            spec, _ = generate_anomaly_map(anomaly_data, title=f"Water Vapour Anomaly - {target_year}")
            
            max_anom = result["max_anomaly"]
            
            response = f"""🌡️ <b>ANOMALY ANALYSIS - {target_year}</b><br><br>
            
<b>Summary:</b><br>
{result['summary']}<br><br>

<b>Maximum Anomaly:</b><br>
• Value: <b>{max_anom['value']:+.3f} ppm</b><br>
• Location: <b>{max_anom['lat']:.1f}°N, {max_anom['lon']:.1f}°E</b><br><br>

<b>Statistics:</b><br>
• Mean Anomaly: {result['mean_anomaly']:+.3f} ppm<br>
• Std Deviation: {result['std_anomaly']:.3f} ppm"""
            
            return {
                "answer": response,
                "source": "dataset",
                "visualization": "anomaly_map",
                "visualization_plotly": spec,
            }
        
        # DIFFERENCE MAP
        if intent == "difference_map":
            # Try to extract two years for comparison
            years_in_q = [int(y) for y in re.findall(r'\b(20\d{2})\b', question)]
            
            if len(years_in_q) >= 2:
                year1, year2 = years_in_q[0], years_in_q[1]
            else:
                year1, year2 = 2004, 2024  # Default comparison
            
            response = f"""📊 <b>DIFFERENCE MAP</b><br><br>
            
Comparing <b>{year2}</b> vs <b>{year1}</b><br><br>

<i>Detailed difference analysis requires loading two time periods and computing spatial differences. This feature compares the mean values between two years and highlights regions with significant changes.</i><br><br>

<b>Query:</b> {question}<br>
<b>Years detected:</b> {years_in_q if years_in_q else 'None - using defaults (2004 vs 2024)'}"""
            
            return {
                "answer": response,
                "source": "dataset",
                "visualization": None,
                "visualization_plotly": None,
            }
        
        # CORRELATION ANALYSIS
        if intent == "correlation_analysis":
            response = f"""🔗 <b>CORRELATION ANALYSIS</b><br><br>
            
<i>Correlation analysis compares relationships between different climate variables (e.g., water vapour and precipitation). This requires multiple datasets to be loaded and analyzed together.</i><br><br>

<b>Available Methods:</b><br>
• Pearson correlation (linear)<br>
• Spearman rank correlation (monotonic)<br>
• Kendall's tau<br>
• Lag correlation for delayed effects<br><br>

<b>Note:</b> Full correlation analysis requires precipitation dataset to be available alongside water vapour data."""
            
            return {
                "answer": response,
                "source": "dataset",
                "visualization": None,
                "visualization_plotly": None,
            }
        
        # EXTREME YEARS - Fast query using summaries
        if intent == "extreme_years":
            # Determine if user wants highest or lowest
            find_type = "highest"
            if "lowest" in question or "least" in question or "min" in question:
                find_type = "lowest"
            
            if summaries_available():
                extreme = find_extreme_years(find_type)
                
                if extreme:
                    response = f"""🏆 <b>EXTREME YEAR ANALYSIS</b><br><br>
                    
<b>{find_type.title()} Water Vapour Recorded:</b><br>
• Year: <b>{extreme['year']}</b><br>
• Mean Value: <b>{extreme['mean_vapour']:.3f} ppm</b><br>
• Max Value: <b>{extreme['max_vapour']:.3f} ppm</b><br>
• Min Value: <b>{extreme['min_vapour']:.3f} ppm</b><br><br>

<i>Instant analysis using pre-computed yearly summaries.</i>"""
                else:
                    response = "Unable to retrieve extreme year data from summaries."
            else:
                response = "Summary data not available. Please run preprocessing first."
            
            return {
                "answer": response,
                "source": "dataset",
                "visualization": None,
                "visualization_plotly": None,
            }
        
        # LARGEST CHANGE - Fast query using summaries
        if intent == "event_detection":
            if "biggest change" in question.lower() or "largest change" in question.lower():
                if summaries_available():
                    change = get_largest_change()
                    
                    if change:
                        response = f"""🔄 <b>LARGEST CHANGE DETECTED</b><br><br>
                        
<b>Change from {change['from_year']} to {change['to_year']}:</b><br>
• Magnitude: <b>{change['abs_change']:.3f} ppm</b><br>
• Direction: {'🔺 Increase' if change['change'] > 0 else '🔻 Decrease'}<br>
• From Value: {change['from_value']:.3f} ppm<br>
• To Value: {change['to_value']:.3f} ppm<br>
• Percent Change: <b>{change['percent_change']:+.2f}%</b><br><br>

<i>Instant analysis using pre-computed yearly summaries.</i>"""
                    else:
                        response = "Unable to retrieve change data from summaries."
                else:
                    response = "Summary data not available. Please run preprocessing first."
                
                return {
                    "answer": response,
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
            
            # Default event detection response
            response = f"""⚠️ <b>EVENT DETECTION</b><br><br>
            
<i>Automatically detect extreme events and largest changes in the climate dataset.</i><br><br>

<b>Detection Methods:</b><br>
• Statistical threshold detection (>2σ events)<br>
• Change point analysis<br>
• Spatial anomaly detection<br><br>

<b>Try asking:</b><br>
• 'Show me the biggest change'<br>
• 'What year had the highest water vapour?'"""
            
            return {
                "answer": response,
                "source": "dataset",
                "visualization": None,
                "visualization_plotly": None,
            }
        
        # WORLD MAP WITH MINIMUM - NEW
        if intent == "world_map_min":
            # Extract years from query if provided
            years_full = re.findall(r'\b(19\d{2}|20\d{2})\b', question)
            target_year = None
            year_range = None
            
            if len(years_full) == 1:
                # Single year specified
                target_year = int(years_full[0])
                min_result = find_global_minimum_for_year(str(DATASET_DIR), target_year)
            elif len(years_full) >= 2:
                # Year range specified
                start_year = int(years_full[0])
                end_year = int(years_full[1])
                year_range = (start_year, end_year)
                min_result = find_global_minimum_for_year_range(str(DATASET_DIR), start_year, end_year)
            else:
                # No year specified, use overall minimum
                min_result = find_global_minimum(str(DATASET_DIR))
            
            if min_result:
                # Add year information to response
                year_info = ""
                if target_year:
                    year_info = f" (Year: {target_year})"
                elif year_range:
                    year_info = f" (Years: {year_range[0]}-{year_range[1]})"
                
                # Use enhanced response format
                response = format_max_min_response(min_result, "minimum")
                
                # Update title to include year information
                if year_info:
                    response = response.replace("MINIMUM WATER VAPOUR DETECTED", 
                                              f"MINIMUM WATER VAPOUR DETECTED{year_info}")
                
                response += f"""<br><br>
<b>🌍 REALISTIC GLOBE VISUALIZATION:</b><br>
• 🌐 <b>Matplotlib-powered globe</b> - professional scientific rendering<br>
• 🔵 <b>Minimum location marked</b> with blue diamond<br>
• 📊 <b>Atmospheric water vapour</b> on sphere surface<br>
• �️ <b>Realistic continents</b> with accurate boundaries<br>
• � <b>Interactive 3D rotation</b> - drag to spin globe<br><br>

<i>Realistic globe: Professional matplotlib rendering with accurate continent shapes and atmospheric data!</i>"""
                
                # Generate ultra-light world map for better performance
                spec = generate_ultra_light_world_map(
                    max_lat=None,
                    max_lon=None,
                    max_value=None,
                    min_lat=min_result.lat if min_result else None,
                    min_lon=min_result.lon if min_result else None,
                    min_value=min_result.value if min_result else None,
                    title=f"Minimum Water Vapour - Fast Response{year_info}"
                )
                
                return {
                    "answer": response,
                    "source": "dataset",
                    "visualization": "complete_world_map",
                    "visualization_plotly": spec,
                }
            else:
                year_info = ""
                if target_year:
                    year_info = f" for year {target_year}"
                elif year_range:
                    year_info = f" for years {year_range[0]}-{year_range[1]}"
                
                return {
                    "answer": f"Unable to detect global minimum location{year_info}.",
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
        
        # WORLD MAP WITH MAXIMUM - NEW
        if intent == "world_map_max":
            # Extract years from query if provided
            years_full = re.findall(r'\b(19\d{2}|20\d{2})\b', question)
            target_year = None
            year_range = None
            
            if len(years_full) == 1:
                # Single year specified
                target_year = int(years_full[0])
                max_result = find_global_maximum_for_year(str(DATASET_DIR), target_year)
            elif len(years_full) >= 2:
                # Year range specified
                start_year = int(years_full[0])
                end_year = int(years_full[1])
                year_range = (start_year, end_year)
                max_result = find_global_maximum_for_year_range(str(DATASET_DIR), start_year, end_year)
            else:
                # No year specified, use overall maximum
                max_result = find_global_maximum(str(DATASET_DIR))
            
            if max_result:
                # Add year information to response
                year_info = ""
                if target_year:
                    year_info = f" (Year: {target_year})"
                elif year_range:
                    year_info = f" (Years: {year_range[0]}-{year_range[1]})"
                
                # Use enhanced response format
                response = format_max_min_response(max_result, "maximum")
                
                # Update title to include year information
                if year_info:
                    response = response.replace("MAXIMUM WATER VAPOUR DETECTED", 
                                              f"MAXIMUM WATER VAPOUR DETECTED{year_info}")
                
                response += f"""<br><br>
<b>🌍 WORLD MAP VISUALIZATION:</b><br>
• 🗺️ <b>Complete world view</b> - shows entire globe<br>
• 🔴 <b>Maximum location marked</b> with red star<br>
• 📊 <b>Water vapour distribution</b> across all continents<br>
• 🌍 <b>Realistic continents</b> with accurate boundaries<br>
• 🔍 <b>Interactive exploration</b> - zoom anywhere<br><br>

<i>Interactive world map: Hover for details, scroll to zoom, drag to pan. Maximum location clearly marked!</i>"""
                
                # Generate ultra-light world map for better performance
                spec = generate_ultra_light_world_map(
                    max_lat=max_result.lat if max_result else None,
                    max_lon=max_result.lon if max_result else None,
                    max_value=max_result.value if max_result else None,
                    min_lat=None,
                    min_lon=None,
                    min_value=None,
                    title=f"Maximum Water Vapour - Fast Response{year_info}"
                )
                
                return {
                    "answer": response,
                    "source": "dataset",
                    "visualization": "complete_world_map",
                    "visualization_plotly": spec,
                }
            else:
                year_info = ""
                if target_year:
                    year_info = f" for year {target_year}"
                elif year_range:
                    year_info = f" for years {year_range[0]}-{year_range[1]}"
                
                return {
                    "answer": f"Unable to detect global maximum location{year_info}.",
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
        
        # MAX LOCATION DETECTION - NEW
        if intent == "max_location":
            # Extract years from query if provided
            years_full = re.findall(r'\b(19\d{2}|20\d{2})\b', question)
            target_year = None
            year_range = None
            
            if len(years_full) == 1:
                # Single year specified
                target_year = int(years_full[0])
            elif len(years_full) >= 2:
                # Year range specified
                start_year = int(years_full[0])
                end_year = int(years_full[1])
                year_range = (start_year, end_year)
            
            max_result = find_global_maximum(str(DATASET_DIR))
            
            if max_result:
                # Add year information to response
                year_info = ""
                if target_year:
                    year_info = f" (Year: {target_year})"
                elif year_range:
                    year_info = f" (Years: {year_range[0]}-{year_range[1]})"
                
                response = format_max_min_response(max_result, "maximum")
                
                # Update response title to include year information
                if year_info:
                    response = response.replace("GLOBAL MAXIMUM WATER VAPOUR DETECTED", 
                                              f"GLOBAL MAXIMUM WATER VAPOUR DETECTED{year_info}")
                
                # Generate enhanced 3D globe visualization
                spec = generate_enhanced_globe_with_markers(
                    max_lat=max_result.lat,
                    max_lon=max_result.lon,
                    max_value=max_result.value,
                    title=f"Global Maximum Water Vapour{year_info} - {max_result.date}"
                )
                
                return {
                    "answer": response,
                    "source": "dataset",
                    "visualization": "enhanced_globe",
                    "visualization_plotly": spec,
                }
            else:
                return {
                    "answer": "Unable to detect global maximum location.",
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
        
        # MIN LOCATION DETECTION - NEW
        if intent == "min_location":
            min_result = find_global_minimum(str(DATASET_DIR))
            
            if min_result:
                response = format_max_min_response(min_result, "minimum")
                
                # Generate visualization
                spec = generate_world_map_with_markers(max_lat=None, max_lon=None, 
                                                      min_lat=min_result.lat, min_lon=min_result.lon, 
                                                      title="Global Minimum Water Vapour")
                
                return {
                    "answer": response,
                    "source": "dataset",
                    "visualization": "global_min_map",
                    "visualization_plotly": spec,
                }
            else:
                return {
                    "answer": "Unable to detect global minimum location.",
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
        
        # BIGGEST EVENT DETECTION - NEW
        if intent == "biggest_event":
            # Extract years from query if provided
            years = re.findall(r'\b(19|20)\d{2}\b', question)
            # Fix: Need to match the full 4-digit year
            years_full = re.findall(r'\b(19\d{2}|20\d{2})\b', question)
            start_year = int(years_full[0]) if len(years_full) > 0 else 2002
            end_year = int(years_full[1]) if len(years_full) > 1 else 2020
            
            event = detect_biggest_event(start_year, end_year)
            
            if event:
                response = format_event_response(event)
                
                # Generate enhanced event visualization
                event_data = {
                    'magnitude': event.magnitude,
                    'percent_change': event.percent_change,
                    'year': event.year
                }
                spec = generate_event_analysis_map(event.year, event.year - 1, event_data)
                
                return {
                    "answer": response,
                    "source": "dataset",
                    "visualization": "event_analysis_map",
                    "visualization_plotly": spec,
                }
            else:
                return {
                    "answer": f"Unable to detect significant events between {start_year} and {end_year}.",
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
        
        # HOTSPOT DETECTION - NEW
        if intent == "hotspot_detection":
            hotspots = detect_water_vapour_hotspots(top_n=5)
            
            if hotspots:
                # Cluster hotspots
                clusters = cluster_hotspots(hotspots)
                
                response = format_hotspots_response(hotspots, clusters)
                
                # Generate visualization
                spec = generate_hotspot_map(hotspots, clusters)
                
                return {
                    "answer": response,
                    "source": "dataset",
                    "visualization": "hotspot_map",
                    "visualization_plotly": spec,
                }
            else:
                return {
                    "answer": "Unable to detect water vapour hotspots.",
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
        
        # GLOBAL MAP WITH MARKERS - NEW
        if intent == "global_map":
            # Extract years from query if provided
            years_full = re.findall(r'\b(19\d{2}|20\d{2})\b', question)
            target_year = None
            year_range = None
            year_info = ""
            
            if len(years_full) == 1:
                # Single year specified
                target_year = int(years_full[0])
                max_result = find_global_maximum_for_year(str(DATASET_DIR), target_year)
                min_result = find_global_minimum_for_year(str(DATASET_DIR), target_year)
                year_info = f" (Year: {target_year})"
            elif len(years_full) >= 2:
                # Year range specified
                start_year = int(years_full[0])
                end_year = int(years_full[1])
                year_range = (start_year, end_year)
                max_result = find_global_maximum_for_year_range(str(DATASET_DIR), start_year, end_year)
                min_result = find_global_minimum_for_year_range(str(DATASET_DIR), start_year, end_year)
                year_info = f" (Years: {start_year}-{end_year})"
            else:
                # No year specified, use overall max/min
                max_result = find_global_maximum(str(DATASET_DIR))
                min_result = find_global_minimum(str(DATASET_DIR))
                year_info = " (All Years)"
            
            response = f"""🌍 <b>COMPLETE WORLD MAP - FULL GLOBE VIEW{year_info}</b><br><br>
            
<b>📍 Extreme Locations:</b><br>
"""
            
            if max_result:
                response += f"""• <b>Maximum:</b> {max_result.value:.3f} ppm at {max_result.lat:.1f}°N, {max_result.lon:.1f}°E ({max_result.region})<br>"""
            
            if min_result:
                response += f"""• <b>Minimum:</b> {min_result.value:.3f} ppm at {min_result.lat:.1f}°N, {min_result.lon:.1f}°E ({min_result.region})<br>"""
            
            response += f"""<br>
<b>🌍 COMPLETE WORLD MAP FEATURES:</b><br>
• 🗺️ <b>Full globe view</b> - shows entire world (not half!)<br>
• 🌎 <b>All continents visible</b> - Asia, Africa, Americas, Europe, Australia<br>
• 🏝️ <b>Complete coastlines</b> - no cut-off continents<br>
• 🌊 <b>Full ocean coverage</b> - Pacific, Atlantic, Indian, Arctic<br>
• 📐 <b>Complete coordinate system</b> -180° to 180° longitude<br>
• 🔍 <b>Interactive exploration</b> - zoom anywhere on Earth<br><br>

<b>🔍 Scientific Overview:</b><br>
This complete world map shows the ENTIRE globe with all continents fully visible{year_info.lower()}. No more half-maps! You can see the complete global distribution of stratospheric water vapour across all longitudes (-180° to 180°) and latitudes (-90° to 90°).<br><br>

<i>Complete world map: Full globe, all continents, no cut-offs{year_info.lower()}!</i>"""
            
            # Generate ultra-light world map for better performance
            spec = generate_ultra_light_world_map(
                max_lat=max_result.lat if max_result else None,
                max_lon=max_result.lon if max_result else None,
                max_value=max_result.value if max_result else None,
                min_lat=min_result.lat if min_result else None,
                min_lon=min_result.lon if min_result else None,
                min_value=min_result.value if min_result else None,
                title=f"COMPLETE WORLD MAP - Fast Response{year_info}"
            )
            
            return {
                "answer": response,
                "source": "dataset",
                "visualization": "complete_world_map",
                "visualization_plotly": spec,
            }
        
        # ENHANCED ANOMALY MAP - NEW
        if intent == "anomaly_map":
            # Extract year from query
            years = re.findall(r'\b(19|20)\d{2}\b', question)
            target_year = int(years[0]) if years else 2016  # Default to 2016
            
            anomaly_result = compute_anomaly_map(target_year)
            
            if anomaly_result:
                regions = detect_anomaly_regions(anomaly_result)
                response = format_anomaly_response(anomaly_result, regions)
                
                # Generate visualization
                spec = generate_anomaly_visualization(anomaly_result)
                
                return {
                    "answer": response,
                    "source": "dataset",
                    "visualization": "anomaly_map",
                    "visualization_plotly": spec,
                }
            else:
                return {
                    "answer": f"Unable to compute anomaly map for {target_year}.",
                    "source": "dataset",
                    "visualization": None,
                    "visualization_plotly": None,
                }
        
        # HELP / DEFAULT
        help_text = """🤖 <b>NICeS Water Vapour Research Assistant</b> - Available Commands:<br><br>

<b>📊 Dataset Queries (20-Year Data 2004-2024):</b><br>
• <b>'average on 2023-01-15'</b> - Daily average<br>
• <b>'average Feb 2023'</b> - Monthly average<br>
• <b>'average from Jan 21 to March 23'</b> - Date range<br>
• <b>'trend'</b> - Full 20-year time series<br>
• <b>'compare Jan 15 and Feb 20'</b> - Compare dates<br><br>

<b>🗺️ Spatial Analysis:</b><br>
• <b>'heatmap'</b> - Global spatial distribution<br>
• <b>'globe'</b> or <b>'3D earth'</b> - Interactive 3D globe<br>
• <b>'animation'</b> - Time-lapse animation<br><br>

<b>🇮🇳 India-Specific:</b><br>
• <b>'india map'</b> - India regional map with max location<br>
• <b>'india comparison'</b> - India vs global comparison<br><br>

<b>� Advanced Climate Analysis (NEW):</b><br>
• <b>'Which area has maximum water vapour'</b> - Global maximum detection<br>
• <b>'Where is minimum water vapour'</b> - Global minimum detection<br>
• <b>'Biggest event between 2002 and 2020'</b> - Major climate events<br>
• <b>'Show vapour hotspots'</b> - Moisture hotspot detection<br>
• <b>'Global map'</b> - World map with extreme locations<br>
• <b>'Anomaly map for 2016'</b> - Yearly anomaly analysis<br><br>

<b>📈 Statistical Analysis:</b><br>
• <b>'trend analysis'</b> - Mann-Kendall test + Sen's slope<br>
• <b>'change point'</b> - PELT regime shift detection<br>
• <b>'difference 2004 vs 2024'</b> - Compare two periods<br>
• <b>'correlation'</b> - Variable correlation analysis<br>
• <b>'event detection'</b> - Extreme event identification<br><br>

<b>📊 Data Intelligence (20-Year Analysis):</b><br>
• <b>'what is the max'</b> or <b>'highest value'</b> - Maximum water vapour across 20 years<br>
• <b>'what is the min'</b> or <b>'lowest value'</b> - Minimum water vapour across 20 years<br>
• <b>'latitudes and longitudes'</b> - Coordinate information<br>
• <b>'coverage'</b> or <b>'grid resolution'</b> - 20-year dataset coverage details<br><br>

<b>💡 General Questions:</b><br>
• <b>'What is water vapour?'</b> - Scientific explanation<br>
• <b>'What is NICeS?'</b> - Project information<br>
• <b>'Explain stratospheric water vapour'</b> - Educational content<br><br>

Just ask naturally - I understand questions about <b>locations, max/min values, coordinates, trends, comparisons, and statistical analysis</b> across <b>20 years of data</b>! 🌍"""
        
        return {
            "answer": help_text,
            "source": "local",
            "visualization": None,
            "visualization_plotly": None,
        }
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
