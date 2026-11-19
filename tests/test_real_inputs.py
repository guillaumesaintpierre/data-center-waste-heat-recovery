"""Tests on constructed fixtures; they DO NOT constitute downloaded 2025 data."""
import json
import numpy as np
import pandas as pd
import pytest
from heat_reuse.observed import read_hourly_weather, build_observed_profiles
from heat_reuse.profiles import make_synthetic_profiles
from heat_reuse.simulation import simulate
from heat_reuse.economics import summarize
from scripts.fetch_real_inputs import (CUTOVER, parse_eds_records, market_urls,
                                       parse_dmi_observations, save_data)


def test_2025_cutover_is_danish_midnight_in_utc():
    assert CUTOVER == pd.Timestamp('2025-09-30T22:00:00Z')
    reqs, expected = market_urls(2025)
    assert len(expected)==8760
    assert len(reqs)==2
    assert reqs[0][2][-1]==pd.Timestamp('2025-09-30T21:00:00Z')
    assert reqs[1][2][0]==CUTOVER
    assert len(reqs[0][2])+len(reqs[1][2])==8760


def test_old_hourly_price_allows_negative():
    ix=pd.date_range('2025-05-01',periods=3,freq='h',tz='UTC')
    rows=[{'HourUTC':t.isoformat(),'SpotPriceEUR':v,'PriceArea':'DK2'}
          for t,v in zip(ix,[3,-90,101])]
    s=parse_eds_records(rows,ix,'HourUTC','SpotPriceEUR')
    assert list(s)==[3,-90,101]


def test_transition_15min_to_hourly_and_strict_count():
    ix=pd.date_range(CUTOVER,periods=8,freq='15min',tz='UTC')
    rows=[{'TimeUTC':t.isoformat(),'DayAheadPriceEUR':v,'PriceArea':'DK2'}
          for t,v in zip(ix,[100,120,80,100, 1,5,9,13])]
    target=pd.date_range(CUTOVER,periods=2,freq='h',tz='UTC')
    s=parse_eds_records(rows,target,'TimeUTC','DayAheadPriceEUR')
    np.testing.assert_array_equal(s.to_numpy(),[100.,7.])
    with pytest.raises(ValueError, match='coverage incomplete'):
        parse_eds_records(rows[:-1],target,'TimeUTC','DayAheadPriceEUR')


def test_market_mismatched_area_and_duplicate_rejected():
    ix=pd.date_range('2025-05-01',periods=2,freq='h',tz='UTC')
    row={'HourUTC':ix[0].isoformat(),'SpotPriceEUR':0,'PriceArea':'DK2'}
    with pytest.raises(ValueError,match='Duplicate'):
        parse_eds_records([row,row],ix,'HourUTC','SpotPriceEUR')
    with pytest.raises(ValueError,match='Mixed'):
        parse_eds_records([{**row,'PriceArea':'DK1'}],ix[:1],'HourUTC','SpotPriceEUR')


def feature(obs,val,station='06180'):
    return {'properties':{'observed':obs,'value':val,'stationId':station,'parameterId':'temp_mean_past1h'}}


def test_dmi_prior_hour_alignment_and_gap_flags():
    # For full-year data, leave exactly one interior missing hour (2025-01-01 01 UTC).
    ix=pd.date_range('2025-01-01', '2026-01-01',freq='h',inclusive='left',tz='UTC')
    items=[feature((t+pd.Timedelta(hours=1)).isoformat(),float(np.sin(i/24.)))
           for i,t in enumerate(ix) if i!=1]
    out,meta=parse_dmi_observations(items,2025)
    assert len(out)==8760
    assert out.loc[0,'time_utc']=='2025-01-01T00:00:00Z'
    assert out.loc[1,'quality']=='interpolated'
    assert out.loc[1,'ambient_c']==pytest.approx((np.sin(0.)+np.sin(2/24.))/2)
    assert meta['interpolated_hours']==1


def test_dmi_interpolation_maximum_gap_enforced():
    ix=pd.date_range('2025-01-01','2026-01-01',freq='h',inclusive='left',tz='UTC')
    items=[feature((t+pd.Timedelta(hours=1)).isoformat(),5.)
          for i,t in enumerate(ix) if i not in range(100,105)]
    with pytest.raises(ValueError, match='gap longer'):
        parse_dmi_observations(items,2025,max_gap=3)


def test_dmi_weather_reader_strict_indices(tmp_path):
    ix=pd.date_range('2025-01-01',periods=3,freq='h',tz='UTC')
    path=tmp_path/'weather.csv'
    pd.DataFrame({'time_utc':ix,'ambient_c':[0.,1.,-2.],
                  'quality':['observed','interpolated','observed']}).to_csv(path,index=False)
    temp,flags,n=read_hourly_weather(path,ix)
    assert n==1 and flags[1]=='interpolated' and temp[2]==-2.
    with pytest.raises(ValueError,match='coverage mismatch'):
        read_hourly_weather(path,ix[:2])


def test_real_weather_changes_demand_and_supply_not_it_load(tmp_path):
    cfg=json.loads(open('config.json').read())
    p=make_synthetic_profiles(cfg)
    ix=p['time_utc']; n=len(p)
    w=tmp_path/'w.csv'; e=tmp_path/'e.csv'
    pd.DataFrame({'time_utc':ix,'ambient_c':np.full(n,-4),
                  'quality':['observed']*n}).to_csv(w,index=False)
    pd.DataFrame({'time_utc':ix,'electricity_eur_mwh':np.full(n,120.)}).to_csv(e,index=False)
    cfg['profiles']['observed_weather_csv']=str(w)
    cfg['profiles']['observed_electricity_csv']=str(e)
    new,meta=build_observed_profiles(cfg,p)
    assert np.allclose(new['ambient_c'],-4)
    assert np.allclose(new['electricity_eur_mwh'],120)
    np.testing.assert_array_equal(new['it_load_fraction'],p['it_load_fraction'])
    assert not np.allclose(new['district_demand_mw'],p['district_demand_mw'])
    assert not np.allclose(new['district_supply_c'],p['district_supply_c'])
    result=simulate(cfg,new); summary=summarize(result,cfg)
    assert summary['hours']==8760
    assert meta['weather_imputed_hours']==0


def test_partial_real_inputs_fail_hard(tmp_path):
    cfg=json.loads(open('config.json').read())
    cfg['profiles']['observed_weather_csv']=str(tmp_path/'nonexistent.csv')
    with pytest.raises(FileNotFoundError):
        build_observed_profiles(cfg,make_synthetic_profiles(cfg))


def test_2026_all_new_settlement_year_starts_in_january():
    reqs,ix=market_urls(2026)
    assert len(reqs)==1 and reqs[0][0]=='DayAheadPrices'
    assert '2025-12-31' in reqs[0][1]
    assert len(ix)==8760


def test_dmi_conflicting_repeated_measurements_rejected():
    items=[feature('2025-01-01T01:00:00Z',0.),feature('2025-01-01T01:00:00Z',2.)]
    with pytest.raises(ValueError,match='Conflicting'):
        parse_dmi_observations(items,2025)


def test_dmi_weather_spike_requires_review():
    ix=pd.date_range('2025-01-01','2026-01-01',freq='h',inclusive='left',tz='UTC')
    items=[feature((t+pd.Timedelta(hours=1)).isoformat(),18. if i==100 else 0.) for i,t in enumerate(ix)]
    with pytest.raises(ValueError,match='12 C'):
        parse_dmi_observations(items,2025)

def test_dmi_week_windows_cover_exactly_8760_observation_hours():
    from urllib.parse import urlsplit, parse_qs
    from scripts.fetch_real_inputs import dmi_urls
    urls = dmi_urls(2025, '06180')
    assert len(urls) == 53
    observations = []
    for name, url in urls:
        qs = parse_qs(urlsplit(url).query)
        assert qs['stationId'] == ['06180']
        assert 'sortorder' not in qs
        assert qs['parameterId'] == ['temp_mean_past1h']
        start, end = qs['datetime'][0].split('/')
        observations.extend(pd.date_range(start, end, freq='h', tz='UTC'))
    expected = pd.date_range('2025-01-01T01:00:00Z',
                             '2026-01-01T00:00:00Z', freq='h')
    assert len(observations) == 8760
    assert pd.DatetimeIndex(observations).equals(expected)


def test_dmi_weekly_mocked_fetch_and_coverage():
    from urllib.parse import urlsplit, parse_qs
    from scripts.fetch_real_inputs import dmi_records_for_year
    def fake_getter(url):
        qs = parse_qs(urlsplit(url).query)
        start, end = qs['datetime'][0].split('/')
        return {'features': [feature(t.isoformat(), 10.)
                             for t in pd.date_range(start, end, freq='h', tz='UTC')],
                'links': []}
    records, origins = dmi_records_for_year(2025, getter=fake_getter)
    assert len(records) == 8760
    assert len(origins) == 53
    frame, meta = parse_dmi_observations(records, 2025)
    assert len(frame) == 8760
    assert meta['interpolated_hours'] == 0


def test_dmi_http_error_reports_provider_message(monkeypatch):
    import io
    from urllib.error import HTTPError
    import scripts.fetch_real_inputs as module
    def fake_urlopen(request, timeout=100):
        raise HTTPError('https://example.org/api', 400, 'Bad Request', {},
                        io.BytesIO(b'{"message":"invalid query parameter"}'))
    monkeypatch.setattr(module, 'urlopen', fake_urlopen)
    with pytest.raises(RuntimeError, match='invalid query parameter'):
        module.load_json('https://example.org/api')
