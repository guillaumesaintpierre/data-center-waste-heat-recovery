import numpy as np
import pytest
from heat_reuse.physics import heating_cop, heat_pump_output_cap, heat_pump_flows


def test_cop_lower_for_hotter_network():
    assert heating_cop(32,80)<heating_cop(32,60)


def test_cop_higher_for_warmer_source():
    assert heating_cop(35,68)>heating_cop(25,68)


def test_cop_not_above_carnot():
    c=heating_cop(30,65,second_law_efficiency=1.,maximum=999)
    assert np.isclose(c,(65+3+273.15)/((65+3)-(30-4)))


def test_invalid_temperature_lift_rejected():
    with pytest.raises(ValueError):heating_cop(80,60)


def test_eta_out_of_range_rejected():
    with pytest.raises(ValueError):heating_cop(30,60,second_law_efficiency=1.2)


def test_source_limited_output():
    cop=4.
    # Qhot=Qsrc*COP/(COP-1) = 0.6*4/3=0.8 MW
    assert np.isclose(heat_pump_output_cap(.6,cop,2.0),.8)


def test_capacity_limited_output():
    assert np.isclose(heat_pump_output_cap(1.0,3.0,1.1),1.1)


def test_zero_source_output():
    assert heat_pump_output_cap(0.,3.,1.0)==0


def test_first_law_and_network():
    qsrc,w,loss,usable,pump=heat_pump_flows(1.,4.,.97,.02)
    assert np.isclose(qsrc,.75)
    assert np.isclose(w,.25)
    assert np.isclose(qsrc+w,usable+loss)
    assert np.isclose(usable,.97)
    assert np.isclose(pump,.02)


def test_negative_condenser_output_rejected():
    with pytest.raises(ValueError):heat_pump_flows(-1,4,.97,.02)


def test_invalid_delivery_efficiency_rejected():
    with pytest.raises(ValueError):heat_pump_flows(1,4,1.05,.02)
