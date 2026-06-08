import os
import sys
import numpy as np
from pytest import fixture
import aerosandbox as asb

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from src_final.Aircraft.Planform import Planform
from src_final.Aircraft.Fixed import Fixed
from src_final.Drag.Fuselage import Fuselage
from src_final.Drag.Bay import Bay
from src_final.Drag.LandingGear import LandingGear
from src_final.Aircraft.Aircraft import Aircraft
from src_final.global_parameters import Assumptions
from src_final.Requirements.FuelReq import FuelReq
from src_final.Requirements.LGReq import LGReq
from src_final.Requirements.MassReq import MassReq
from src_final.Requirements.MDReq import MDReq
from src_final.Requirements.EmpennageReq import EmpennageReq
from src_final.Requirements.Requirement import Requirement
from src_final.EmpennageSizing.TailFinder import TailFinder
from src_final.EmpennageSizing.CanardFinder import CanardFinder

@fixture
def fixed() -> Fixed:
    assumptions = Assumptions()

    #TODO load the fuselage here
    main_gear_bay = Bay(surface_wetted=np.pi*0.02*0.5, length=0.5, diameter=0.02)
    engine_bay = Bay(surface_wetted=np.pi*0.02*0.5, length=0.5, diameter=0.02)
    main_gear = LandingGear(wheel_width=assumptions.main_gear_width_wheel, exposed_height=0.02, wheel_diameter=0.03, strut_width=0.01)
    nose_gear = LandingGear(wheel_width=assumptions.main_gear_width_wheel, exposed_height=0.02, wheel_diameter=0.03, strut_width=0.01)
    fuselage = Fuselage(surface_wetted=np.pi*0.03*3.4, length_total=3.4, diameter_max=0.03, upsweep=np.pi/12, base_area=np.pi/4*0.007**2)
    fixed = Fixed(mass=25., fuel_mass=10., x_cg_min=1.6, x_cg_max=2., x_tail_cone=2.3, z_cg=0.04, z_tail_cone=0.02, z_wing=0.05, x_LE_canard=0.01,
                x_LE_wing=1.6, x_LE_tail=3.25, x_nose_gear=0.1, x_main_gear=1.8, y_main_gear=0.02, fuselage=fuselage, nose_gear=nose_gear,
                main_gear=main_gear, gear_bay=main_gear_bay, engine_bay=engine_bay)

    for component in fixed.drag_components(False):
        component.add_cache_entry("go_around", assumptions.airspeed_approach/asb.Atmosphere(assumptions.altitude_go_round).speed_of_sound(), assumptions.altitude_go_round)
        component.add_cache_entry("mach_max", assumptions.mach_max, assumptions.altitude_mach_max)
        component.add_cache_entry("cruise", assumptions.mach_cruise, assumptions.altitude_cruise)
    for component in fixed.drag_components(True):
        component.add_cache_entry("takeoff", assumptions.airspeed_approach/asb.Atmosphere().speed_of_sound(), 0.)
        print(component)

    return fixed


@fixture
def main_wing_forward_swept() -> Planform:
    assumptions = Assumptions()

    pf = Planform(
        aspect_ratio=27.,
        span=4.,
        sweep_quarter_deg=-20.,
        taper=1.,
        thickness_to_chord=0.18,
        cm_quarter_chord=-.05,
        wetted_surface_ratio=1.07,
        interference_factor=1.,
        clmax=1.,
        flap=False
    )

    go_around_atmosphere = asb.Atmosphere(assumptions.altitude_go_round)
    sea_level_atmosphere = asb.Atmosphere()
    
    pf.add_cache_entry('cruise', assumptions.mach_cruise, assumptions.altitude_cruise)
    pf.add_cache_entry('mach_max', assumptions.mach_max, assumptions.altitude_mach_max)
    #NOTE: not fully technically correct but prevents coupling which would be problematic, acceptable as CD0 dept. on mach is small @ low mach
    pf.add_cache_entry('go_around', assumptions.airspeed_approach / go_around_atmosphere.speed_of_sound(), assumptions.altitude_go_round)
    pf.add_cache_entry('takeoff', assumptions.airspeed_approach / sea_level_atmosphere.speed_of_sound(), 0.)

    pf.mass_cache = 5.
    pf.x_cg_cache = pf.x_MAC + pf.MAC/3

    assert np.isclose(pf.x_MAC+pf.MAC/4, pf.aerodynamic_center(20))

    return pf


class TestEmpennageSizing():
    def test_tail_forward_sweep(self, fixed:Fixed, main_wing_forward_swept:Planform):
        #Constrained by stability
        pass