import os
import sys
import pickle
import numpy as np
from numba import njit
import itertools as itt
import aerosandbox as asb

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

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


assumptions = Assumptions()

#TODO load the fuselage here
with open("pickles/fixed_pickle.pcl", "rb") as f:
    fixed:Fixed = pickle.load(f)

for component in fixed.drag_components(False):
    component.add_cache_entry("go_around", assumptions.airspeed_approach/asb.Atmosphere(assumptions.altitude_go_round).speed_of_sound(), assumptions.altitude_go_round)
    component.add_cache_entry("mach_max", assumptions.mach_max, assumptions.altitude_mach_max)
    component.add_cache_entry("cruise", assumptions.mach_cruise, assumptions.altitude_cruise)
for component in fixed.drag_components(True):
    component.add_cache_entry("takeoff", assumptions.airspeed_approach/asb.Atmosphere().speed_of_sound(), 0.)


standard_wing = Planform(aspect_ratio=27, span=2.667, sweep_quarter_deg=15., taper=.5, thickness_to_chord=0.12, cm_quarter_chord=0,
                         wetted_surface_ratio=1.07, interference_factor=1.0, clmax=1.25, flap=False)


go_around_atmosphere = asb.Atmosphere(assumptions.altitude_go_round)
sea_level_atmosphere = asb.Atmosphere()

standard_wing.add_cache_entry('cruise', assumptions.mach_cruise, assumptions.altitude_cruise)
standard_wing.add_cache_entry('mach_max', assumptions.mach_max, assumptions.altitude_mach_max)
#NOTE: not fully technically correct but prevents coupling which would be problematic, acceptable as CD0 dept. on mach is small @ low mach
standard_wing.add_cache_entry('go_around', assumptions.airspeed_approach / go_around_atmosphere.speed_of_sound(), assumptions.altitude_go_round)
standard_wing.add_cache_entry('takeoff', assumptions.airspeed_approach / sea_level_atmosphere.speed_of_sound(), 0.)

standard_wing.mass_cache = 3.
standard_wing.x_cg_cache = 0.2

tail = TailFinder(fixed, 7, .7, .8).find_planforms(standard_wing)

print(tail[0].wing_area / standard_wing.wing_area)

for t in tail:
    t.add_cache_entry('cruise', assumptions.mach_cruise, assumptions.altitude_cruise)
    t.add_cache_entry('mach_max', assumptions.mach_max, assumptions.altitude_mach_max)
#NOTE: not fully technically correct but prevents coupling which would be problematic, acceptable as CD0 dept. on mach is small @ low mach
    t.add_cache_entry('go_around', assumptions.airspeed_approach / go_around_atmosphere.speed_of_sound(), assumptions.altitude_go_round)
    t.add_cache_entry('takeoff', assumptions.airspeed_approach / sea_level_atmosphere.speed_of_sound(), 0.)


ac = Aircraft(fixed, [standard_wing] + tail)