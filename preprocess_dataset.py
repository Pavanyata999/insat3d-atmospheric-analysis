#!/usr/bin/env python3
import os
import re
import zipfile
import tempfile
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp

import numpy as np
import pandas as pd
import xarray as xr
from tqdm import tqdm


@dataclass
class DailyStats:
    date: datetime
    year: int
    month: int
    day: int
    mean_vapour: float
    max_vapour: float
    min_vapour: float
    max_lat: float
    max_lon: float
    min_lat: float
    min_lon: float
    valid_points: int
    total_points: int


def extract_date_from_filename(filename: str) -> Optional[datetime]:
    pattern = r'\d{8}'
    match = re.search(pattern, filename)
    if match:
        date_str = match.group()
        try:
            return datetime.strptime(date_str, '%Y%m%d')
        except ValueError:
            return None
    return None


def compute_daily_stats(zip_path: str, dataset_dir: str) -> Optional[DailyStats]:
    filename = os.path.basename(zip_path)
    date = extract_date_from_filename(filename)
    
    if date is None:
        print(f"Could not extract date from {filename}")
        return None
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            nc_files = [f for f in zf.namelist() if f.endswith('.nc') or f.endswith('.nc4')]
            
            if not nc_files:
                print(f"No NetCDF file found in {filename}")
                return None
            
            with tempfile.TemporaryDirectory() as tmpdir:
                zf.extract(nc_files[0], tmpdir)
                nc_path = os.path.join(tmpdir, nc_files[0])
                
                ds = xr.open_dataset(nc_path)
                
                vapour_var = None
                for var in ['atmosphere_mass_content_of_water_vapor', 'tcwv', 'wv', 'water_vapor']:
                    if var in ds.data_vars:
                        vapour_var = var
                        break
                
                if vapour_var is None:
                    vapour_var = list(ds.data_vars)[0]
                
                data = ds[vapour_var]
                
                if 'time' in data.dims and data.shape[0] == 1:
                    data = data.isel(time=0)
                
                lat = ds.lat.values if 'lat' in ds.coords else ds.latitude.values
                lon = ds.lon.values if 'lon' in ds.coords else ds.longitude.values
                
                valid_mask = ~np.isnan(data.values)
                valid_data = data.values[valid_mask]
                
                if len(valid_data) == 0:
                    print(f"No valid data in {filename}")
                    return None
                
                mean_val = float(np.mean(valid_data))
                max_val = float(np.max(valid_data))
                min_val = float(np.min(valid_data))
                
                max_idx = np.unravel_index(np.nanargmax(data.values), data.values.shape)
                max_lat = float(lat[max_idx[0]])
                max_lon = float(lon[max_idx[1]])
                
                min_idx = np.unravel_index(np.nanargmin(data.values), data.values.shape)
                min_lat = float(lat[min_idx[0]])
                min_lon = float(lon[min_idx[1]])
                
                ds.close()
                
                return DailyStats(
                    date=date,
                    year=date.year,
                    month=date.month,
                    day=date.day,
                    mean_vapour=mean_val,
                    max_vapour=max_val,
                    min_vapour=min_val,
                    max_lat=max_lat,
                    max_lon=max_lon,
                    min_lat=min_lat,
                    min_lon=min_lon,
                    valid_points=int(np.sum(valid_mask)),
                    total_points=int(data.size)
                )
                
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return None


def process_all_files(dataset_dir: str, max_workers: Optional[int] = None) -> pd.DataFrame:
    zip_files = sorted(glob.glob(os.path.join(dataset_dir, "*.zip")))
    
    if not zip_files:
        raise ValueError(f"No ZIP files found in {dataset_dir}")
    
    print(f"Found {len(zip_files)} ZIP files to process")
    
    if max_workers is None:
        max_workers = max(1, mp.cpu_count() - 1)
    
    print(f"Processing with {max_workers} parallel workers...")
    
    results = []
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(compute_daily_stats, zip_path, dataset_dir): zip_path 
            for zip_path in zip_files
        }
        
        # Collect results with progress bar
        for future in tqdm(as_completed(future_to_file), total=len(zip_files), desc="Processing files"):
            result = future.result()
            if result is not None:
                results.append(result)
    
    print(f"\nSuccessfully processed {len(results)} files")
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            'date': r.date,
            'year': r.year,
            'month': r.month,
            'day': r.day,
            'mean_vapour': r.mean_vapour,
            'max_vapour': r.max_vapour,
            'min_vapour': r.min_vapour,
            'max_lat': r.max_lat,
            'max_lon': r.max_lon,
            'min_lat': r.min_lat,
            'min_lon': r.min_lon,
            'valid_points': r.valid_points,
            'total_points': r.total_points
        }
        for r in results
    ])
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    return df


def create_yearly_summary(daily_df: pd.DataFrame) -> pd.DataFrame:
    yearly = daily_df.groupby('year').agg({
        'mean_vapour': 'mean',
        'max_vapour': 'max',
        'min_vapour': 'min'
    }).reset_index()
    
    yearly.columns = ['year', 'mean_vapour', 'max_vapour', 'min_vapour']
    
    return yearly


def create_monthly_summary(daily_df: pd.DataFrame) -> pd.DataFrame:
    monthly = daily_df.groupby(['year', 'month']).agg({
        'mean_vapour': 'mean',
        'max_vapour': 'mean',
        'min_vapour': 'mean'
    }).reset_index()
    
    monthly.columns = ['year', 'month', 'mean_vapour', 'max_vapour', 'min_vapour']
    
    return monthly


def main():
    DATASET_DIR = "watervapour_dataset"
    OUTPUT_DIR = "climate_summaries"
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("=" * 60)
    print("NICeS Climate Dataset Preprocessing Pipeline")
    print("=" * 60)
    print(f"Dataset directory: {DATASET_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    # Check if dataset directory exists
    if not os.path.exists(DATASET_DIR):
        print(f"ERROR: Dataset directory '{DATASET_DIR}' not found!")
        print("Please ensure the watervapour_dataset directory exists.")
        return 1
    
    # Step 1: Process all files
    print("Step 1: Processing daily ZIP files...")
    print("-" * 60)
    daily_df = process_all_files(DATASET_DIR)
    
    # Save daily summary
    daily_path = os.path.join(OUTPUT_DIR, "climate_summary.csv")
    daily_df.to_csv(daily_path, index=False)
    print(f"\nSaved daily summary: {daily_path}")
    print(f"  Records: {len(daily_df)}")
    print(f"  Date range: {daily_df['date'].min()} to {daily_df['date'].max()}")
    print()
    
    # Step 2: Create yearly summary
    print("Step 2: Creating yearly summary...")
    print("-" * 60)
    yearly_df = create_yearly_summary(daily_df)
    
    yearly_path = os.path.join(OUTPUT_DIR, "yearly_summary.csv")
    yearly_df.to_csv(yearly_path, index=False)
    print(f"Saved yearly summary: {yearly_path}")
    print(f"  Records: {len(yearly_df)}")
    print(f"  Years: {yearly_df['year'].min()} to {yearly_df['year'].max()}")
    print()
    
    # Step 3: Create monthly summary
    print("Step 3: Creating monthly summary...")
    print("-" * 60)
    monthly_df = create_monthly_summary(daily_df)
    
    monthly_path = os.path.join(OUTPUT_DIR, "monthly_summary.csv")
    monthly_df.to_csv(monthly_path, index=False)
    print(f"Saved monthly summary: {monthly_path}")
    print(f"  Records: {len(monthly_df)}")
    print()
    
    # Print statistics
    print("=" * 60)
    print("Preprocessing Complete!")
    print("=" * 60)
    print(f"\nSummary Statistics:")
    print(f"  Total files processed: {len(daily_df)}")
    print(f"  Date range: {daily_df['date'].min().date()} to {daily_df['date'].max().date()}")
    print(f"  Mean water vapour range: {daily_df['mean_vapour'].min():.2f} to {daily_df['mean_vapour'].max():.2f}")
    print(f"  Max value ever recorded: {daily_df['max_vapour'].max():.2f}")
    print(f"  Min value ever recorded: {daily_df['min_vapour'].min():.2f}")
    
    print(f"\nOutput files:")
    print(f"  - {daily_path}")
    print(f"  - {yearly_path}")
    print(f"  - {monthly_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
