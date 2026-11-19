"""Simple, auditable energy-system relations.

Units: temperatures in degC externally (convert to Kelvin for Carnot),
power in MW, hourly energy in MWh. The reduced-order COP model is not
a refrigerant-cycle simulation and must not be presented as a manufacturer curve.
"""
from __future__ import annotations

import numpy as np


def heating_cop(source_supply_c, district_supply_c, second_law_efficiency=0.50,
                evaporator_approach_k=4.0, condenser_approach_k=3.0,
                minimum=1.2, maximum=9.0):
    """Estimate COP using eta_II * T_cond/(T_cond - T_evap).

    The approaches refer to temperature differences between the external
    heat-transfer fluids and the refrigerant saturation levels. Rejects
    impossible or non-heating configurations rather than masking them.
    """
    src = np.asarray(source_supply_c, dtype=float)
    sink = np.asarray(district_supply_c, dtype=float)
    t_c = src + 273.15 - evaporator_approach_k
    t_h = sink + 273.15 + condenser_approach_k
    delta = t_h - t_c
    if not (0 < second_law_efficiency <= 1):
        raise ValueError("Second-law efficiency must be in (0, 1]")
    if np.any(t_c <= 0) or np.any(delta <= 0):
        raise ValueError("Invalid temperature lift or absolute temperature")
    carnot = t_h / delta
    raw = second_law_efficiency * carnot
    if np.any(raw < minimum):
        raise ValueError("Assumed heat pump performance is below min COP")
    return np.minimum(raw, np.minimum(maximum, carnot))


def heat_pump_output_cap(source_mw, cop, rated_output_mw):
    """Condenser heat limited by available evaporator heat and rated capacity."""
    qsrc = np.asarray(source_mw, dtype=float)
    cop = np.asarray(cop, dtype=float)
    if np.any(qsrc < 0) or np.any(cop <= 1) or rated_output_mw <= 0:
        raise ValueError("Heat source must be nonnegative; COP>1, rated power>0")
    return np.minimum(rated_output_mw, qsrc * cop / (cop - 1.0))


def heat_pump_flows(condenser_heat_mw, cop, delivery_efficiency, pump_fraction):
    """Return Q_source, compressor power, distribution loss, useful heat, pumps.

    Conserves Q_source + compressor_W = Q_condenser = useful + loss.
    Pump electricity is additional purchased electricity and conservatively
    not credited to the heat output; this is documented as a boundary choice.
    """
    q_h = np.asarray(condenser_heat_mw, dtype=float)
    cop = np.asarray(cop, dtype=float)
    if np.any(q_h < 0) or np.any(cop <= 1):
        raise ValueError("Negative thermal power or COP<=1")
    if not (0 < delivery_efficiency <= 1) or pump_fraction < 0:
        raise ValueError("Invalid delivery efficiency/pumping fraction")
    w_comp = q_h / cop
    q_source = q_h - w_comp
    q_loss = q_h * (1 - delivery_efficiency)
    q_useful = q_h - q_loss
    w_pump = pump_fraction * q_h
    return q_source, w_comp, q_loss, q_useful, w_pump
