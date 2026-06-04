import sys
import os
import numpy as np
import aerosandbox as asb

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Class_I.fuel_mass_fraction import fuel_mass_fraction
from src_final.Requirements.Requirement import Requirement
from Aircraft.Aircraft import Aircraft

from global_parameters import CONSTANTS, Assumptions


class FuelReq(Requirement):
    #TODO: connect the fuel estimation. Check if the fuselage fuel tanks have enough fuel
    def __init__(self, assumptions:Assumptions=Assumptions()):
        self.assumptions = assumptions

    def assess(self, aircraft:Aircraft) -> bool:
        assumptions = self.assumptions
        fuel_mass_available = aircraft.fixed.fuel_mass
        wing_loading = (aircraft.total_mass()*CONSTANTS.G0)/aircraft.planforms[0].wing_area

        glide_ratio_cruise, _ = aircraft.glide_ratio(assumptions.mach_cruise, assumptions.altitude_cruise, aircraft.CD0_cruise)
        glide_ratio_max_mach, _ = aircraft.glide_ratio(assumptions.mach_max, assumptions.altitude_mach_max, aircraft.CD0_mach_max)
        glide_ratio_go_around, CL_max_glide_ratio_go_around = aircraft.glide_ratio(aircraft.mach_go_around(assumptions), assumptions.altitude_go_round, aircraft.CD0_go_around)

        efficiency_cruise = assumptions.mach_cruise * asb.Atmosphere(assumptions.altitude_cruise).speed_of_sound() / assumptions.sfc / assumptions.energy_density_saf
        efficiency_go_around = aircraft.mach_go_around(assumptions) * asb.Atmosphere(assumptions.altitude_go_round).speed_of_sound() / assumptions.sfc / assumptions.energy_density_saf
        efficiency_mach_max = assumptions.mach_max * asb.Atmosphere(assumptions.altitude_mach_max).speed_of_sound() / assumptions.sfc / assumptions.energy_density_saf

        fuel_mass_required = aircraft.total_mass() * fuel_mass_fraction(assumptions.altitude_go_round, assumptions.altitude_cruise,
                                                                        assumptions.altitude_mach_max, assumptions.time_half_circle, 
                                                                        CL_max_glide_ratio_go_around, glide_ratio_max_mach, glide_ratio_cruise, 
                                                                        glide_ratio_go_around, assumptions.airspeed_approach, wing_loading,
                                                                        efficiency_cruise, assumptions.energy_density_saf, assumptions.mach_cruise,
                                                                        assumptions.mach_max, assumptions.time_cruise, time_mach_max=assumptions.time_mach_max)


<<<<<<< HEAD
        if fuel_mass_available >= fuel_mass_required:
            fuel_mass_pass = True

        if fuel_mass_pass:
            print('Fuel mass requirement passed!')

        else:
            print('Fuel mass requirement failed.')
            print(f'Fuel mass required: {fuel_mass_required}')
            print(f'Fuel mass HUGO: {fuel_mass_available}')
            print(f'Difference {fuel_mass_required-fuel_mass_available}')
=======
        return fuel_mass_available >= fuel_mass_required
>>>>>>> main
