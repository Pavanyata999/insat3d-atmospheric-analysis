import os
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class TrendResult:
    start_year: int
    end_year: int
    start_value: float
    end_value: float
    slope: float
    percent_change: float
    trend_direction: str
    r_squared: float
    p_value: float
    significant: bool
    years: List[int]
    values: List[float]


@dataclass
class DifferenceResult:
    year1: int
    year2: int
    mean1: float
    mean2: float
    difference: float
    percent_change: float
    direction: str
    max1: float
    max2: float
    min1: float
    min2: float


# Paths to summary files
SUMMARY_DIR = "climate_summaries"
DAILY_SUMMARY_PATH = os.path.join(SUMMARY_DIR, "climate_summary.csv")
YEARLY_SUMMARY_PATH = os.path.join(SUMMARY_DIR, "yearly_summary.csv")
MONTHLY_SUMMARY_PATH = os.path.join(SUMMARY_DIR, "monthly_summary.csv")


@lru_cache(maxsize=1)
def load_yearly_summary() -> Optional[pd.DataFrame]:
    if not os.path.exists(YEARLY_SUMMARY_PATH):
        return None
    
    df = pd.read_csv(YEARLY_SUMMARY_PATH)
    return df


@lru_cache(maxsize=1)
def load_daily_summary() -> Optional[pd.DataFrame]:
    if not os.path.exists(DAILY_SUMMARY_PATH):
        return None
    
    df = pd.read_csv(DAILY_SUMMARY_PATH)
    return df


@lru_cache(maxsize=1)
def load_monthly_summary() -> Optional[pd.DataFrame]:
    if not os.path.exists(MONTHLY_SUMMARY_PATH):
        return None
    
    df = pd.read_csv(MONTHLY_SUMMARY_PATH)
    return df


def get_year_range_trend(start_year: int, end_year: int) -> Optional[TrendResult]:
    df = load_yearly_summary()
    
    if df is None:
        return None
    
    # Filter to requested range
    mask = (df['year'] >= start_year) & (df['year'] <= end_year)
    filtered = df[mask].sort_values('year')
    
    if len(filtered) < 2:
        return None
    
    years = filtered['year'].values
    values = filtered['mean_vapour'].values
    
    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(years, values)
    
    # Calculate trend metrics
    start_value = values[0]
    end_value = values[-1]
    total_change = end_value - start_value
    percent_change = (total_change / start_value) * 100 if start_value != 0 else 0
    
    # Determine trend direction
    if abs(percent_change) < 1.0:  # Less than 1% change
        trend_direction = "stable"
    elif percent_change > 0:
        trend_direction = "increasing"
    else:
        trend_direction = "decreasing"
    
    return TrendResult(
        start_year=start_year,
        end_year=end_year,
        start_value=float(start_value),
        end_value=float(end_value),
        slope=float(slope),
        percent_change=float(percent_change),
        trend_direction=trend_direction,
        r_squared=float(r_value ** 2),
        p_value=float(p_value),
        significant=p_value < 0.05,
        years=years.tolist(),
        values=values.tolist()
    )


def get_difference_between_years(year1: int, year2: int) -> Optional[DifferenceResult]:
    df = load_yearly_summary()
    
    if df is None:
        return None
    
    # Get data for both years
    data1 = df[df['year'] == year1]
    data2 = df[df['year'] == year2]
    
    if len(data1) == 0 or len(data2) == 0:
        return None
    
    mean1 = float(data1['mean_vapour'].iloc[0])
    mean2 = float(data2['mean_vapour'].iloc[0])
    max1 = float(data1['max_vapour'].iloc[0])
    max2 = float(data2['max_vapour'].iloc[0])
    min1 = float(data1['min_vapour'].iloc[0])
    min2 = float(data2['min_vapour'].iloc[0])
    
    difference = mean2 - mean1
    percent_change = (difference / mean1) * 100 if mean1 != 0 else 0
    
    if abs(percent_change) < 1.0:
        direction = "stable"
    elif percent_change > 0:
        direction = "increase"
    else:
        direction = "decrease"
    
    return DifferenceResult(
        year1=year1,
        year2=year2,
        mean1=mean1,
        mean2=mean2,
        difference=difference,
        percent_change=percent_change,
        direction=direction,
        max1=max1,
        max2=max2,
        min1=min1,
        min2=min2
    )


def find_extreme_years(find: str = "highest") -> Optional[Dict]:
    df = load_yearly_summary()
    
    if df is None:
        return None
    
    if find == "highest":
        idx = df['mean_vapour'].idxmax()
        row = df.loc[idx]
        return {
            'year': int(row['year']),
            'mean_vapour': float(row['mean_vapour']),
            'max_vapour': float(row['max_vapour']),
            'min_vapour': float(row['min_vapour']),
            'extreme_type': 'highest'
        }
    elif find == "lowest":
        idx = df['mean_vapour'].idxmin()
        row = df.loc[idx]
        return {
            'year': int(row['year']),
            'mean_vapour': float(row['mean_vapour']),
            'max_vapour': float(row['max_vapour']),
            'min_vapour': float(row['min_vapour']),
            'extreme_type': 'lowest'
        }
    
    return None


def get_largest_change() -> Optional[Dict]:
    df = load_yearly_summary()
    
    if df is None or len(df) < 2:
        return None
    
    df = df.sort_values('year')
    df['change'] = df['mean_vapour'].diff()
    df['abs_change'] = df['change'].abs()
    
    max_change_idx = df['abs_change'].idxmax()
    max_change_row = df.loc[max_change_idx]
    
    # Get previous year
    prev_year = int(max_change_row['year']) - 1
    prev_row = df[df['year'] == prev_year]
    
    if len(prev_row) == 0:
        return None
    
    return {
        'from_year': prev_year,
        'to_year': int(max_change_row['year']),
        'from_value': float(prev_row['mean_vapour'].iloc[0]),
        'to_value': float(max_change_row['mean_vapour']),
        'change': float(max_change_row['change']),
        'abs_change': float(max_change_row['abs_change']),
        'percent_change': float((max_change_row['change'] / prev_row['mean_vapour'].iloc[0]) * 100)
    }


def format_trend_response(trend: TrendResult) -> str:
    direction_emoji = {
        "increasing": "📈",
        "decreasing": "📉",
        "stable": "➡️"
    }
    
    significance_text = "statistically significant" if trend.significant else "not statistically significant"
    
    return f"""{direction_emoji.get(trend.trend_direction, '📊')} <b>TREND ANALYSIS: {trend.start_year} - {trend.end_year}</b><br><br>

• Trend Direction: <b>{trend.trend_direction.title()}</b><br>
• Rate of Change: <b>{trend.slope:+.4f} ppm/year</b><br>
• Total Change: <b>{trend.end_value - trend.start_value:+.3f} ppm</b> ({trend.percent_change:+.2f}%)<br>
• Start Value ({trend.start_year}): <b>{trend.start_value:.3f} ppm</b><br>
• End Value ({trend.end_year}): <b>{trend.end_value:.3f} ppm</b><br>
• R² = {trend.r_squared:.3f} (explains {trend.r_squared*100:.1f}% of variance)<br>
• Significance: <b>{significance_text}</b> (p = {trend.p_value:.4f})<br><br>

<i>This analysis is based on {len(trend.years)} years of pre-computed summary data.</i>"""


def format_difference_response(diff: DifferenceResult) -> str:
    direction_emoji = {
        "increase": "🔺",
        "decrease": "🔻",
        "stable": "➡️"
    }
    
    return f"""{direction_emoji.get(diff.direction, '📊')} <b>DIFFERENCE ANALYSIS: {diff.year1} vs {diff.year2}</b><br><br>

• Mean Change: <b>{diff.difference:+.3f} ppm</b> ({diff.percent_change:+.2f}%)<br>
• Direction: <b>{diff.direction.title()}</b><br><br>

<b>{diff.year1} (Baseline):</b><br>
• Mean: {diff.mean1:.3f} ppm<br>
• Max: {diff.max1:.3f} ppm<br>
• Min: {diff.min1:.3f} ppm<br><br>

<b>{diff.year2} (Comparison):</b><br>
• Mean: {diff.mean2:.3f} ppm<br>
• Max: {diff.max2:.3f} ppm<br>
• Min: {diff.min2:.3f} ppm<br><br>

<i>Instant analysis using pre-computed yearly summaries.</i>"""


# Utility function to check if summaries are available
def summaries_available() -> bool:
    return (
        os.path.exists(YEARLY_SUMMARY_PATH) and
        os.path.exists(DAILY_SUMMARY_PATH) and
        os.path.exists(MONTHLY_SUMMARY_PATH)
    )
