"""Compare baseline synthetic runs and observed-covariate runs after BOTH exist.

This script does not fetch data and never simulates missing measurements.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd


def read_metrics(path):
    meta=json.loads(Path(path).read_text(encoding='utf-8'))
    return meta['metrics'],meta['provenance']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',default='results/summary.json')
    p.add_argument('--observed',default='results/real-2025/summary.json')
    args=p.parse_args()
    a,pa=read_metrics(args.reference); b,pb=read_metrics(args.observed)
    if pb.get('ambient_data','synthetic')=='synthetic' or pb.get('price_data','synthetic')=='synthetic':
        raise ValueError('Observed scenario must contain both observed price and weather inputs')
    metrics=['heat_demand_mwh','heat_delivered_mwh','mean_running_cop','heat_demand_coverage',
             'electricity_cost_eur','annual_incremental_cashflow_eur','npv_eur',
             'break_even_heat_value_eur_per_mwh']
    df=pd.DataFrame([{'metric':m,'synthetic_reference':a[m],
                      'historical_price_weather__other_assumptions':b[m],
                      'difference':b[m]-a[m]} for m in metrics])
    print(df.to_string(index=False,float_format=lambda x:f'{x:,.3f}'))
    print('\nIMPORTANT: differences are conditional; heat demand and IT demand are still parametric assumptions.')

if __name__=='__main__':main()
