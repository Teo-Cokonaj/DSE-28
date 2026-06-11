import os
import sys
import pickle
import numpy as np
from numba import njit
import itertools as itt
import aerosandbox as asb
import pathlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed
from Drag.Fuselage import Fuselage
from Drag.Bay import Bay
from Drag.LandingGear import LandingGear
from Aircraft.Aircraft import Aircraft
from global_parameters import Assumptions
from Requirements.FuelReq import FuelReq
from Requirements.LGReq import LGReq
from Requirements.MassReq import MassReq
from Requirements.MDReq import MDReq
from Requirements.EmpennageReq import EmpennageReq
from Requirements.Requirement import Requirement
from EmpennageSizing.TailFinder import TailFinder
from EmpennageSizing.CanardFinder import CanardFinder
from structural_analysis.iterative_planform_sizing import size_planform, Material

assumptions = Assumptions()

#TODO load the fuselage here
#with open("../notebooks/pickles/fixed_pickle.pcl", "rb") as f:
    #fixed: Fixed = pickle.load(f)

_HERE = pathlib.Path(__file__).parent
pickle_path = _HERE / ".." / "notebooks" / "pickles" / "fixed_pickle.pcl"

with open(pickle_path, "rb") as f:
    fixed: Fixed = pickle.load(f)

for component in fixed.drag_components(False):
    component.add_cache_entry("go_around", assumptions.airspeed_approach/asb.Atmosphere(assumptions.altitude_go_round).speed_of_sound(), assumptions.altitude_go_round)
    component.add_cache_entry("mach_max", assumptions.mach_max, assumptions.altitude_mach_max)
    component.add_cache_entry("cruise", assumptions.mach_cruise, assumptions.altitude_cruise)
for component in fixed.drag_components(True):
    component.add_cache_entry("takeoff", assumptions.airspeed_approach/asb.Atmosphere().speed_of_sound(), 0.)


standard_wing = Planform(aspect_ratio=27, span=2.667, sweep_quarter_deg=15., taper=.5, thickness_to_chord=0.12, cm_quarter_chord=0,
                         wetted_surface_ratio=1.07, interference_factor=1.0, clmax=1.25, flap=False)

material_skin = Material(assumptions.cfrp_density, elastic_modulus=assumptions.cfrp_Young_modulus, 
                         poisson_ratio=assumptions.cfrp_poisson, shear_modulus=assumptions.cfrp_Young_modulus / 2 / (1 + assumptions.cfrp_poisson),
                         yield_strength=assumptions.cfrp_yield_strength, fracture_strength=assumptions.cfrp_yield_strength)

fuselage_diameter = fixed.fuselage.diameter_max
size_planform(planform=standard_wing, thicknesses=assumptions.allowable_thicknesses, fuselage_diameter=fuselage_diameter, material_skin=material_skin, density_core=assumptions.foam_denisty) 


go_around_atmosphere = asb.Atmosphere(assumptions.altitude_go_round)
sea_level_atmosphere = asb.Atmosphere()

standard_wing.add_cache_entry('cruise', assumptions.mach_cruise, assumptions.altitude_cruise)
standard_wing.add_cache_entry('mach_max', assumptions.mach_max, assumptions.altitude_mach_max)
#NOTE: not fully technically correct but prevents coupling which would be problematic, acceptable as CD0 dept. on mach is small @ low mach
standard_wing.add_cache_entry('go_around', assumptions.airspeed_approach / go_around_atmosphere.speed_of_sound(), assumptions.altitude_go_round)
standard_wing.add_cache_entry('takeoff', assumptions.airspeed_approach / sea_level_atmosphere.speed_of_sound(), 0.)

standard_wing.mass_cache = 3.
standard_wing.x_cg_cache = 0.2


tail_ARs = np.arange(0, 1.5, 0.5)

AR_mass_list = []


for AR in tail_ARs:

    tail = TailFinder(fixed, material=material_skin, core_density=assumptions.foam_denisty, thicknesses=assumptions.allowable_thicknesses, 
                  safety_factor=assumptions.structural_safety_factor, AR_h=AR, taper_h=.7, taper_v=.8).find_planforms(standard_wing)

    #print(tail[0].wing_area / standard_wing.wing_area)

    for t in tail:
        t.add_cache_entry('cruise', assumptions.mach_cruise, assumptions.altitude_cruise)
        t.add_cache_entry('mach_max', assumptions.mach_max, assumptions.altitude_mach_max)
    #NOTE: not fully technically correct but prevents coupling which would be problematic, acceptable as CD0 dept. on mach is small @ low mach
        t.add_cache_entry('go_around', assumptions.airspeed_approach / go_around_atmosphere.speed_of_sound(), assumptions.altitude_go_round)
        t.add_cache_entry('takeoff', assumptions.airspeed_approach / sea_level_atmosphere.speed_of_sound(), 0.)


    ac = Aircraft(fixed, [standard_wing] + tail)

    AR_mass_list.append((AR, ac.total_mass))

    print(AR_mass_list)



