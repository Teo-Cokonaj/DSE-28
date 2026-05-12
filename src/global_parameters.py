# Imports
import aerosandbox.numpy as np

# Global parameters for configurations:
class CONSTANTS:

    G0 = 9.80665
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
    OBSTACLE_HEIGHT = 11 #[m]
    

class Assumptions():

    def __init__(self):
    
        # Cruise Assumptions:
        self.ALTITUDE_CRUISE = 5500.0 # [m] (up for review)
        self.AIR_DENSITY_CRUISE_ALTITUDE = 0.695 # [kg/m^3]
        self.TEMPERATURE_CRUISE_ALTITUDE = 252.2 #[K]

        # TURN ASSUMPTIONS:
        self.ALTITUDE_GO_AROUND = 2000. # [m]
        self.TIME_HALF_CIRCLE = 60.0 # [s]
        self.OMEGA_GO_AROUND = np.pi / 60 # [rad/s] -> rate 1 coordinated turn
        self.MC=0.75 #cruise Mach number
        self.MD = 0.80 #ADSEE: in general, MD is 0.05M higher than MC
        self.positive_C_L_max_airfoil=1.25 #CHANGE
        self.negative_C_L_max_airfoil=-1.25 #CHANGE
        self.C_L_alpha = 0.5*2*np.pi #CHANGE

        self.airfield_length = 1000. #m #TODO check with the actual airport

        # Geometry Assumptions:
        # Fuselage
        self.diameter_fuselage = .15 # m (based on FLEXOP)
        self.fuselage_length1 = .55 # [m] nose cone length (based on FLEXOP)
        self.fuselage_length2 = 1.75 # [m] middle fuselage section length (based on FLEXOP)
        self.fuselage_length3 = 1.12 # [m] tail cone length (based on FLEXOP)
        self.fuselage_upsweep = np.radians(11) # [rad] (based on FLEXOP)
        self.fuselage_base_area = np.pi / 4 * self.diameter_fuselage**2 * 0.1  # [m^2] (10% of max cross-section?)
        
        # Main gear (all are placeholders currently)
        self.main_gear_diameter_wheel = 0.15   # [m] standard for 50-80kg UAV class
        self.main_gear_width_wheel    = 0.055  # [m]
        self.main_gear_height_strut   = 0.20   # [m] sized for belly clearance + rotation angle
        self.main_gear_width_strut    = 0.035  # [m]
        self.main_gear_enclosed       = False

        # Nose gear (all are placeholders currently)
        self.nose_gear_diameter_wheel = 0.10   # [m] smaller since lightly loaded
        self.nose_gear_width_wheel    = 0.045  # [m]
        self.nose_gear_height_strut   = 0.18   # [m] slightly shorter than main to give nose-up ground attitude
        self.nose_gear_width_strut    = 0.025  # [m]
        self.nose_gear_enclosed       = False

class Engine():
    def __init__(self):
        # ENGINE CONSTANTS --- ENGINE TBD ---
        pass
    