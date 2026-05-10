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
        self.TIME_HALF_CIRCLE = 60.0 # [s]
        self.OMEGA_GO_AROUND = np.pi / 60 # [rad/s] -> rate 1 coordinated turn
        self.MC=0.75 #cruise Mach number
        self.MD = 0.80 #ADSEE: in general, MD is 0.05M higher than MC
        self.positive_C_L_max=1.6 #CHANGE
        self.negative_C_L_max=-0.8 #CHANGE
        self.C_L_alpha = 0.5*2*np.pi #CHANGE


class Engine():
    def __init__(self):
        # ENGINE CONSTANTS --- ENGINE TBD ---
        pass
    