"""Regenerate final-report figures from the published 2025 observations.

This script uses ONLY data downloaded from the two named official providers
and existing simulator outputs. It neither downloads data nor creates synthetic
observations. Run from the repository root:
    python scripts/build_final_report_figures.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def read_series(root: Path, year: int = 2025):
    observed = root / 'data' / 'observed'
    electricity_file = observed / f'dk2_prices_{year}.csv'
    weather_file = observed / f'dmi_temperature_{year}.csv'
    meta_file = observed / f'observed_{year}.metadata.json'

    if not all(p.exists() for p in (electricity_file, weather_file, meta_file)):
        raise FileNotFoundError('Historical CSV and provenance metadata missing. '
                                'Run scripts/fetch_real_inputs.py first.')

    metadata = json.loads(meta_file.read_text(encoding='utf-8'))
    if metadata.get('year') != year or metadata.get('electricity_zone') != 'DK2':
        raise ValueError('Observed metadata year or electricity zone mismatch')
    for file in (electricity_file, weather_file):
        actual = hashlib.sha256(file.read_bytes()).hexdigest()
        if metadata['sha256'].get(file.name) != actual:
            raise ValueError(f'SHA-256 mismatch for {file.name}; inspect provenance')

    electric = pd.read_csv(electricity_file)
    weather = pd.read_csv(weather_file)
    expected = pd.date_range(f'{year}-01-01', f'{year+1}-01-01',
                             freq='h', inclusive='left', tz='UTC')
    for label, frame in (('electricity', electric), ('weather', weather)):
        if 'time_utc' not in frame.columns:
            raise ValueError(f'{label} file missing UTC timestamps')
        time = pd.DatetimeIndex(pd.to_datetime(frame['time_utc'], utc=True))
        if not time.equals(expected):
            raise ValueError(f'{label} does not cover exactly the full {year} UTC grid')
        frame.index = time
    price = electric['electricity_eur_mwh'].astype(float)
    temperature = weather['ambient_c'].astype(float)
    if not np.isfinite(price).all() or not np.isfinite(temperature).all():
        raise ValueError('Non-finite historical value')
    if not set(weather['quality'].unique()).issubset({'observed', 'interpolated'}):
        raise ValueError('Missing or unexpected observed-weather quality flags')
    return price, temperature, weather, metadata


def build(root: Path, year: int):
    price, temperature, weather, metadata = read_series(root, year)
    ref = json.loads((root/'results'/'summary.json').read_text(encoding='utf-8'))['metrics']
    obs = json.loads((root/'results'/f'real-{year}'/'summary.json').read_text(encoding='utf-8'))
    if not ('Energinet' in obs.get('provenance', {}).get('price_data','') and
            'DMI' in obs.get('provenance', {}).get('ambient_data','')):
        raise ValueError('Historical summary does not identify both observed input sources')
    actual = obs['metrics']
    if obs['provenance']['weather_imputed_hours'] != int((weather['quality']=='interpolated').sum()):
        raise ValueError('Imputation count does not match the observed summary')

    out = root/'figures'
    out.mkdir(exist_ok=True)
    months = list(range(1,13))
    weather_m = temperature.groupby(temperature.index.month).mean().reindex(months)
    price_m = price.groupby(price.index.month).mean().reindex(months)
    if not weather_m.notna().all() or not price_m.notna().all():
        raise ValueError('Incomplete monthly input coverage')
    label=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    plt.rcParams.update({'font.size': 10, 'font.family':'DejaVu Sans',
                         'axes.spines.top':False, 'axes.spines.right':False})
    fig, axes = plt.subplots(2,1,figsize=(10,6.3),sharex=True,layout='constrained')
    axes[0].plot(months, weather_m.values, 'o-', lw=2, markersize=5, color='#147D92')
    axes[0].set_title('Monthly ambient temperature | DMI station 06180 (Kastrup)',
                      loc='left', fontsize=12, weight='bold')
    axes[0].set_ylabel('Air temperature (°C)')
    axes[0].grid(alpha=.18)
    axes[0].set_ylim(0,22)
    axes[1].plot(months, price_m.values, 'o-', lw=2, markersize=5, color='#B36827')
    axes[1].set_title('Monthly day-ahead wholesale electricity price | Energinet DK2',
                      loc='left', fontsize=12, weight='bold')
    axes[1].set_ylabel('EUR/MWh electricity')
    axes[1].set_xlabel(f'{year} (UTC calendar months)')
    axes[1].grid(alpha=.18)
    axes[1].set_ylim(40,130)
    axes[1].set_xticks(months,label)
    fig.savefig(out/'09_observed_2025_monthly_inputs.png', dpi=180,bbox_inches='tight')
    plt.close(fig)

    fields=[('heat_delivered_mwh','Useful heat\ndelivered'),
            ('heat_demand_coverage','Modelled demand\ncoverage'),
            ('mean_running_cop','Running COP'),
            ('electricity_cost_eur','Annual electricity\ncost'),
            ('npv_eur','NPV (20 yrs)')]
    changes=[100*(actual[k]/ref[k]-1) for k,_ in fields]
    fig,ax=plt.subplots(figsize=(10,3.7),layout='constrained')
    bars=ax.barh(range(len(fields)),changes,
                 color=['#347B8D' if x>=0 else '#D28C43' for x in changes])
    ax.axvline(0,lw=.9,color='#444')
    ax.set_yticks(range(len(fields)),[label for _,label in fields])
    ax.invert_yaxis()
    ax.grid(axis='x',alpha=.2)
    ax.set_axisbelow(True)
    ax.set_xlabel('Relative change from synthetic reference (%)')
    ax.set_title(f'Effect of historical {year} weather / price boundary conditions',
                 loc='left',fontsize=12,weight='bold')
    for rect,change in zip(bars,changes):
        xpos=rect.get_width()
        ax.text(xpos+(0.5 if change>=0 else -0.5),
                rect.get_y()+rect.get_height()/2,f'{change:+.1f}%',
                ha='left' if change>=0 else 'right',va='center',fontsize=10)
    ax.set_xlim(min(changes)-5,max(changes)+6)
    fig.savefig(out/'10_historical_vs_reference.png',dpi=180,bbox_inches='tight')
    plt.close(fig)
    print(f'Validated {len(price)} DK2 market hours and {len(weather)} weather hours; '
          f'{(weather["quality"]=="interpolated").sum()} explicitly interpolated.')
    print('Regenerated figures 09 and 10 from published data and simulation results.')
    print('Observed annual mean DK2 EUR/MWh:',round(float(price.mean()),3))
    print('Observed annual mean air temperature C:',round(float(temperature.mean()),3))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--year',type=int,default=2025)
    args=parser.parse_args()
    build(args.root.resolve(),args.year)

if __name__=='__main__':
    main()
