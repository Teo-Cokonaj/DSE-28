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

    ULTIMATE_LOAD_FACTOR = 9. 
    

class Assumptions():

    def __init__(self):
    
        # Cruise Assumptions:
        self.ALTITUDE_CRUISE = CONSTANTS.ALTITUDE_MACH_MAX # [m]
        self.AIR_DENSITY_CRUISE_ALTITUDE = 0.38 # [kg/m^3]
        self.TEMPERATURE_CRUISE_ALTITUDE = 273-35 #[K]

        self.energy_density_saf = 42.8e6 # [J/kg]

        # TURN ASSUMPTIONS:
        self.ALTITUDE_GO_AROUND = 1500 / .3048 # [m]
        self.TIME_HALF_CIRCLE = 60.0 # [s]
        self.OMEGA_GO_AROUND = np.pi / 60 # [rad/s] -> rate 1 coordinated turn

        self.MC=0.45 #cruise Mach number
        self.MD = 0.80

        self.airfoil_thickness_to_chord_max = .12
        self.airfoil_thickness_to_chord_max_location = .37
        self.max_camber_position = np.inf #to cancel the camber term
        self.positive_C_L_max_airfoil=1.25 #CHANGE
        self.negative_C_L_max_airfoil=-1.25 #CHANGE
        self.airfoil_C_l_alpha = 0.5/np.radians(4.0) #0.5 per 4deg
        # self.C_L_alpha_airfoil=0.25/np.radians(5.0)
        self.C_L_alpha=3.0

        self.airfield_length = 1275. #m #TODO check with the actual airport

        # Geometry Assumptions:
        #CG position
        self.CG_EXCURSION_MAC = 0.5

        # Fuselage
        self.diameter_fuselage = .315 # m (based on FLEXOP)
        self.fuselage_length1 = .55 # nose cone length / span (based on FLEXOP)
        self.fuselage_length2 = 1.75   # middle fuselage section length /span (based on FLEXOP)
        self.fuselage_length3 = 1.12  # tail cone length / span (based on FLEXOP)
        self.fuselage_upsweep = np.radians(11) # [rad] (based on FLEXOP)
        self.fuselage_base_area = 0 # A_base should only reflect truly blunt aft terminations
        
        # Main gear (all are placeholders currently)
        W_main_lbf = (0.85 * 50 * 2.205) / 2   # ~46.9 lbf per wheel
        self.main_gear_diameter_wheel = .015#1.51 * W_main_lbf**0.349 * 0.0254  # ~0.147 m
        self.main_gear_width_wheel    = .0075#0.751 * W_main_lbf**0.312 * 0.0254 # ~0.061 m
        #self.main_gear_height_strut   = 0.156   # [m] 
        self.main_gear_width_strut    = 0.01  # [m]
        self.main_gear_enclosed       = True

        # Nose gear (all are placeholders currently)
        self.nose_gear_diameter_wheel = .015#0.8*self.main_gear_diameter_wheel  # [m] 80% ot MLG
        self.nose_gear_width_wheel    = .0075#0.8*self.main_gear_width_wheel  # [m]
        #self.nose_gear_height_strut   = 0.156   # [m] 
        self.nose_gear_width_strut    = 0.01  # [m]
        self.nose_gear_enclosed       = True

        #tail arm
        self.moment_arm = stat.HT_arm_FLEXOP # based on FLEXOP

        self.fuselage_laminar_frac = .05
        self.wing_bay_laminar_frac = .1
        self.lg_bay_length_safety_factor = 1.25
        self.lg_bay_wheel_diameter_ratio = 2.


    @property
    def airspeed_approach(self) -> float:
        return self.airspeed_stall * 1.3
    
    @property
    def airspeed_stall(self) -> float:
        return np.sqrt(self.airfield_length / .6)
    