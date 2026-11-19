"""Plot actually imported market prices and weather (with visible imputation flags)."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--year',type=int,default=2025)
    parser.add_argument('--indir',default='data/observed')
    parser.add_argument('--out',default='results/real-2025/figures')
    args=parser.parse_args()
    root=Path(args.indir)
    price=pd.read_csv(root/f'dk2_prices_{args.year}.csv',parse_dates=['time_utc']).set_index('time_utc')
    temp=pd.read_csv(root/f'dmi_temperature_{args.year}.csv',parse_dates=['time_utc']).set_index('time_utc')
    if not price.index.equals(temp.index):raise ValueError('Price and weather hours differ')
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    f,axes=plt.subplots(2,1,figsize=(11,6.6),sharex=True)
    price['electricity_eur_mwh'].resample('D').mean().plot(ax=axes[0],lw=.9)
    axes[0].set_title(f'DK2 day-ahead wholesale electricity price, observed {args.year} (daily means)')
    axes[0].set_ylabel('EUR/MWh')
    temp['ambient_c'].resample('D').mean().plot(ax=axes[1],lw=.9)
    axes[1].set_title('DMI station air temperature (daily means; short gaps may be imputed)')
    axes[1].set_ylabel('Degrees C')
    for ax in axes:
        ax.grid(alpha=.15)
        ax.spines[['top','right']].set_visible(False)
    f.tight_layout();f.savefig(out/'00_actual_observed_inputs.png',dpi=170);plt.close(f)
    n=int((temp['quality']=='interpolated').sum())
    print(f"Saved {out/'00_actual_observed_inputs.png'}; DMI interpolated: {n}/{len(temp)} hours")

if __name__=='__main__':main()
