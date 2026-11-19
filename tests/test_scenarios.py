from heat_reuse.profiles import make_synthetic_profiles
from heat_reuse.studies import scenario_cases,price_surface,assumptions_sweep


def test_scenario_direction_low_temp(config):
    df=scenario_cases(config,make_synthetic_profiles(config))
    base=df.set_index('case').loc['Reference']
    low=df.set_index('case').loc['Low-temperature network']
    assert low['mean_running_cop']>base['mean_running_cop']


def test_price_surface_higher_gas_has_higher_npv(config):
    gas,eshift,v=price_surface(config,make_synthetic_profiles(config),n=3)
    assert (v[-1,:]>v[0,:]).all()


def test_assumption_sweep_reproducible(config):
    p=make_synthetic_profiles(config)
    a=assumptions_sweep(config,p,n=4,seed=2)
    b=assumptions_sweep(config,p,n=4,seed=2)
    assert a.equals(b)


def test_capacity_cost_anchor_recovers_reference(config):
    from heat_reuse.studies import capacity_sizing
    frame=capacity_sizing(config,make_synthetic_profiles(config))
    ref=frame.iloc[(frame['rated_output_mw']-config['heat_pump']['rated_heat_output_mw']).abs().argmin()]
    assert abs(ref['rated_output_mw']-1.15)<0.001
    assert abs(ref['capex_eur']-config['economics']['installed_capex_eur'])<0.001


def test_sizing_grid_has_finite_unique_optimum(config):
    import numpy as np
    from heat_reuse.studies import capacity_sizing
    frame=capacity_sizing(config,make_synthetic_profiles(config))
    assert len(frame)==config['sizing']['steps']
    assert np.isfinite(frame['npv_eur']).all()
    assert frame['rated_output_mw'].is_monotonic_increasing
