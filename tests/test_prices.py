import pandas as pd
import numpy as np
import pytest
from heat_reuse.io import read_hourly_prices


def test_prices_exact_utc_hours(tmp_path):
    ix=pd.date_range('2026-01-01',periods=3,freq='h',tz='UTC')
    p=tmp_path/'hourly.csv'
    pd.DataFrame({'time_utc':ix.astype(str),'electricity_eur_mwh':[90,100,-1]}).to_csv(p,index=False)
    assert np.array_equal(read_hourly_prices(p,ix),[90,100,-1])


def test_quarter_hour_to_hourly_mean(tmp_path):
    ix=pd.date_range('2026-01-01',periods=8,freq='15min',tz='UTC')
    p=tmp_path/'quarter.csv'
    pd.DataFrame({'TimeUTC':ix.astype(str),'DayAheadPriceEUR':[1,2,3,4,5,6,7,8]}).to_csv(p,index=False)
    expected=pd.date_range('2026-01-01',periods=2,freq='h',tz='UTC')
    assert np.allclose(read_hourly_prices(p,expected),[2.5,6.5])


def test_reject_gap_in_market_series(tmp_path):
    ix=pd.date_range('2026-01-01',periods=8,freq='15min',tz='UTC').delete(3)
    p=tmp_path/'gap.csv'
    pd.DataFrame({'TimeUTC':ix.astype(str),'DayAheadPriceEUR':np.arange(7)}).to_csv(p,index=False)
    with pytest.raises(ValueError):read_hourly_prices(p,pd.date_range('2026-01-01',periods=2,freq='h',tz='UTC'))


def test_reject_missing_hour(tmp_path):
    ix=pd.date_range('2026-01-01',periods=2,freq='h',tz='UTC')
    p=tmp_path/'miss.csv'
    pd.DataFrame({'time_utc':ix[:1].astype(str),'electricity_eur_mwh':[10.]}).to_csv(p,index=False)
    with pytest.raises(ValueError):read_hourly_prices(p,ix)
