import numpy as np
import os
import sys
from aerosandbox import Atmosphere
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class CONSTANTS:

    G0 = 9.80665 # [N/kg]
    GAS_CONSTANT_AIR = 287.05 # [J/kg/K]
    GAMMA_AIR = 1.4
    PRESSURE_SEA_LEVEL = 101325 # [Pa]
    TEMPERATURE_SEA_LEVEL = 288.15 # [K]
    AIR_DENSITY_SEA_LEVEL = 1.225 # [kg/m^3]
    DYNAMIC_VISCOSITY_SEA_LEVEL = 1.789e-5 # [kg/m/s]
    TEMPERATURE_LAPSE = -.0065 # [K/m]
    N_LANDING_ATTEMPTS = 4
    HEIGHT_OBSTACLE = 11 # [m]
    ALTITUDE_OEI_CLIMB = 122 # [m]
    CLIMB_GRADIENT_AEO = .04
    CLIMB_GRADIENT_OEI = .01


class Assumptions():

    def __init__(self):

        #Flight conditions
        self.mach_cruise = 0.4
        self.mach_max = 0.75
        self.time_cruise = 25 * 60 # [s]
        self.time_mach_max = 5 * 60 # [s]
        self.altitude_mach_max = 27000 * 0.3048 # [m], (27000 in ft)
        self.altitude_cruise = self.altitude_mach_max # [m]
        self.atmosphere_cruise = Atmosphere(self.altitude_cruise)
        self.air_density_cruise_altitude = self.atmosphere_cruise.density() # [kg/m^3]
        self.temperature_cruise_altitude = self.atmosphere_cruise.temperature() #[K]
        self.altitude_go_round = 1500 / .3048 # [m]
        self.time_half_circle = 60.0 # [s]
        self.omega_go_round = np.pi / 60 # [rad/s] -> rate 1 coordinated turn
        self.airfield_length = 1275. #m #TODO check with the actual airport
        self.positive_manoeuvring_limit_load_factor=6.0 #CS-23 aerobatic

        #Structural properties
        self.structural_safety_factor= 1.5 
        self.cfrp_density = 1600.0 # [kg/m^3]
        self.cfrp_yield_strength = 600e6 # [Pa]  
        self.cfrp_Young_modulus = 80e9 # [Pa]
        self.energy_density_saf = 42.8e6 # [J/kg]           

        #Mass properties
        self.initial_total_aircraft_mass = 50.0 # [kg]
        self.cg_excursion_mac = 0.5
        self.mass_payload = 5. # [kg]

        #Fuselage dimensions
        self.diameter_fuselage = .315 # m (based on FLEXOP)
        self.fuselage_length1 = .55 # nose cone length / span (based on FLEXOP)
        self.fuselage_length2 = 1.75   # middle fuselage section length /span (based on FLEXOP)
        self.fuselage_length3 = 1.12  # tail cone length / span (based on FLEXOP)
        self.fuselage_upsweep = np.radians(11) # [rad] (based on FLEXOP)
        self.fuselage_base_area = 0 # A_base should only reflect truly blunt aft terminations
        
        # Main gear properties (based on FLEXOP)
        self.main_gear_diameter_wheel = 0.17 / 2 # [m]
        self.main_gear_width_wheel    = 0.05 / 2 # [m]
        self.main_gear_height_strut   = 0.156 # [m] 
        self.main_gear_width_strut    = 0.05 / 2  # [m]
        self.main_gear_enclosed       = True

        # Nose gear properties (based on FLEXOP)
        self.nose_gear_diameter_wheel = self.main_gear_diameter_wheel  # [m] 
        self.nose_gear_width_wheel    = self.main_gear_width_wheel  # [m]
        self.nose_gear_height_strut   = 0.156 # [m] 
        self.nose_gear_width_strut    = self.main_gear_width_strut       # [m]
        self.nose_gear_enclosed       = True

        self.fuselage_laminar_frac = .05
        self.wing_bay_laminar_frac = .1
        self.lg_bay_length_safety_factor = 1.25
        self.lg_bay_wheel_diameter_ratio = 2.


    @property
    def airspeed_approach(self) -> float:
        return self.airspeed_stall * 1.3  #Vos
    
    @property
    def airspeed_stall(self) -> float:
        return np.sqrt(self.airfield_length / .6)  #Vos
    