import sys
import os
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src_final.Requirements.Requirement import Requirement
from Aircraft.Aircraft import Aircraft
from global_parameters import CONSTANTS, Assumptions


class FuelReq(Requirement):
    def assess(self, aicraft:Aircraft) -> bool:
        fuel_mass_fixed = Aircraft.fixed.fuel_mass

        #fuel_mass_required = fuel_mass_cruise + fuel_mass_max_mach + Assumptions.N_LANDING_ATTEMPTS*fuel_go_around
        
        pass #TODO: connect the fuel estimation. Check if the fuselage fuel tanks have enough fuel
        
