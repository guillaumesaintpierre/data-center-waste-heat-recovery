"""Incremental project comparison against a gas-boiler heat counterfactual."""
from __future__ import annotations
import math
import numpy as np


def discounted_npv(annual_net_eur, capex_eur, discount_rate, years, overhaul_fraction=0., overhaul_year=12):
    if not 0 <= discount_rate < 1 or years < 1 or capex_eur < 0:
        raise ValueError("Invalid discounted cash-flow inputs")
    npv = -capex_eur
    for year in range(1,int(years)+1):
        cash = annual_net_eur - (overhaul_fraction*capex_eur if year == overhaul_year else 0)
        npv += cash/(1+discount_rate)**year
    return float(npv)


def break_even_heat_value_eur_mwh(heat_mwh, elec_cost_eur, variable_cost_eur, fixed_eur,
                                  capex_eur, rate, years, overhaul_fraction):
    if heat_mwh<=0:
        return math.inf
    annuity = sum(1/(1+rate)**t for t in range(1,years+1))
    discounted_repair = (overhaul_fraction*capex_eur/(1+rate)**12) if years>=12 else 0.
    fixed_capital_annuity = (capex_eur+discounted_repair)/annuity
    return float((elec_cost_eur+variable_cost_eur+fixed_eur+fixed_capital_annuity)/heat_mwh)


def summarize(df, config):
    e = config["economics"]
    h = float(df["heat_delivery_mwh"].sum())
    qsource = float(df["source_heat_mwh"].sum())
    wcomp = float(df["compressor_mwh"].sum())
    wpump = float(df["pumping_mwh"].sum())
    avoided_gas_mwh = h/e["boiler_efficiency"]
    baseline_heat_cost = avoided_gas_mwh*e["gas_price_eur_per_mwh_fuel"]
    electric_cost = float(((df["compressor_mwh"]+df["pumping_mwh"])*df["electricity_eur_mwh"]).sum())
    var_cost = h*e["variable_operating_cost_eur_per_mwh_heat"]
    fixed_cost = float(e["fixed_operating_cost_eur_per_year"])
    net = baseline_heat_cost-electric_cost-var_cost-fixed_cost
    capex = float(e["installed_capex_eur"])
    cash_npv = discounted_npv(net,capex,e["real_discount_rate"],e["evaluation_years"],
                              e["year_12_overhaul_fraction_of_capex"])
    avoided_emissions_t = float(df["net_avoided_co2_kg"].sum())/1000.
    # Direct-data-centre energy is not counted as avoided: reused heat is a coproduct.
    return {
        "hours":int(len(df)),"heat_demand_mwh":float(df["district_heat_demand_mwh"].sum()),
        "heat_delivered_mwh":h,"source_heat_used_mwh":qsource,
        "compressor_electricity_mwh":wcomp,"pumping_electricity_mwh":wpump,
        "mean_running_cop":float((df["condenser_heat_mw"].sum()/wcomp) if wcomp>0 else 0),
        "heat_demand_coverage":float(h/df["district_heat_demand_mwh"].sum()) if float(df["district_heat_demand_mwh"].sum())>0 else 0,
        "capacity_factor_rated_heat_output":float(df["condenser_heat_mw"].sum()/e_float(config["heat_pump"]["rated_heat_output_mw"]*len(df)*config["time"]["step_hours"])),
        "baseline_gas_heat_cost_avoided_eur":baseline_heat_cost,
        "electricity_cost_eur":electric_cost,"variable_om_eur":var_cost,"fixed_om_eur":fixed_cost,
        "annual_incremental_cashflow_eur":net,
        "capital_expenditure_eur":capex,
        "simple_payback_years":(capex/net if net>0 else None),
        "npv_eur":cash_npv,
        "break_even_heat_value_eur_per_mwh":break_even_heat_value_eur_mwh(h,electric_cost,var_cost,fixed_cost,
                 capex,e["real_discount_rate"],e["evaluation_years"],e["year_12_overhaul_fraction_of_capex"]),
        "conditional_operational_emissions_avoided_tonnes":avoided_emissions_t,
        "data_provenance":("electricity: "+("Energinet observed" if config.get("profiles",{}).get("observed_electricity_csv") else "synthetic")+"; ambient: "+("DMI observed with QC flags" if config.get("profiles",{}).get("observed_weather_csv") else "synthetic")+"; district heat demand and technology parameters: assumed"),
        "counterfactual":"district heat supplied by natural gas boiler; no heat-recovery infrastructure",
        "note":"Illustrative feasibility study, not a bankable feasibility assessment."
    }


def e_float(x): return float(x)
