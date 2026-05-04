# Imports
import numpy as np

# Global parameters for configurations:
class CONSTANTS:

    G0 = 9.80665
    MACH_CRUISE = 0.4
    MACH_MAX = 0.75
    TIME_CRUISE = 25 * 60 # [s]
    TIME_MACH_MAX = 5 * 60 # [s]
    ALTITUDE_MACH_MAX = 27000 * 0.3048 # [m], (27000 in ft)
    

class Assumptions():

    def __init__(self):
    
        # Cruise Assumptions:
        self.ALTITUDE_CRUISE = 5500 # [m] (up for review)

        # TURN ASSUMPTIONS:
        self.TIME_HALF_CIRCLE = 60 # [s]
        self.OMEGA_GO_AROUND = np.pi / 60 # [rad/s] -> rate 1 coordinated turn


class Engine():
    def __init__(self):
        # ENGINE CONSTANTS --- ENGINE TBD ---
        pass
    