"""Auditable integration of time-aligned DMI station temperature and DK2 prices.

All simulations retain synthetic IT load, heat demand coefficients and plant
hardware.  Observed inputs are exogenous boundary conditions, not calibration.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from .io import read_hourly_prices


def read_hourly_weather(path, expected_times):
    """Require an exact UTC hourly grid and explicit observation/imputation flags."""
    raw = pd.read_csv(path)
    required = {'time_utc', 'ambient_c', 'quality'}
    if not required.issubset(raw.columns):
        raise ValueError(f"Weather CSV must contain {sorted(required)}")
    times = pd.DatetimeIndex(pd.to_datetime(raw['time_utc'], utc=True))
    expected = pd.DatetimeIndex(pd.to_datetime(expected_times, utc=True))
    if times.has_duplicates or not times.is_monotonic_increasing or not times.equals(expected):
        missing = expected.difference(times)
        extra = times.difference(expected)
        raise ValueError(f"Weather UTC coverage mismatch: {len(missing)} missing; {len(extra)} extra; or unsorted/duplicate")
    temp = pd.to_numeric(raw['ambient_c'], errors='coerce').to_numpy(dtype=float)
    if (not np.isfinite(temp).all()) or ((temp < -50) | (temp > 50)).any():
        raise ValueError('Weather temperatures are missing, nonfinite, or implausible')
    allowed={'observed', 'interpolated'}
    flags=raw['quality'].astype(str).str.lower()
    if not set(flags).issubset(allowed):
        raise ValueError('Weather quality flag must be observed or interpolated')
    return temp, flags.to_numpy(), int((flags == 'interpolated').sum())


def build_observed_profiles(config, synthetic):
    """Apply observed covariates, recompute ALL quantities depending on ambient T."""
    p = synthetic.copy()
    ps = config.get('profiles', {})
    weather_path=ps.get('observed_weather_csv')
    elec_path=ps.get('observed_electricity_csv')
    meta={"price_data": "synthetic", "ambient_data":"synthetic",
          "load_and_heat_demand":"hypothetical parametric models", "weather_imputed_hours":0}
    if weather_path:
        weather, quality, n_imputed=read_hourly_weather(weather_path, p['time_utc'])
        p['ambient_c']=weather
        p['weather_quality']=quality
        net=config['network']; src=config['source']
        p['district_demand_mw']=np.clip(
            float(net['base_demand_mw']) + float(net['heating_demand_per_degree_mw'])*np.maximum(
                0., float(net['heating_balance_temperature_c']) - weather),
            0.,float(net['max_demand_mw']))
        p['district_supply_c']=np.clip(
            float(net['design_supply_c']) + float(net['supply_reset_c_per_c'])*(8.-weather),
            float(net['min_supply_c']),float(net['max_supply_c']))
        p['source_supply_c']=(float(src['source_supply_c']) +
                              float(src['source_ambient_sensitivity_c_per_c'])*(weather-9.))
        meta['ambient_data']='DMI observed station air temperature (with explicit gap flags)'
        meta['weather_imputed_hours']=n_imputed
    if elec_path:
        p['electricity_eur_mwh']=read_hourly_prices(elec_path, p['time_utc'])
        meta['price_data']='Energinet DK2 historical wholesale day-ahead prices'
    return p, meta
