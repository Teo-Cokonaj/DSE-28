import sys
import os
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Class_I.fuel_mass_fraction import fuel_mass_fraction
from src_final.Requirements.Requirement import Requirement
from Aircraft.Aircraft import Aircraft

from global_parameters import CONSTANTS, Assumptions


class FuelReq(Requirement):
    #TODO: connect the fuel estimation. Check if the fuselage fuel tanks have enough fuel

    def assess(self, aircraft:Aircraft, constants:CONSTANTS, assumptions:Assumptions) -> bool:
        fuel_mass_available = aircraft.fixed.fuel_mass
        wing_loading = aircraft.total_mass()/aircraft.planforms[0].wing_area

        

        glide_ratio_cruise, _ = aircraft.glide_ratio(assumptions.mach_cruise, assumptions.altitude_cruise)
        glide_ratio_max_mach, _ = aircraft.glide_ratio(assumptions.mach_max, assumptions.altitude_mach_max)
        glide_ratio_go_around, CL_max_glide_ratio_go_around = aircraft.glide_ratio(assumptions.mach_go_around, assumptions.altitude_go_round)


        fuel_mass_required = aircraft.total_mass() * fuel_mass_fraction(assumptions.altitude_go_round, assumptions.altitude_cruise,                                    
                                                                        assumptions.altitude_mach_max, assumptions.time_half_circle, 
                                                                        CL_max_glide_ratio_go_around, glide_ratio_max_mach, glide_ratio_cruise,
                                                                        glide_ratio_go_around, assumptions.airspeed_approach(), wing_loading,
                                                                        efficiency_cruise, energy_density_saf, assumptions.mach_cruise,
                                                                        assumptions.mach_max, assumptions.time_cruise, assumptions.time_mach_max,
                                                                        debug=False, efficiency_go_around=None efficiency_max_mach=None)
        # CL at max glide ratio during go-around
        # glide ratio at max Mach
        # glide ratio at cruise
        # glide ratio at go-around
        # engine efficiency at cruise
        # engine efficiency at climb
        # engine efficiency at go-around
        # SAF energy density

        if fuel_mass_available >= fuel_mass_required:
            pass
