from copy import deepcopy
import numpy as np
import pandas as pd
import pytest
from heat_reuse.profiles import make_synthetic_profiles
from heat_reuse.simulation import simulate
from heat_reuse.economics import summarize,discounted_npv,break_even_heat_value_eur_mwh


def test_profiles_exactly_one_year(config):
    p=make_synthetic_profiles(config)
    assert len(p)==8760
    assert p['time_utc'].is_unique and p['time_utc'].dt.tz is not None


def test_synthetic_profiles_are_reproducible(config):
    a=make_synthetic_profiles(config);b=make_synthetic_profiles(config)
    pd.testing.assert_frame_equal(a,b)


def test_hourly_first_law(config):
    d=simulate(config,make_synthetic_profiles(config))
    assert np.max(np.abs(d['source_heat_used_mw']+d['compressor_electricity_mw']-d['condenser_heat_mw']))<1e-10
    assert np.max(np.abs(d['condenser_heat_mw']-d['network_loss_mw']-d['district_heat_delivered_mw']))<1e-10


def test_all_constraints(config):
    d=simulate(config,make_synthetic_profiles(config))
    assert (d['district_heat_delivered_mw'] <= d['district_demand_mw']+1e-10).all()
    assert (d['source_heat_used_mw'] <= d['available_source_heat_mw']+1e-10).all()
    assert (d['condenser_heat_mw'] <= config['heat_pump']['rated_heat_output_mw']+1e-10).all()


def test_zero_heat_demand_produces_no_output(config):
    p=make_synthetic_profiles(config).iloc[:24].copy()
    p['district_demand_mw']=0.0
    d=simulate(config,p)
    assert d['condenser_heat_mw'].sum()==0.


def test_zero_it_load_produces_no_output(config):
    p=make_synthetic_profiles(config).iloc[:24].copy()
    p['it_load_fraction']=0.
    assert simulate(config,p)['heat_delivery_mwh'].sum()==0.


def test_extremely_expensive_power_stops_economic_dispatch(config):
    p=make_synthetic_profiles(config).iloc[:24].copy()
    p['electricity_eur_mwh']=10000.
    assert simulate(config,p)['heat_delivery_mwh'].sum()==0.
    assert simulate(config,p,'heat_first')['heat_delivery_mwh'].sum()>0.


def test_negative_spot_price_allowed(config):
    p=make_synthetic_profiles(config).iloc[:24].copy()
    p['electricity_eur_mwh']=-20.
    assert simulate(config,p)['heat_delivery_mwh'].sum()>0.


def test_sensitivity_to_capture_fraction(config):
    p=make_synthetic_profiles(config)
    ref=simulate(config,p,'heat_first')['heat_delivery_mwh'].sum()
    c=deepcopy(config);c['source']['recoverable_fraction_of_it_heat']=0.2
    lower=simulate(c,p,'heat_first')['heat_delivery_mwh'].sum()
    assert lower<ref


def test_technical_only_no_heat_preserves_baseline_gas_supply(config):
    p=make_synthetic_profiles(config).iloc[:24].copy()
    p['district_demand_mw']=0.
    d=simulate(config,p)
    assert summarize(d,config)['heat_delivered_mwh']==0.


def test_emissions_boundaries_and_sign(config):
    d=simulate(config,make_synthetic_profiles(config))
    s=summarize(d,config)
    assert s['conditional_operational_emissions_avoided_tonnes']>0
    c=deepcopy(config);c['economics']['electricity_emission_factor_kg_per_mwh']=3000.
    d2=simulate(c,make_synthetic_profiles(c))
    assert summarize(d2,c)['conditional_operational_emissions_avoided_tonnes']<0


def test_annual_energy_never_creates_free_heat(config):
    d=simulate(config,make_synthetic_profiles(config))
    assert np.isclose(d['heat_delivery_mwh'].sum()+d['network_loss_mw'].sum(),
                      d['source_heat_mwh'].sum()+d['compressor_mwh'].sum(),rtol=1e-12)


def test_duplicate_time_rejected(config):
    p=make_synthetic_profiles(config).iloc[:3].copy()
    p.loc[p.index[1],'time_utc']=p.iloc[0]['time_utc']
    with pytest.raises(ValueError):simulate(config,p)


def test_missing_column_rejected(config):
    p=make_synthetic_profiles(config).iloc[:3].drop(columns=['source_supply_c'])
    with pytest.raises(ValueError):simulate(config,p)


def test_discounted_npv_manual():
    # 2 years at 10%; capex 100; annual return 60.
    assert np.isclose(discounted_npv(60,100,.10,2),-100+60/1.1+60/1.1**2)


def test_break_even_cost_positive():
    assert break_even_heat_value_eur_mwh(100,1500,200,300,1000,.05,15,0.)>20


def test_zero_heat_break_even_infinite():
    assert np.isinf(break_even_heat_value_eur_mwh(0,1500,200,300,1000,.05,15,0.))


def test_economic_dispatch_no_worse_variable_surplus(config):
    p=make_synthetic_profiles(config);p['electricity_eur_mwh']=240.
    d1=simulate(config,p,'economic');d2=simulate(config,p,'heat_first')
    assert d1['hourly_net_savings_eur'].sum()>=d2['hourly_net_savings_eur'].sum()
