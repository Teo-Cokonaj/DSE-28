import sys
import os
import numpy as np
import aerosandbox as asb

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from global_parameters import CONSTANTS, Assumptions
from Class_I.MissionSegment import Mission_Segment

def fuel_mass_fraction(altitude_go_around:float, altitude_cruise:float, altitude_mach_max:float, time_half_turn:float, CL_max_glide_ratio_go_around:float, 
                       glide_ratio_mach_max:float, glide_ratio_cruise:float, glide_ratio_go_around:float, airspeed_approach:float,
                       wing_loading:float, efficiency_cruise:float, energy_density_saf:float, 
                       mach_cruise:float, mach_max:float, time_cruise:float, time_mach_max:float,
                       debug=False,
                       efficiency_go_around:float=None, efficiency_mach_max:float=None, return_intermediate=False) -> float: 
    if efficiency_go_around is None:
        efficiency_go_around = efficiency_cruise
    if efficiency_mach_max is None:
        efficiency_mach_max = efficiency_cruise

    #determining the cruise parameters
    atmosphere_cruise = asb.Atmosphere(altitude_cruise)
    airspeed_cruise = atmosphere_cruise.speed_of_sound()*mach_cruise
    
    #determining the max Mach parameters
    atmosphere_mach_max = asb.Atmosphere(altitude_mach_max)
    airspeed_mach_max = atmosphere_mach_max.speed_of_sound()*mach_max
    
    #determining go around parameters
    omega_turn = np.pi/time_half_turn
    atmosphere_go_around = asb.Atmosphere(altitude_go_around)
    rho_go_around_altitude = atmosphere_go_around.density()
    #NOTE: to get go around condition, solve n**2 - quadratic_b_term*n -1 = 0
    quadratic_b_term = omega_turn**2/CONSTANTS.G0**2 * wing_loading * 2/rho_go_around_altitude / CL_max_glide_ratio_go_around
    load_factor_go_around = .5*(quadratic_b_term + np.sqrt(quadratic_b_term**2+4))
    airspeed_go_around = np.sqrt(wing_loading * 2/rho_go_around_altitude * load_factor_go_around/CL_max_glide_ratio_go_around)

    segment_cruise = Mission_Segment(glide_ratio_cruise, airspeed_cruise, time_cruise, altitude_cruise)
    segment_mach_max = Mission_Segment(glide_ratio_mach_max, airspeed_mach_max, time_mach_max, altitude_mach_max-altitude_cruise, airspeed_cruise)
    segment_go_around = Mission_Segment(glide_ratio_go_around, airspeed_go_around, time_half_turn * 2, altitude_go_around, airspeed_approach) #we make a full 360 turn in a go around
    segment_go_around.equivalent_range *= CONSTANTS.N_LANDING_ATTEMPTS 

    fuel_frac_cruise = segment_cruise.fuel_fraction(efficiency_cruise, energy_density_saf)
    
    fuel_frac_mach_max_local = segment_mach_max.fuel_fraction(efficiency_mach_max, energy_density_saf)
    fuel_frac_mach_max = fuel_frac_mach_max_local*(1-fuel_frac_cruise)

    fuel_frac_go_around_local = segment_go_around.fuel_fraction(efficiency_go_around, energy_density_saf)
    fuel_frac_go_around = fuel_frac_go_around_local*(1-fuel_frac_cruise-fuel_frac_mach_max)

    if debug:
        print("=====fuel mass fraction intermediate values====")
        print(f"load_factor_go_around: {load_factor_go_around}")
        print(f"airspeed_go_around: {airspeed_go_around}")
        print(f"Fuel fractions: {fuel_frac_cruise} for cruise, {fuel_frac_mach_max} for mach max, {fuel_frac_go_around} for go-around")
        print(f"Fuel_fractions local {fuel_frac_mach_max_local} for mach max, {fuel_frac_go_around_local} for go around")
        print(f"Equivalent ranges: {segment_cruise.equivalent_range} for cruise, {segment_mach_max.equivalent_range} for mach max, {segment_go_around.equivalent_range} for go_around")

    if return_intermediate:
        return fuel_frac_cruise, fuel_frac_mach_max, fuel_frac_go_around
    
    return fuel_frac_cruise + fuel_frac_mach_max + fuel_frac_go_around


if __name__ == "__main__":
    from global_parameters import Assumptions

    assumptions = Assumptions()

    efficiency_cruise = assumptions.mach_cruise * asb.Atmosphere(assumptions.altitude_cruise).speed_of_sound() / assumptions.sfc / assumptions.energy_density_saf
    #TODO: introduce a pickled standard aircraft object here and replace the mach go around with aircraft.mach_go_around
    efficiency_go_around = 0.2 * asb.Atmosphere(assumptions.altitude_go_round).speed_of_sound() / assumptions.sfc / assumptions.energy_density_saf
    efficiency_mach_max = assumptions.mach_max * asb.Atmosphere(assumptions.altitude_mach_max).speed_of_sound() / assumptions.sfc / assumptions.energy_density_saf

    frac_cr, frac_mm, frac_ga = fuel_mass_fraction(
        altitude_go_around=assumptions.altitude_go_round,
        altitude_cruise=assumptions.altitude_cruise,
        altitude_mach_max=assumptions.altitude_mach_max,
        CL_max_glide_ratio_go_around=0.6, #TODO: callibrte with the standard wing later on
        glide_ratio_go_around=10.,
        glide_ratio_mach_max=8.,
        glide_ratio_cruise=13.,
        airspeed_approach=55., #TODO callibrate with the standard win
        time_half_turn=60.,
        wing_loading=1200.,
        efficiency_cruise=efficiency_cruise,
        efficiency_mach_max=efficiency_mach_max,
        efficiency_go_around=efficiency_go_around,
        energy_density_saf=assumptions.energy_density_saf,
        time_cruise=assumptions.time_cruise,
        time_mach_max=assumptions.time_mach_max,
        mach_cruise=assumptions.mach_cruise,
        mach_max=assumptions.mach_max,
        return_intermediate=True
    )

    MTOM=50. #TODO: replace with the test aircraft actual

    print(f"Fuel mass at cruise ({assumptions.altitude_cruise} m, {assumptions.time_cruise} s) = {frac_cr*MTOM} kg")
    print(f"Fuel mass at mach max ({assumptions.altitude_mach_max} m, {assumptions.time_mach_max} s) = {frac_mm*MTOM} kg")
    print(f"Fuel mass at go-around ({assumptions.altitude_go_round} m, {assumptions.time_half_circle*2*CONSTANTS.N_LANDING_ATTEMPTS} s) = {frac_ga*MTOM} kg")