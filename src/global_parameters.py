# Imports
import aerosandbox.numpy as np

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import src.ac_stats as stat

# Global parameters for configurations:
class CONSTANTS:

    G0 = 9.80665 # [N/kg]
    SAFETY_FACTOR= 1.5 
    GAS_CONSTANT_AIR = 287.05 # [J/kg/K]
    GAMMA_AIR = 1.4
    PRESSURE_SEA_LEVEL = 101325 # [Pa]
    TEMPERATURE_SEA_LEVEL = 288.15 # [K]
    AIR_DENSITY_SEA_LEVEL = 1.225 # [kg/m^3]
    MACH_CRUISE = 0.4
    MACH_MAX = 0.75
    TIME_CRUISE = 25 * 60 # [s]
    TIME_MACH_MAX = 5 * 60 # [s]
    ALTITUDE_MACH_MAX = 27000 * 0.3048 # [m], (27000 in ft)
    TEMPERATURE_LAPSE = -.0065 # [K/m]
    N_LANDING_ATTEMPTS = 4
    MASS_PAYLOAD = 5. # [kg]
    DYNAMIC_VISCOSITY_SEA_LEVEL = 1.789e-5 # [kg/m/s]

    #cs-23 requirements
    OBSTACLE_HEIGHT = 11 # [m]
    ALTITUDE_OEI_CLIMB = 122 # [m]
    CLIMB_GRADIENT_AEO = .04
    CLIMB_GRADIENT_OEI = .01

    #material properties
    DENSITY_CFRP = 1600.0 # [kg/m^3]
    YIELD_STRENGTH_CFRP = 600e6 # [Pa]  
    E_MODULUS_CFRP = 80e9 # [Pa]      
    

class Assumptions():

    def __init__(self):
    
        # Cruise Assumptions:
        self.ALTITUDE_CRUISE = 5500.0 # [m] (up for review)
        self.AIR_DENSITY_CRUISE_ALTITUDE = 0.695 # [kg/m^3]
        self.TEMPERATURE_CRUISE_ALTITUDE = 252.2 #[K]

        self.energy_density_saf = 42.8e6 # [J/kg]

        # TURN ASSUMPTIONS:
        self.ALTITUDE_GO_AROUND = 2000. # [m]
        self.TIME_HALF_CIRCLE = 60.0 # [s]
        self.OMEGA_GO_AROUND = np.pi / 60 # [rad/s] -> rate 1 coordinated turn
        self.MC=0.75 #cruise Mach number
        self.MD = 0.80 #ADSEE: in general, MD is 0.05M higher than MC
        self.positive_C_L_max_airfoil=1.25 #CHANGE
        self.negative_C_L_max_airfoil=-1.25 #CHANGE
        self.C_L_alpha = 0.5*2*np.pi #CHANGE

        self.airfield_length = 1275. #m #TODO check with the actual airport

        # Geometry Assumptions:
        #CG position
        self.CG_EXCURSION_MAC = 0.5

        # Fuselage
        self.diameter_fuselage = .15 # m (based on FLEXOP)
        self.fuselage_length1_per_area = .55 / 2.499245 # nose cone length / span (based on FLEXOP)
        self.fuselage_length2_per_area = 1.75 / 2.499245  # middle fuselage section length /span (based on FLEXOP)
        self.fuselage_length3_per_area = 1.12 / 2.499245  # tail cone length / span (based on FLEXOP)
        self.fuselage_upsweep = np.radians(11) # [rad] (based on FLEXOP)
        self.fuselage_base_area = 0 # A_base should only reflect truly blunt aft terminations
        
        # Main gear (all are placeholders currently)
        self.main_gear_diameter_wheel = 0.05   # [m] standard for 50-80kg UAV class
        self.main_gear_width_wheel    = 0.025  # [m]
        self.main_gear_height_strut   = 0.1   # [m] sized for belly clearance + rotation angle
        self.main_gear_width_strut    = 0.01  # [m]
        self.main_gear_enclosed       = False

        # Nose gear (all are placeholders currently)
        self.nose_gear_diameter_wheel = 0.04   # [m] smaller since lightly loaded
        self.nose_gear_width_wheel    = 0.02  # [m]
        self.nose_gear_height_strut   = 0.1   # [m] slightly shorter than main to give nose-up ground attitude
        self.nose_gear_width_strut    = 0.008  # [m]
        self.nose_gear_enclosed       = False

        #tail arm
        self.moment_arm_per_area = stat.HT_arm_over_area # based on FLEXOP

        self.statistical_OEM_fraction = 870 / 1008

    @property
    def airspeed_approach(self) -> float:
        return self.airspeed_stall * 1.3
    
    @property
    def airspeed_stall(self) -> float:
        return np.sqrt(self.airfield_length / .6)


class Engine():
    def __init__(self):
        # ENGINE CONSTANTS --- ENGINE TBD ---
        pass
    