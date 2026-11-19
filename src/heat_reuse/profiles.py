"""Deterministic synthetic boundary conditions, NOT measured Copenhagen data."""
from __future__ import annotations
import numpy as np
import pandas as pd


def make_synthetic_profiles(config):
    y = int(config["time"]["year"])
    t = pd.date_range(f"{y}-01-01", f"{y+1}-01-01", freq="h", inclusive="left", tz="UTC")
    n = len(t)
    d = t.dayofyear.to_numpy(dtype=float)
    h = t.hour.to_numpy(dtype=float)
    w = t.dayofweek.to_numpy(dtype=float)
    rng = np.random.default_rng(int(config["time"]["seed"]))
    # Calendar seasonality, only intended for method development; not climate data.
    ambient = 9.0 - 9.5 * np.cos(2*np.pi*(d-15)/365.0) + 2.1*np.sin(2*np.pi*(h-7)/24)
    ambient += rng.normal(0, 1.25, size=n)
    s = config["source"]
    load = (float(s["mean_it_load_fraction"]) + 0.050*np.sin(2*np.pi*(h-5)/24)
            - 0.035*(w>=5) + rng.normal(0, 0.018, n))
    load = np.clip(load, 0.45, 1.0)
    net = config["network"]
    demand = (float(net["base_demand_mw"]) + float(net["heating_demand_per_degree_mw"])
              * np.maximum(0.0, float(net["heating_balance_temperature_c"])-ambient))
    demand = np.clip(demand, 0, float(net["max_demand_mw"]))
    # Network is weather-compensated: lower supply T when ambient warmer.
    supply = float(net["design_supply_c"]) + float(net["supply_reset_c_per_c"])*(8-ambient)
    supply = np.clip(supply, float(net["min_supply_c"]), float(net["max_supply_c"]))
    source_c = (float(s["source_supply_c"])
                + float(s["source_ambient_sensitivity_c_per_c"])*(ambient-9))
    eco = config["economics"]
    price = (float(eco["electricity_price_mean_eur_per_mwh"])
             + float(eco["electricity_price_variation_eur_per_mwh"])
             *(0.50*np.cos(2*np.pi*(h-18)/24) + 0.35*np.cos(2*np.pi*(d-20)/365))
             + rng.normal(0, 11.0, n))
    # No negative-price modelling in synthetic data; importer accepts them.
    price = np.maximum(price, 5)
    return pd.DataFrame({"time_utc":t,"ambient_c":ambient,"it_load_fraction":load,
                         "district_demand_mw":demand,"district_supply_c":supply,
                         "source_supply_c":source_c,"electricity_eur_mwh":price})
