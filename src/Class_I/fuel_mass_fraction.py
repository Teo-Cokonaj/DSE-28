import sys
import os
import numpy as np

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from global_parameters import CONSTANTS
from Class_I.Mission_Segment import Mission_Segment
from util.isa_calculator import dens_at_h, speed_of_sound_at_h

def fuel_mass_fraction(altitude_go_around:float, altitude_cruise:float, time_half_turn:float, CL_max_glide_ratio_go_around:float, 
                       glide_ratio_mach_max:float, glide_ratio_cruise:float, glide_ratio_go_around:float, airspeed_approach:float,
                       wing_loading:float, efficiency_engine_total:float, energy_density_saf:float,  debug=False) -> float:

    #determining the cruise parameters
    airspeed_cruise = speed_of_sound_at_h(altitude_cruise)*CONSTANTS.MACH_CRUISE
    
    #determining the max Mach parameters
    airspeed_mach_max = speed_of_sound_at_h(CONSTANTS.ALTITUDE_MACH_MAX)*CONSTANTS.MACH_MAX
    
    #determining go around parameters
    omega_turn = np.pi/time_half_turn
    rho_go_around_altitude = dens_at_h(altitude_go_around)
    # n**2 - quadratic_b_term*n -1
    quadratic_b_term = omega_turn**2/CONSTANTS.G0**2 * wing_loading * 2/rho_go_around_altitude / CL_max_glide_ratio_go_around
    load_factor_go_around = .5*(quadratic_b_term + np.sqrt(quadratic_b_term**2+4))
    airspeed_go_around = np.sqrt(wing_loading * 2/rho_go_around_altitude * load_factor_go_around/CL_max_glide_ratio_go_around)

    segment_cruise = Mission_Segment(glide_ratio_cruise, airspeed_cruise, CONSTANTS.TIME_CRUISE, altitude_cruise)
    segment_mach_max = Mission_Segment(glide_ratio_mach_max, airspeed_mach_max, CONSTANTS.TIME_MACH_MAX, CONSTANTS.ALTITUDE_MACH_MAX-altitude_cruise, airspeed_cruise)
    segment_go_around = Mission_Segment(glide_ratio_go_around, airspeed_go_around, time_half_turn, altitude_go_around, airspeed_approach)
    segment_go_around.equivalent_range *= CONSTANTS.N_LANDING_ATTEMPTS #we need multiple times the range for one go around

    fuel_frac_cruise = segment_cruise.fuel_fraction(efficiency_engine_total, energy_density_saf)

    fuel_frac_mach_max_local = segment_mach_max.fuel_fraction(efficiency_engine_total, energy_density_saf)
    fuel_frac_mach_max = fuel_frac_mach_max_local*(1-fuel_frac_cruise)

    fuel_frac_go_around_local = segment_go_around.fuel_fraction(efficiency_engine_total, energy_density_saf)
    fuel_frac_go_around = fuel_frac_go_around_local*(1-fuel_frac_cruise-fuel_frac_mach_max)

    if debug:
        print("=====fuel mass fraction intermediate values====")
        print(f"load_factor_go_around: {load_factor_go_around}")
        print(f"airspeed_go_around: {airspeed_go_around}")
        print(f"Fuel fractions: {fuel_frac_cruise} for cruise, {fuel_frac_mach_max} for mach max, {fuel_frac_go_around} for go-around")
        print(f"Fuel_fractions local {fuel_frac_mach_max_local} for mach max, {fuel_frac_go_around_local} for go around")
        print(f"Equivalent ranges: {segment_cruise.equivalent_range} for cruise, {segment_mach_max.equivalent_range} for mach max, {segment_go_around.equivalent_range} for go_around")

    return fuel_frac_cruise + fuel_frac_mach_max + fuel_frac_go_around

