import aerosandbox as asb
import aerosandbox.numpy as np
import os
import sys
import typing as ty

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.MatchingDiagram.MatchingDiagram import MatchingDiagram
from src.MatchingDiagram.ThrustLapse import ThrustLapse
from src.global_parameters import CONSTANTS

class MatchingDiagramJet(MatchingDiagram):
    def __init__(self, approach_speed:float, CL_max:float, landing_field_length:float, cruise_speed_constraints:list[dict[str, float]], climb_gradient_constraints:list[dict[str, float]]):
        wing_loading_constraints:dict[str, float] = list()
        thrust_weight_constraints:dict[str, ty.Callable[[float]], float] = list()

        stall_speed = approach_speed/1.3
        wing_loading_constraints["Approach speed"] = CONSTANTS.AIR_DENSITY_SEA_LEVEL/2 * stall_speed**2 * CL_max
        wing_loading_constraints["Landing length"] = CONSTANTS.AIR_DENSITY_SEA_LEVEL/2 * landing_field_length/.6 * CL_max

        for cruise_speed_constraint in cruise_speed_constraints:
            atmosphere_cruise = asb.Atmosphere(cruise_speed_constraint["altitude"])
            atmospheric_coefficient = atmosphere_cruise.speed_of_sound()**2 * atmosphere_cruise.density()/2
            mach = cruise_speed_constraint["mach"]
            cruise_condition_term = atmospheric_coefficient*mach**2

            CD0 = cruise_speed_constraint["CD0"]
            inviscid_ratio = cruise_speed_constraint["inviscid_ratio"]

            thrust_lapse = ThrustLapse(cruise_speed_constraint["altitude"])
            lapse = thrust_lapse.thrust_lapse(mach)

            thrust_weight_constraints.append(lambda wing_laoding: (CD0*cruise_condition_term/wing_laoding + wing_laoding/inviscid_ratio/cruise_condition_term) / lapse)

        for climb_gradient_constraint in climb_gradient_constraints:
            sin_gradient = np.sin(np.arctan(climb_gradient_constraint["gradient"]))
            CD0 = cruise_speed_constraint["CD0"]
            inviscid_ratio = cruise_speed_constraint["inviscid_ratio"]
            engine_inoperative_coefficient = 1 if (cruise_speed_constraint["n_engines_if_inoperative"] is None) else 1 + 1/(cruise_speed_constraint["n_engines_if_inoperative"]-1)
