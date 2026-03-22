import os, re, zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
import numpy as np
import xarray as xr

@dataclass(frozen=True)
class TrendSeries:
    dates: list[date]
    values: list[float]

_DEFAULT_DATASET_DIR = Path(__file__).resolve().parent / "watervapour_dataset"
_DEFAULT_VAR_NAME = "water_vapor_profile"


def _parse_date_from_path(path: str) -> date | None:
    m = re.search(r"(20\d{6})", Path(path).name)
    if not m:
        m = re.search(r"(20\d{6})", str(path))
    if not m:
        return None
    yyyymmdd = m.group(1)
    try:
        return date(int(yyyymmdd[0:4]), int(yyyymmdd[4:6]), int(yyyymmdd[6:8]))
    except ValueError:
        return None


def _dataset_dir(dataset_dir: str | Path | None) -> Path:
    if dataset_dir is None:
        return _DEFAULT_DATASET_DIR
    return Path(dataset_dir)


def list_nc_files(dataset_dir: str | Path | None = None) -> list[str]:
    base = _dataset_dir(dataset_dir)
    if not base.exists():
        raise FileNotFoundError(f"Dataset folder not found: {base}")

    paths: list[str] = []
    for root, _dirs, files in os.walk(base):
        for f in files:
            if f.endswith(".nc") or f.endswith(".zip"):
                paths.append(str(Path(root) / f))

    def _sort_key(p: str) -> tuple[int, str]:
        d = _parse_date_from_path(p)
        return (int(d.strftime("%Y%m%d")) if d else 99999999, p)

    return sorted(paths, key=_sort_key)


@lru_cache(maxsize=8)
def build_date_index(dataset_dir: str | Path | None = None) -> dict[date, str]:
    paths = list_nc_files(dataset_dir)
    index: dict[date, str] = {}
    for p in paths:
        d = _parse_date_from_path(p)
        if d is not None:
            index[d] = p
    return index


def load_dataset(path: str) -> xr.Dataset:
    if path.endswith('.zip'):
        # Extract and load from zip
        with zipfile.ZipFile(path, 'r') as zf:
            nc_files = [f for f in zf.namelist() if f.endswith('.nc')]
            if not nc_files:
                raise FileNotFoundError(f"No .nc file found in zip: {path}")
            # Extract to temp and load
            temp_dir = Path(path).parent / ".temp"
            temp_dir.mkdir(exist_ok=True)
            zf.extract(nc_files[0], temp_dir)
            nc_path = temp_dir / nc_files[0]
            ds = xr.open_dataset(str(nc_path))
            try:
                yield ds
            finally:
                ds.close()
                # Cleanup
                try:
                    nc_path.unlink()
                except:
                    pass
    else:
        ds = xr.open_dataset(path)
        try:
            yield ds
        finally:
            ds.close()


@contextmanager
def load_dataset_ctx(path: str):
    if path.endswith('.zip'):
        with zipfile.ZipFile(path, 'r') as zf:
            nc_files = [f for f in zf.namelist() if f.endswith('.nc')]
            if not nc_files:
                raise FileNotFoundError(f"No .nc file found in zip: {path}")
            temp_dir = Path(path).parent / ".temp"
            temp_dir.mkdir(exist_ok=True)
            zf.extract(nc_files[0], temp_dir)
            nc_path = temp_dir / nc_files[0]
            ds = xr.open_dataset(str(nc_path))
            try:
                yield ds
            finally:
                ds.close()
                try:
                    nc_path.unlink()
                except:
                    pass
    else:
        ds = xr.open_dataset(path)
        try:
            yield ds
        finally:
            ds.close()


def _get_var(ds: xr.Dataset, var_name: str | None) -> xr.DataArray:
    name = var_name or _DEFAULT_VAR_NAME
    if name not in ds.data_vars:
        raise KeyError(f"Variable '{name}' not found in dataset. Available: {list(ds.data_vars)}")
    return ds[name]


@lru_cache(maxsize=1)
def compute_average_vapour(
    dataset_dir: str | Path | None = None,
    var_name: str | None = None,
) -> float:
    paths = list_nc_files(dataset_dir)
    if not paths:
        raise FileNotFoundError("No .nc files found in dataset directory")

    daily_means: list[float] = []
    for p in paths:
        with load_dataset_ctx(p) as ds:
            v = _get_var(ds, var_name).mean(skipna=True).values
            daily_means.append(float(v))

    return float(np.mean(daily_means))


def compute_trend(
    dataset_dir: str | Path | None = None,
    var_name: str | None = None,
) -> TrendSeries:
    paths = list_nc_files(dataset_dir)
    if not paths:
        raise FileNotFoundError("No .nc files found in dataset directory")

    dates: list[date] = []
    values: list[float] = []
    for idx, p in enumerate(paths):
        with load_dataset_ctx(p) as ds:
            v = _get_var(ds, var_name).mean(skipna=True).values
            values.append(float(v))
        d = _parse_date_from_path(p)
        dates.append(d if d else date.fromordinal(date(1970, 1, 1).toordinal() + idx))

    return TrendSeries(dates=dates, values=values)


def compute_daily_average_vapour(
    day: date,
    dataset_dir: str | Path | None = None,
    var_name: str | None = None,
) -> float:
    index = build_date_index(dataset_dir)
    if day not in index:
        raise FileNotFoundError(f"No dataset file found for date {day.isoformat()}")
    with load_dataset_ctx(index[day]) as ds:
        v = _get_var(ds, var_name).mean(skipna=True).values
        return float(v)


def compute_monthly_average_vapour(
    year: int,
    month: int,
    dataset_dir: str | Path | None = None,
    var_name: str | None = None,
) -> float:
    index = build_date_index(dataset_dir)
    days = sorted([d for d in index.keys() if d.year == year and d.month == month])
    if not days:
        raise FileNotFoundError(f"No dataset files found for {year:04d}-{month:02d}")
    vals = [compute_daily_average_vapour(d, dataset_dir=dataset_dir, var_name=var_name) for d in days]
    return float(np.mean(vals))


def compute_trend_range(
    start: date,
    end: date,
    dataset_dir: str | Path | None = None,
    var_name: str | None = None,
) -> TrendSeries:
    if end < start:
        start, end = end, start
    index = build_date_index(dataset_dir)
    days = sorted([d for d in index.keys() if start <= d <= end])
    if not days:
        raise FileNotFoundError(
            f"No dataset files found in range {start.isoformat()} to {end.isoformat()}"
        )
    values = [compute_daily_average_vapour(d, dataset_dir=dataset_dir, var_name=var_name) for d in days]
    return TrendSeries(dates=days, values=values)


def list_available_dates(dataset_dir: str | Path | None = None) -> list[date]:
    index = build_date_index(dataset_dir)
    return sorted(index.keys())


def pick_file_for_date(day: date, dataset_dir: str | Path | None = None) -> str:
    index = build_date_index(dataset_dir)
    if day not in index:
        raise FileNotFoundError(f"No dataset file found for date {day.isoformat()}")
    return index[day]


def list_files_for_range(start: date, end: date, dataset_dir: str | Path | None = None) -> list[str]:
    if end < start:
        start, end = end, start
    index = build_date_index(dataset_dir)
    days = sorted([d for d in index.keys() if start <= d <= end])
    if not days:
        raise FileNotFoundError(
            f"No dataset files found in range {start.isoformat()} to {end.isoformat()}"
        )
    return [index[d] for d in days]


def load_field_2d(
    path: str,
    var_name: str | None = None,
    level: int | None = None,
    reduce_level: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with load_dataset_ctx(path) as ds:
        v = _get_var(ds, var_name)
        lat = ds["lat"].values
        lon = ds["lon"].values

        if "level" in v.dims:
            if level is not None:
                v2d = v.isel(level=level)
            elif reduce_level:
                v2d = v.mean(dim="level", skipna=True)
            else:
                v2d = v.isel(level=0)
        else:
            v2d = v

        return np.asarray(lat), np.asarray(lon), np.asarray(v2d.values)


def pick_sample_file(dataset_dir: str | Path | None = None) -> str:
    paths = list_nc_files(dataset_dir)
    if not paths:
        raise FileNotFoundError("No .nc files found in dataset directory")
    return paths[0]


def compute_max_min_values(
    path: str | None = None,
    dataset_dir: str | Path | None = None,
) -> dict:
    if path is None:
        path = pick_sample_file(dataset_dir)
    
    lat, lon, field = load_field_2d(path)
    
    max_val = np.nanmax(field)
    min_val = np.nanmin(field)
    mean_val = np.nanmean(field)
    
    max_idx = np.unravel_index(np.nanargmax(field), field.shape)
    max_lat = float(lat[max_idx[0]])
    max_lon = float(lon[max_idx[1]])
    
    min_idx = np.unravel_index(np.nanargmin(field), field.shape)
    min_lat = float(lat[min_idx[0]])
    min_lon = float(lon[min_idx[1]])
    
    return {
        "max_value": float(max_val),
        "max_lat": max_lat,
        "max_lon": max_lon,
        "min_value": float(min_val),
        "min_lat": min_lat,
        "min_lon": min_lon,
        "mean_value": float(mean_val),
        "lat_range": (float(lat.min()), float(lat.max())),
        "lon_range": (float(lon.min()), float(lon.max())),
        "grid_shape": field.shape,
    }