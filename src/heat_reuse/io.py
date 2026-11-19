"""Strictly validated hourly electricity-price data imports."""
from __future__ import annotations
import pandas as pd
import numpy as np


def read_hourly_prices(path, expected_times):
    """Import TimeUTC or time_utc, electricity_eur_mwh; reject missing hours.

    This method intentionally has no forward fill or interpolation. Missing
    market intervals cannot silently become invented observations.
    """
    raw = pd.read_csv(path)
    if set(("time_utc","electricity_eur_mwh")).issubset(raw.columns):
        timecol, valuecol = "time_utc", "electricity_eur_mwh"
    elif set(("TimeUTC","DayAheadPriceEUR")).issubset(raw.columns):
        timecol, valuecol = "TimeUTC", "DayAheadPriceEUR"
    else:
        raise ValueError("Required columns: time_utc,electricity_eur_mwh (or TimeUTC,DayAheadPriceEUR)")
    times = pd.to_datetime(raw[timecol],utc=True)
    values = pd.to_numeric(raw[valuecol],errors="coerce")
    if values.isna().any() or not np.isfinite(values.to_numpy()).all():
        raise ValueError("Observed price data contain missing or nonfinite prices")
    p = pd.Series(values.to_numpy(dtype=float),index=pd.DatetimeIndex(times))
    if p.index.has_duplicates:
        # 15-min observations become exact hour means; monthly duplicate records
        # otherwise require explicit review.
        if not (p.index.minute.isin([0,15,30,45])).all():
            raise ValueError("Unexpected duplicated timestamps")
        if p.index.duplicated().any():
            raise ValueError("Duplicated actual timestamps")
    if (p.index.minute!=0).any():
        counts = p.resample("h").count()
        if not (counts==4).all():
            raise ValueError("15-minute market series has incomplete hours")
        p = p.resample("h").mean()
    expected = pd.DatetimeIndex(pd.to_datetime(expected_times,utc=True))
    if not p.index.equals(expected):
        missing=expected.difference(p.index)
        extra=p.index.difference(expected)
        raise ValueError(f"Observed market series coverage mismatch: {len(missing)} missing, {len(extra)} extra hours")
    return p.to_numpy()


def write_timestamped_csv(frame, path):
    frame.to_csv(path,index=False,float_format="%.7f")
