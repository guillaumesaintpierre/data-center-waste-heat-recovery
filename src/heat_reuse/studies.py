"""Controlled scenario changes; each run derives all results from base inputs."""
from __future__ import annotations
from copy import deepcopy
import numpy as np
import pandas as pd
from .simulation import simulate
from .economics import summarize


def scenario_cases(config, raw_profiles):
    specs = [
      ("Reference",0.0,None,None),
      ("Low-temperature network",-12.0,None,None),
      ("High-temperature network",8.0,None,None),
      ("Reduced heat capture",0.0,0.55,None),
      ("Poor heat-pump performance",0.0,None,0.38),
      ("Heat-first dispatch",0.0,None,None),
    ]
    out=[]
    for name,shift,capture,eta in specs:
        cfg=deepcopy(config); p=raw_profiles.copy()
        p["district_supply_c"]+=shift
        if capture is not None:cfg["source"]["recoverable_fraction_of_it_heat"]=capture
        if eta is not None:cfg["heat_pump"]["second_law_efficiency"]=eta
        mode="heat_first" if name=="Heat-first dispatch" else "economic"
        d=simulate(cfg,p,mode)
        result=summarize(d,cfg); result["case"]=name
        out.append(result)
    return pd.DataFrame(out)


def price_surface(config,raw_profiles,gas_range=(35,105),electricity_shift_range=(-35,45),n=15):
    # The x axis is a hypothetical mean price shift, for synthetic OR observed data.
    gas=np.linspace(*gas_range,n); eshift=np.linspace(*electricity_shift_range,n)
    npvs=np.empty((n,n))
    for i,g in enumerate(gas):
        for j,es in enumerate(eshift):
            cfg=deepcopy(config);p=raw_profiles.copy()
            cfg["economics"]["gas_price_eur_per_mwh_fuel"]=float(g)
            p["electricity_eur_mwh"]=p["electricity_eur_mwh"]+es
            # Negative hourly prices are possible and are intentionally retained.
            s=summarize(simulate(cfg,p),cfg)
            npvs[i,j]=s["npv_eur"]
    return gas,eshift,npvs


def assumptions_sweep(config,raw_profiles,n=280,seed=20261117):
    """Range exploration. Independent UNIFORM draws are not empirical priors.

    The resulting fractions must NOT be interpreted as probabilities of
    profitability: ranges have been selected for teaching and have no
    statistical calibration.
    """
    rng=np.random.default_rng(seed)
    result=[]
    for i in range(n):
        c=deepcopy(config);p=raw_profiles.copy()
        c["source"]["recoverable_fraction_of_it_heat"]=float(rng.uniform(.55,.90))
        c["heat_pump"]["second_law_efficiency"]=float(rng.uniform(.37,.60))
        c["economics"]["gas_price_eur_per_mwh_fuel"]=float(rng.uniform(35,110))
        c["economics"]["installed_capex_eur"]=float(rng.uniform(600000,1300000))
        price_shift=float(rng.uniform(-35,45))
        p["electricity_eur_mwh"]+=price_shift
        s=summarize(simulate(c,p),c)
        result.append({"scenario_id":i+1,"capture_fraction":c["source"]["recoverable_fraction_of_it_heat"],
                       "eta_second_law":c["heat_pump"]["second_law_efficiency"],
                       "gas_price_eur_mwh_fuel":c["economics"]["gas_price_eur_per_mwh_fuel"],
                       "electricity_price_shift_eur_mwh":price_shift,
                       "installed_capex_eur":c["economics"]["installed_capex_eur"],
                       "heat_delivered_mwh":s["heat_delivered_mwh"],
                       "npv_eur":s["npv_eur"],"net_co2_t":s["conditional_operational_emissions_avoided_tonnes"]})
    return pd.DataFrame(result)


def capacity_sizing(config, raw_profiles):
    """Discrete sizing screen under an EXPLICITLY ASSUMED linear CAPEX law.

    K(P) = K_fixed + k_var*P; anchored to the reference CAPEX at reference MW.
    No claim of a manufacturer's actual cost curve or continuous global optimum.
    """
    opt=config["sizing"]
    base_mw=float(config["heat_pump"]["rated_heat_output_mw"])
    base_capex=float(config["economics"]["installed_capex_eur"])
    fixed=float(opt["fixed_capex_eur"])
    if not 0<=fixed<base_capex:raise ValueError("Invalid assumed fixed CAPEX")
    slope=(base_capex-fixed)/base_mw
    rows=[]
    for rated in np.linspace(opt["range_min_mw"],opt["range_max_mw"],int(opt["steps"])):
        cfg=deepcopy(config)
        cfg["heat_pump"]["rated_heat_output_mw"]=float(rated)
        cfg["economics"]["installed_capex_eur"]=float(fixed+slope*rated)
        m=summarize(simulate(cfg,raw_profiles),cfg)
        rows.append({"rated_output_mw":rated,
                     "capex_eur":cfg["economics"]["installed_capex_eur"],
                     "heat_delivered_mwh":m["heat_delivered_mwh"],
                     "annual_cashflow_eur":m["annual_incremental_cashflow_eur"],
                     "npv_eur":m["npv_eur"]})
    return pd.DataFrame(rows)
