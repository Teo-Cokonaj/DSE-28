import sys
import os
import numpy as np
from dataclasses import dataclass

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from global_parameters import CONSTANTS
from Class_I.fuel_mass_fraction import fuel_mass_fraction

@dataclass
class Class_I_Result:
    mtom: float
    fuel_fraction: float
    oem_fraction: float

    def fuel_mass(self) -> float:
        return self.mtom*self.fuel_fraction
    
    def oem_mass(self) -> float:
        return self.mtom*self.oem_fraction
    
    def payload_fraction(self) -> float:
        return 1-self.fuel_fraction-self.oem_fraction
    


class Class_I:
    def __init__(self, altitude_cruise:float, altitude_go_around:float, efficiency_engine_total:float, energy_density_saf:float, time_half_turn:float, debug=False):
        #Variables initiated here are assumptions, they must be the same for every design
        self.altitude_cruise = altitude_cruise
        self.altitude_go_around = altitude_go_around
        self.efficiency_engine_total = efficiency_engine_total
        self.energy_density_saf = energy_density_saf
        self.time_half_turn = time_half_turn
        self.debug = debug


    def run_estimation(self, oem_fraction:float, CL_max_glide_ratio_go_around:float, glide_ratio_mach_max:float, 
                       glide_ratio_cruise:float, glide_ratio_go_around:float, airspeed_approach:float, wing_loading:float) -> Class_I_Result:
        
        fuel_fraction = fuel_mass_fraction(self.altitude_go_around, self.altitude_cruise, self.time_half_turn, CL_max_glide_ratio_go_around, 
                       glide_ratio_mach_max, glide_ratio_cruise, glide_ratio_go_around, airspeed_approach,
                       wing_loading, self.efficiency_engine_total, self.energy_density_saf, self.debug)
        
        mtom = CONSTANTS.MASS_PAYLOAD / (1 - oem_fraction - fuel_fraction)

        return Class_I_Result(mtom, fuel_fraction, oem_fraction)