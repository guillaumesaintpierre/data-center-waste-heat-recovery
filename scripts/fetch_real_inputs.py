"""Download and validate observed 2025 DK2 spot prices and DMI station temperatures.

Usage (internet required): python scripts/fetch_real_inputs.py --year 2025
Inputs: official Energinet and DMI open-data REST APIs. No synthetic values are
written by this script. Missing weather station hours can optionally be filled
using clearly labelled bounded linear interpolation, never silently.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, parse_qs, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import sys

import numpy as np
import pandas as pd

BASE_E='https://api.energidataservice.dk/dataset/'
BASE_D='https://opendataapi.dmi.dk/v2/metObs/collections/observation/items'
# New 15-minute settlement began at 2025-10-01 00:00 Europe/Copenhagen
# = 2025-09-30 22:00 UTC (CEST); do NOT cut at midnight UTC.
CUTOVER=pd.Timestamp('2025-09-30T22:00:00Z')


def load_json(url, *, timeout=100):
    """Fetch JSON and include DMI's diagnostic message for invalid requests."""
    req = Request(url, headers={
        'User-Agent': 'EPFL-DTU-student-waste-heat-study/1.0 (academic project)',
        'Accept': 'application/json',
    })
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')[:1600].strip()
        raise RuntimeError(
            f'Data provider returned HTTP {exc.code} for {url}\n'
            f'Provider response: {body or "(empty response)"}'
        ) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f'Could not retrieve provider data from {url}: {exc}') from exc


def with_offset(url, offset):
    """Update pagination offset without changing the other query parameters."""
    parts = urlsplit(url)
    query = parse_qs(parts.query, keep_blank_values=True)
    query['offset'] = [str(offset)]
    return urlunsplit((parts.scheme, parts.netloc, parts.path,
                       urlencode(query, doseq=True, safe=':/,'), parts.fragment))


def parse_eds_records(rows, expected, field_t, field_p):
    if not rows:
        raise ValueError('No market records received')
    frame=pd.DataFrame(rows)
    if not {field_t,field_p}.issubset(frame.columns):
        raise ValueError(f'Unexpected provider schema: need {field_t}, {field_p}; found {frame.columns.tolist()}')
    if 'PriceArea' in frame.columns and (frame['PriceArea']!='DK2').any():
        raise ValueError('Mixed price areas in downloaded DK2 data')
    ts=pd.DatetimeIndex(pd.to_datetime(frame[field_t],utc=True))
    if ts.has_duplicates:
        raise ValueError('Duplicate exact market timestamps')
    values=pd.to_numeric(frame[field_p],errors='coerce')
    if not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError('Missing or infinite market prices')
    p=pd.Series(values.to_numpy(dtype=float),index=ts).sort_index()
    if (p.index.minute!=0).any():
        if not set(p.index.minute).issubset({0,15,30,45}) or (p.index.second!=0).any():
            raise ValueError('Unexpected day-ahead settlement interval')
        # This is NOT an imputation. Each full hour has four genuine quarter-hours.
        p=p.loc[(p.index>=CUTOVER)]
        grouped=p.resample('h')
        counts=grouped.count()
        # Edge hours outside the requested UTC window are discarded below.
        counts=counts.reindex(expected,fill_value=0)
        if (counts!=4).any():
            bad=counts[counts!=4]
            raise ValueError(f'Quarter-hour coverage incomplete: {len(bad)} affected hours; first={bad.index[0]}')
        return grouped.mean().reindex(expected)
    if not p.reindex(expected).notna().all():
        bad=expected.difference(p.index)
        raise ValueError(f'Hourly market coverage incomplete: {len(bad)} missing hours')
    return p.reindex(expected)


def market_urls(year):
    """Get generous market-local calendar bounds and clip to UTC afterwards."""
    interval=pd.date_range(f'{year}-01-01', f'{year+1}-01-01',freq='h',inclusive='left',tz='UTC')
    requests=[]
    part_old=interval[interval<CUTOVER]
    part_new=interval[interval>=CUTOVER]
    if len(part_old):
        q={'start':f'{year-1}-12-31','end':f'{year}-10-02' if len(part_new) else f'{year+1}-01-03',
           'filter':json.dumps({'PriceArea':['DK2']}),'limit':0,'sort':'HourUTC'}
        requests.append(('Elspotprices',BASE_E+'Elspotprices?'+urlencode(q),part_old,'HourUTC','SpotPriceEUR'))
    if len(part_new):
        q={'start':f'{year}-09-30' if len(part_old) else f'{year-1}-12-31','end':f'{year+1}-01-03','filter':json.dumps({'PriceArea':['DK2']}),
           'limit':0,'sort':'TimeUTC'}
        requests.append(('DayAheadPrices',BASE_E+'DayAheadPrices?'+urlencode(q),part_new,'TimeUTC','DayAheadPriceEUR'))
    return requests,interval


def fetch_prices(year, getter=load_json):
    reqs,expected=market_urls(year)
    out=[]; info=[]
    for name,url,part,tc,pc in reqs:
        data=getter(url)
        rows=data.get('records',[])
        # DayAheadPrices may include quarter-hour rows in a period that also includes
        # pre-cutover boundaries; parse_eds_records clips before hourly aggregation.
        series=parse_eds_records(rows,part,tc,pc)
        out.append(series)
        info.append({'dataset':name,'url':url,'records':len(rows),
                     'requested_hour_count':len(part)})
    result=pd.concat(out).sort_index()
    if not result.index.equals(expected) or result.isna().any():
        raise ValueError('Full-year electricity coverage failed after combining provider datasets')
    frame=pd.DataFrame({'time_utc':expected.strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'electricity_eur_mwh':result.to_numpy(dtype=float)})
    return frame,info


def dmi_urls(year, station, window_days=7):
    """Request non-overlapping weekly windows of hourly DMI observations.

    An observation at 01:00 describes the preceding 00:00--01:00 interval.
    For study hours [a,b), request timestamps [a+1h,b], inclusive.
    """
    if not 1 <= window_days <= 31:
        raise ValueError('DMI window_days must be between 1 and 31')
    first = pd.Timestamp(year=year, month=1, day=1, tz='UTC')
    last = pd.Timestamp(year=year + 1, month=1, day=1, tz='UTC')
    out = []
    cursor = first
    while cursor < last:
        stop = min(cursor + pd.Timedelta(days=window_days), last)
        start_observed = cursor + pd.Timedelta('1h')
        end_observed = stop
        query = {
            'stationId': station,
            'parameterId': 'temp_mean_past1h',
            'datetime': (f'{start_observed:%Y-%m-%dT%H:%M:%SZ}/'
                         f'{end_observed:%Y-%m-%dT%H:%M:%SZ}'),
            'limit': 1000,
            'offset': 0,
        }
        # Keep the standard RFC3339 interval slash unescaped. Sort offline.
        url = BASE_D + '?' + urlencode(query, safe=':/,')
        out.append((f'{cursor:%Y-%m-%d}', url))
        cursor = stop
    return out


def dmi_records_for_year(year, station='06180', getter=load_json):
    features = []
    origins = []
    for window, url in dmi_urls(year, station):
        offset = 0
        pages = 0
        while True:
            actual = with_offset(url, offset)
            try:
                data = getter(actual)
            except RuntimeError as exc:
                raise RuntimeError(
                    f'DMI request failed in window beginning {window} '
                    f'for station {station}.\n{exc}'
                ) from exc
            batch = data.get('features', [])
            if not isinstance(batch, list):
                raise ValueError('DMI features must be a list')
            features.extend(batch)
            pages += 1
            next_link = next((link.get('href') for link in data.get('links', [])
                              if link.get('rel') == 'next'), None)
            if next_link:
                if pages >= 30:
                    raise ValueError('DMI unexpectedly returned >30 pages in one window')
                parsed_next = parse_qs(urlsplit(next_link).query)
                next_offset = int(parsed_next.get('offset', [offset + len(batch)])[0])
                if next_offset <= offset:
                    raise ValueError('DMI pagination did not advance')
                offset = next_offset
            elif len(batch) == 1000:
                if pages >= 30:
                    raise ValueError('DMI unexpectedly returned >30 pages in one window')
                offset += len(batch)
            else:
                break
        origins.append({'window_start': window, 'query_url': url, 'pages': pages})
    return features, origins


def parse_dmi_observations(features,year,station='06180',max_gap=3,max_missing_fraction=.01):
    if not features:raise ValueError('No DMI records found for this station/parameter/year')
    df=pd.DataFrame([f.get('properties',{}) for f in features])
    required={'observed','value','parameterId','stationId'}
    if not required.issubset(df.columns):raise ValueError('Unexpected DMI GeoJSON schema')
    if (df['stationId'].astype(str)!=str(station)).any() or (df['parameterId']!='temp_mean_past1h').any():
        raise ValueError('DMI station or parameter differs from requested dataset')
    ts=pd.DatetimeIndex(pd.to_datetime(df['observed'],utc=True)) - pd.Timedelta(hours=1)
    val=pd.to_numeric(df['value'],errors='coerce')
    if ((val<-50)|(val>50)).any() or not np.isfinite(val.to_numpy(dtype=float)).all():
        raise ValueError('DMI observation has missing or implausible Celsius reading')
    s=pd.Series(val.to_numpy(dtype=float),index=ts).sort_index()
    duplicates=int(s.index.duplicated().sum())
    if duplicates:
        # Two different reported values at the same instant require manual review.
        spread=s.groupby(level=0).agg(lambda x:max(x)-min(x))
        if (spread>1e-9).any():
            raise ValueError('Conflicting DMI temperatures at the same timestamp')
        s=s.loc[~s.index.duplicated(keep='first')]
    expected=pd.date_range(f'{year}-01-01',f'{year+1}-01-01',freq='h',inclusive='left',tz='UTC')
    s=s.reindex(expected)
    missing=s.isna()
    nmissing=int(missing.sum())
    if nmissing/len(s)>max_missing_fraction:
        raise ValueError(f'DMI weather gaps exceed {max_missing_fraction:.1%}: {nmissing}/{len(s)} hours')
    if nmissing:
        groups=(missing!=missing.shift(fill_value=False)).cumsum()
        runlens=missing.groupby(groups).sum()
        if (runlens>max_gap).any():
            raise ValueError(f'DMI has weather gap longer than {max_gap} h')
        if missing.iloc[0] or missing.iloc[-1]:
            raise ValueError('Missing DMI observation at a year boundary; no extrapolation')
        s=s.interpolate(method='time',limit=max_gap,limit_area='inside')
        if s.isna().any():raise ValueError('Unable to interpolate gaps within user-approved limit')
    if np.nanmax(np.abs(s.diff().to_numpy(dtype=float)))>12.0:
        raise ValueError('DMI temperature changes more than 12 C in an hour; inspect station quality manually')
    result=pd.DataFrame({'time_utc':expected.strftime('%Y-%m-%dT%H:%M:%SZ'),
                         'ambient_c':s.to_numpy(),
                         'quality':np.where(missing.to_numpy(),'interpolated','observed')})
    return result, {'raw_records':len(features),'duplicate_identical_timestamp_records':duplicates,
                    'observed_hours':len(result)-nmissing,'interpolated_hours':nmissing,
                    'interpolation_method':f'linear in UTC, gap <= {max_gap} hours, no boundary extrapolation',
                    'hourly_jump_threshold_c':12.0, 'raw_metobs_quality_controlled':False}


def save_data(price,weather,price_info,weather_info,origins,outdir,year,station):
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    pf=outdir/f'dk2_prices_{year}.csv';wf=outdir/f'dmi_temperature_{year}.csv'
    # Write only after both API datasets passed all coverage/quality checks.
    price.to_csv(pf,index=False,float_format='%.6f')
    weather.to_csv(wf,index=False,float_format='%.3f')
    metadata={'data_source':'Historical observations, not synthetic',
       'retrieved_utc':datetime.now(timezone.utc).isoformat(),
       'year':year,'electricity_zone':'DK2','weather_station':station,
       'electricity_units':'EUR/MWh; wholesale spot price; excludes grid fees, levies and taxes',
       'weather_units':'degrees Celsius; DMI preceding-hour mean at observed timestamp',
       'time_alignment':'Both series aligned to interval START in UTC',
       'provenance':{'energy':'Energinet, Energi Data Service, CC BY 4.0',
                     'weather':'Danish Meteorological Institute (DMI), CC BY 4.0'},
       'electricity_requests':price_info,'dmi_requests':origins,
       'weather_qa':weather_info,
       'observed_price_min_eur_mwh':float(price['electricity_eur_mwh'].min()),
       'observed_price_max_eur_mwh':float(price['electricity_eur_mwh'].max()),
       'negative_price_hours':int((price['electricity_eur_mwh']<0).sum()),
       'weather_temperature_min_c':float(weather['ambient_c'].min()),
       'weather_temperature_max_c':float(weather['ambient_c'].max()),
       'sha256':{pf.name:hashlib.sha256(pf.read_bytes()).hexdigest(),
                 wf.name:hashlib.sha256(wf.read_bytes()).hexdigest()},
       'notes':['Actual observations are exogenous inputs only.',
                'District heating demand, IT utilisation, capture and equipment economics remain assumptions.',
                'Weather interpolation, when present, is flagged per hour in data CSV.']}
    (outdir/f'observed_{year}.metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    return pf,wf


def main():
    pa=argparse.ArgumentParser(description=__doc__)
    pa.add_argument('--year',type=int,default=2025)
    pa.add_argument('--station',default='06180',help='DMI station: 06180 Kastrup Copenhagen airport')
    pa.add_argument('--out',default='data/observed')
    pa.add_argument('--max-gap-hours',type=int,default=3)
    pa.add_argument('--max-missing-fraction',type=float,default=0.01)
    args=pa.parse_args()
    if args.year>datetime.now(timezone.utc).year:raise ValueError('Cannot fetch future year')
    print('Fetching Energinet day-ahead prices ...',flush=True)
    prices,info=fetch_prices(args.year)
    print('Fetching DMI hourly station observations ...',flush=True)
    features,origins=dmi_records_for_year(args.year,args.station)
    weather,qa=parse_dmi_observations(features,args.year,args.station,args.max_gap_hours,args.max_missing_fraction)
    a,b=save_data(prices,weather,info,qa,origins,args.out,args.year,args.station)
    print(f'Saved {len(prices)} measured electricity-market hours: {a}')
    print(f'Saved {len(weather)} weather hours ({qa["interpolated_hours"]} imputed): {b}')
    print('Provenance and SHA-256 hashes written beside CSVs. No synthetic data fetched.')

if __name__=='__main__':main()
