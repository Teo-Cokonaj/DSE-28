import pytest
import numpy as np
import aerosandbox as asb
import sys
import os
import numpy.testing as nte
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src_final.Requirements.MassReq import MassReq
from src_final.Aircraft.Aircraft import Aircraft
from src_final.Aircraft.Planform import Planform
from src_final.Aircraft.Fixed import Fixed, Fuselage, Bay, LandingGear
from src_final.global_parameters import Assumptions, CONSTANTS

# Define an MTOW constraint
@pytest.fixture
def mtow_max():
    mtow_max = 50      # [kg]
    return mtow_max

@pytest.fixture
def assumptions():
    return Assumptions()

def constants():
    return CONSTANTS()

@pytest.fixture
def fuselage():
    return Fuselage(surface_wetted=np.pi*0.03*3.4, length_total=3.4, diameter_max=0.03, upsweep=np.pi/12, base_area=np.pi/4*0.007**2)

@pytest.fixture
def engine_bay():
    return Bay(surface_wetted=np.pi*0.02*0.5, length=0.5, diameter=0.02)

@pytest.fixture
def main_gear(assumptions):
    return LandingGear(wheel_width=assumptions.main_gear_width_wheel, exposed_height=0.02, wheel_diameter=0.03, strut_width=0.01)

@pytest.fixture
def nose_gear(assumptions):
    return LandingGear(wheel_width=assumptions.main_gear_width_wheel, exposed_height=0.02, wheel_diameter=0.03, strut_width=0.01)

@pytest.fixture
def fixed(fuselage, nose_gear, main_gear, engine_bay, assumptions):
    fix_no_drag =  Fixed(mass=25., fuel_mass=10., x_cg_min=1.6, x_cg_max=2., x_tail_cone=2.3, z_cg=0.04, z_tail_cone=0.02, z_wing=0.05, x_LE_canard=0.01,
                x_LE_wing=1.6, x_LE_tail=3.25, x_nose_gear=0.1, x_main_gear=1.8, y_main_gear=0.02, fuselage=fuselage, nose_gear=nose_gear,
                main_gear=main_gear, engine_bay=engine_bay)
    
    for component in fix_no_drag.drag_components(False):
        component.add_cache_entry("go_around", assumptions.airspeed_approach/asb.Atmosphere(assumptions.altitude_go_round).speed_of_sound(), assumptions.altitude_go_round)
        component.add_cache_entry("mach_max", assumptions.mach_max, assumptions.altitude_mach_max)
        component.add_cache_entry("cruise", assumptions.mach_cruise, assumptions.altitude_cruise)
    for component in fix_no_drag.drag_components(True):
        component.add_cache_entry("takeoff", assumptions.airspeed_approach/asb.Atmosphere().speed_of_sound(), 0.)
    
    return fix_no_drag

@pytest.fixture
def planform(assumptions):
    planform =  Planform(aspect_ratio=20.0,    span=2.0,    sweep_quarter_deg=0.0,    taper=1.0,    thickness_to_chord=0.12,
            cm_quarter_chord=1.0,    wetted_surface_ratio=1.0,    interference_factor=1.0,    clmax=1.5,    flap=False,)
    planform.add_cache_entry("cruise",assumptions.mach_cruise, assumptions.altitude_cruise)
    planform.add_cache_entry("mach_max", assumptions.mach_max, assumptions.altitude_mach_max)
    planform.add_cache_entry("go_around", assumptions.airspeed_approach/asb.Atmosphere(assumptions.altitude_go_round).speed_of_sound(), assumptions.altitude_go_round)
    planform.add_cache_entry("takeoff", assumptions.airspeed_approach/asb.Atmosphere().speed_of_sound(), 0.)
    planform.mass_cache = 10.  #[kg]
    return planform

@pytest.fixture
def aircraft(fixed, planform):
    return Aircraft(fixed = fixed, planforms = [planform])              

class TestMassReq:
    def test_MassReq(self,
                    aircraft,
                    mtow_max):

        print(f'MTOW HUGO requirement: {mtow_max}')
        print(f'Total HUGO mass: {aircraft.total_mass()}')
        print(f'Total MTOW margin: {mtow_max-aircraft.total_mass()}')

        req = MassReq(mtow_max=mtow_max)

        assert req.assess(aircraft)