"""Hourly first-law model and financially motivated heat dispatch."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .physics import heating_cop, heat_pump_output_cap, heat_pump_flows

REQUIRED_COLUMNS = ("time_utc", "it_load_fraction", "district_demand_mw", "district_supply_c",
                    "source_supply_c", "electricity_eur_mwh")


def simulate(config, profiles:pd.DataFrame, mode=None):
    p = profiles.copy()
    missing = set(REQUIRED_COLUMNS) - set(p.columns)
    if missing:
        raise ValueError(f"Missing profile columns: {sorted(missing)}")
    if p.empty or p["time_utc"].duplicated().any() or not p["time_utc"].is_monotonic_increasing:
        raise ValueError("Time index must be nonempty, unique and sorted")
    for col in REQUIRED_COLUMNS[1:]:
        if not np.isfinite(p[col].to_numpy(dtype=float)).all():
            raise ValueError(f"Non-finite profile values: {col}")
    if (p["it_load_fraction"].lt(0).any() or p["it_load_fraction"].gt(1).any()
        or p["district_demand_mw"].lt(0).any()):
        raise ValueError("Invalid IT load or negative heat demand")
    dt = float(config["time"]["step_hours"])
    if dt <= 0:
        raise ValueError("Time step must be strictly positive")
    s, hp, network, eco = (config[k] for k in ("source","heat_pump","network","economics"))
    if not (0 <= s["recoverable_fraction_of_it_heat"] <= 1):
        raise ValueError("Recoverable fraction outside [0, 1]")
    if not (0 < eco["boiler_efficiency"] <= 1):
        raise ValueError("Boiler efficiency outside (0, 1]")
    if eco["installed_capex_eur"] < 0 or eco["fixed_operating_cost_eur_per_year"] < 0:
        raise ValueError("Invalid project costs")
    p["it_mw"] = float(s["installed_it_mw"])*p["it_load_fraction"]
    p["facility_electricity_mw_ref"] = p["it_mw"]*float(s["pue_reference"])
    p["available_source_heat_mw"] = p["it_mw"]*float(s["recoverable_fraction_of_it_heat"])
    cop = heating_cop(p["source_supply_c"],p["district_supply_c"],
        second_law_efficiency=hp["second_law_efficiency"],
        evaporator_approach_k=s["evaporator_approach_k"],
        condenser_approach_k=hp["condenser_approach_k"],
        minimum=hp["min_cop"],maximum=hp["max_cop"])
    p["cop"] = cop
    available_condenser = heat_pump_output_cap(p["available_source_heat_mw"],cop,hp["rated_heat_output_mw"])
    p["condenser_heat_potential_mw"] = np.minimum(available_condenser,
                     p["district_demand_mw"]/hp["delivery_efficiency"])
    # Economic dispatch compares marginal avoided-boiler cost with incremental
    # electricity and variable O&M. At no storage, each hour is independent.
    unit_cost = ((p["electricity_eur_mwh"]*(1/p["cop"]+hp["circulation_electricity_fraction_of_heat_output"])
                  +eco["variable_operating_cost_eur_per_mwh_heat"]*hp["delivery_efficiency"])
                  /hp["delivery_efficiency"])
    unit_value = float(eco["gas_price_eur_per_mwh_fuel"])/eco["boiler_efficiency"]
    operating_mode = mode or config["dispatch"]["mode"]
    if operating_mode == "economic":
        operate = unit_value > unit_cost
    elif operating_mode == "heat_first":
        operate = np.ones(len(p),dtype=bool)
    else:
        raise ValueError("Dispatch mode must be economic or heat_first")
    q_heat = np.where(operate,p["condenser_heat_potential_mw"].to_numpy(),0.)
    qsrc,w_comp,loss,q_useful,w_pump = heat_pump_flows(q_heat,cop,
           hp["delivery_efficiency"],hp["circulation_electricity_fraction_of_heat_output"])
    p["source_heat_used_mw"] = qsrc
    p["compressor_electricity_mw"] = w_comp
    p["network_loss_mw"] = loss
    p["condenser_heat_mw"] = q_heat
    p["district_heat_delivered_mw"] = q_useful
    p["pumping_electricity_mw"] = w_pump
    p["additional_electricity_mw"] = w_comp+w_pump
    p["unmet_heat_mw"] = p["district_demand_mw"]-q_useful
    p["hourly_net_savings_eur"] = (q_useful*unit_value -
             (w_comp+w_pump)*p["electricity_eur_mwh"] -
             q_useful*eco["variable_operating_cost_eur_per_mwh_heat"])*dt
    p["heat_delivery_mwh"] = p["district_heat_delivered_mw"]*dt
    p["district_heat_demand_mwh"] = p["district_demand_mw"]*dt
    p["compressor_mwh"] = p["compressor_electricity_mw"]*dt
    p["pumping_mwh"] = p["pumping_electricity_mw"]*dt
    p["source_heat_mwh"] = p["source_heat_used_mw"]*dt
    p["facility_electricity_mwh_ref"] = p["facility_electricity_mw_ref"]*dt
    p["avoided_gas_mwh_fuel"] = p["heat_delivery_mwh"]/eco["boiler_efficiency"]
    p["avoided_gas_co2_kg"] = p["avoided_gas_mwh_fuel"]*eco["gas_emission_factor_kg_per_mwh_fuel"]
    p["extra_electricity_co2_kg"] = (p["compressor_mwh"]+p["pumping_mwh"])*eco["electricity_emission_factor_kg_per_mwh"]
    p["net_avoided_co2_kg"] = p["avoided_gas_co2_kg"]-p["extra_electricity_co2_kg"]
    # Check balances at EVERY simulated time step; fail loudly if violated.
    first_law = p["source_heat_used_mw"]+p["compressor_electricity_mw"]-p["condenser_heat_mw"]
    distribution = p["condenser_heat_mw"]-p["network_loss_mw"]-p["district_heat_delivered_mw"]
    if max(float(first_law.abs().max()),float(distribution.abs().max()))>1e-9:
        raise AssertionError("Energy conservation violated")
    if (p["source_heat_used_mw"] > p["available_source_heat_mw"]+1e-9).any():
        raise AssertionError("Source heat use exceeds available heat")
    if (p["condenser_heat_mw"] > hp["rated_heat_output_mw"]+1e-9).any():
        raise AssertionError("Heat-pump nameplate capacity exceeded")
    if (p["district_heat_delivered_mw"] > p["district_demand_mw"]+1e-9).any():
        raise AssertionError("Demand exceeded")
    return p
