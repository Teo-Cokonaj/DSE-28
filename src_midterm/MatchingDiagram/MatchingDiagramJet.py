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
    def __init__(self, n_engines:float, bypass:float=0., resolution:int=100):
        super().__init__({}, {}, resolution)
        self.engine_inoperative_coefficient = n_engines / (n_engines - 1)
        self.bypass = bypass


    def add_approach_speed(self, constraint_label:str, approach_speed:float, CL_max:float, atmosphere:asb.Atmosphere=asb.Atmosphere(), beta:float=1.):
        stall_speed = approach_speed/1.3
        self.constraints_wing_loading[constraint_label] = atmosphere.density()/2 * stall_speed**2 * CL_max/beta

    
    def add_landing_field_length(self, constraint_label:str, field_length:float, CL_max:float, atmosphere:asb.Atmosphere=asb.Atmosphere(), beta:float=1.):
        self.constraints_wing_loading[constraint_label] = atmosphere.density()/2 * field_length/.6 * CL_max/beta


    def add_cruise_speed(self, constraint_label:str, mach:float, CD0:float, inviscid_ratio:float, atmosphere:asb.Atmosphere=asb.Atmosphere(), beta:float=1.):
            thrust_lapse_cruise = ThrustLapse(atmosphere)
            lapse_cruise = thrust_lapse_cruise.thrust_lapse(mach, self.bypass)

            cruise_condition_term = atmosphere.speed_of_sound()**2 * atmosphere.density()/2 * mach**2

            self.constraints_thrust_weight[constraint_label] = lambda wing_laoding: (CD0 * cruise_condition_term / wing_laoding + wing_laoding / inviscid_ratio / cruise_condition_term) / lapse_cruise * beta
      
        
    def add_climb_gradient(self, constraint_label:str, tan_gradient:float, CD0:float, inviscid_ratio:float, all_engines_operative:bool, atmosphere:asb.Atmosphere=asb.Atmosphere(), beta:float=1.): 
        denisty = atmosphere.density()
        speed_of_sound = atmosphere.speed_of_sound()
        thrust_lapse = ThrustLapse(atmosphere)

        sin_gradient = np.sin(np.arctan(tan_gradient))
        CL_optimal = np.sqrt(CD0*inviscid_ratio) 
        engine_coefficient =  1 if all_engines_operative else self.engine_inoperative_coefficient
        numerator = (2 * np.sqrt(CD0 / inviscid_ratio) + sin_gradient) * engine_coefficient * beta

        mach_from_wing_loading = lambda wing_loading: np.sqrt(wing_loading * 2/denisty / CL_optimal) / speed_of_sound

        self.constraints_thrust_weight[constraint_label] = lambda wing_loading: numerator / thrust_lapse.thrust_lapse(mach_from_wing_loading(wing_loading), self.bypass)


    def add_takeoff_field_length(self, constraint_label:str, field_length:float, inviscid_ratio:float, CL_takeoff:float, atmosphere:asb.Atmosphere=asb.Atmosphere()):
        denisty = atmosphere.density()
        speed_of_sound = atmosphere.speed_of_sound()
        thrust_lapse = ThrustLapse(atmosphere)

        proportionality = 1.15 * np.sqrt(self.engine_inoperative_coefficient / field_length / .85 / CONSTANTS.G0 / denisty / inviscid_ratio)
        intercept = 4 * CONSTANTS.OBSTACLE_HEIGHT * self.engine_inoperative_coefficient / field_length

        mach_from_wing_loading = lambda wing_loading: np.sqrt(wing_loading * 2/denisty / CL_takeoff) / speed_of_sound

        self.constraints_thrust_weight[constraint_label] = lambda wing_loading: (proportionality * np.sqrt(wing_loading) + intercept) / thrust_lapse.thrust_lapse(mach_from_wing_loading(wing_loading), self.bypass) 
