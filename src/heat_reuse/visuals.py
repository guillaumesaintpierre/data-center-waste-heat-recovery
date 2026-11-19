"""Figures created directly from the model outputs; no manual edits."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def setup():
    plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False,
        "axes.grid":True,"grid.alpha":0.17,"savefig.dpi":200})


def save(fig,path):
    fig.tight_layout()
    fig.savefig(path,bbox_inches="tight")
    plt.close(fig)


def figures(df, cases, surface, sweep, sizing, directory):
    setup(); out=Path(directory);out.mkdir(parents=True,exist_ok=True)
    monthly=df.set_index("time_utc")[['district_heat_demand_mwh','heat_delivery_mwh']].resample('MS').sum()
    fig,ax=plt.subplots(figsize=(9,3.8));x=np.arange(len(monthly))
    ax.bar(x-.19,monthly['district_heat_demand_mwh'],width=.38,label='Modelled district heat demand')
    ax.bar(x+.19,monthly['heat_delivery_mwh'],width=.38,label='Recovered heat delivered')
    ax.set_xticks(x,monthly.index.strftime('%b'));ax.set_ylabel('Thermal energy [MWh/month]')
    ax.set_title('Demand matching is the main seasonal constraint');ax.legend(frameon=False)
    save(fig,out/'01_monthly_heat_balance.png')

    # UTC deliberately, not local clock time; avoids DST ambiguity.
    year=int(pd.Timestamp(df['time_utc'].iloc[0]).year)
    d=df.set_index('time_utc').loc[f'{year}-01-13':f'{year}-01-19']
    fig,ax=plt.subplots(figsize=(9,3.8))
    ax.plot(d.index,d['district_demand_mw'],label='Heat demand',lw=1.7)
    ax.plot(d.index,d['district_heat_delivered_mw'],label='Recovered heat delivered',lw=1.7)
    ax.plot(d.index,d['available_source_heat_mw'],label='Heat available at source',lw=1,ls='--')
    ax.set_ylabel('Thermal power [MW]');ax.set_title('Winter week (heat-demand model, weather input as documented)')
    ax.legend(frameon=False,ncol=3,loc='upper center');fig.autofmt_xdate()
    save(fig,out/'02_winter_week.png')

    g,e,values=surface
    fig,ax=plt.subplots(figsize=(7.5,4.5))
    im=ax.imshow(values/1e6,origin='lower',aspect='auto',cmap='RdBu',
       extent=(e[0]+df['electricity_eur_mwh'].mean(),e[-1]+df['electricity_eur_mwh'].mean(),g[0],g[-1]))
    ax.contour(e+df['electricity_eur_mwh'].mean(),g,values/1e6,levels=[0],colors='black',linewidths=1)
    ax.set_xlabel('Mean electricity price with scenario shift [EUR/MWh]')
    ax.set_ylabel('Gas price [EUR/MWh of fuel]')
    ax.set_title('Investment NPV under two uncertain energy-price assumptions')
    fig.colorbar(im,ax=ax,label='Net present value [million EUR]')
    save(fig,out/'03_economic_breakeven.png')

    fig,ax=plt.subplots(figsize=(9,3.5))
    c=cases.set_index('case')
    ax.barh(c.index,c['heat_delivered_mwh']/1000)
    ax.invert_yaxis();ax.set_xlabel('Useful district heat [GWh/year]')
    ax.set_title('Technical scenario comparison');save(fig,out/'04_technical_cases.png')

    fig,ax=plt.subplots(figsize=(9,3.6))
    ax.scatter(sweep['heat_delivered_mwh']/1000,sweep['npv_eur']/1e6,
               s=12,alpha=.52)
    ax.axhline(0,ls='--',lw=1,color='black')
    ax.set_xlabel('Useful heat delivered [GWh/year]')
    ax.set_ylabel('20-year project NPV [million EUR]')
    ax.set_title('Exploratory parameter-space scan (NOT a probabilistic forecast)')
    save(fig,out/'05_parameter_space.png')

    fig,ax=plt.subplots(figsize=(8.5,3.8))
    ax.plot(sizing['rated_output_mw'],sizing['npv_eur']/1e6,marker='o',markersize=3,lw=1.4)
    best=sizing.loc[sizing['npv_eur'].idxmax()]
    ax.scatter([best['rated_output_mw']],[best['npv_eur']/1e6],s=75,marker='*',zorder=5)
    ax.axvline(best['rated_output_mw'],ls='--',lw=1)
    ax.set_xlabel('Heat-pump condenser nameplate [MW thermal]')
    ax.set_ylabel('Discounted NPV [million EUR]')
    ax.set_title('Illustrative equipment sizing under an assumed CAPEX scaling')
    save(fig,out/'08_capacity_sizing.png')

    run=df[df['condenser_heat_mw']>0]
    fig,ax=plt.subplots(figsize=(7.5,4.0))
    hb=ax.hexbin(run['district_supply_c']-run['source_supply_c'],run['cop'],
              gridsize=26,mincnt=1,cmap='viridis')
    fig.colorbar(hb,ax=ax,label='Operating hours per bin')
    ax.set_xlabel('External temperature lift [K]')
    ax.set_ylabel('Estimated heating COP [-]')
    ax.set_title('Heat pump efficiency depends on temperature lift')
    save(fig,out/'06_cop_temperature_lift.png')

    fig,ax=plt.subplots(figsize=(9,3.6))
    annual=df[['source_heat_mwh','compressor_mwh','pumping_mwh','heat_delivery_mwh']].sum()
    ax.bar([0],annual['source_heat_mwh'],label='Extracted source heat')
    ax.bar([0],annual['compressor_mwh'],bottom=annual['source_heat_mwh'],label='Compressor electricity')
    ax.bar([1],annual['heat_delivery_mwh'],label='Useful heat delivered')
    loss=(annual['source_heat_mwh']+annual['compressor_mwh']-annual['heat_delivery_mwh'])
    ax.bar([1],loss,bottom=annual['heat_delivery_mwh'],label='Network losses')
    ax.set_xticks([0,1],['Heat pump input','Condenser output']);ax.set_ylabel('Annual energy [MWh]')
    ax.set_title('First-law bookkeeping (pumping power outside thermal boundary)')
    ax.legend(frameon=False,ncol=2,loc='upper center');save(fig,out/'07_first_law.png')
