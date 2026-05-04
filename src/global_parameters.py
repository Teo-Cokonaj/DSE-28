# Global parameters for configurations:
import numpy as np

class CONSTANTS:

    G0 = 9.80665
    MACH_CRUISE = 0.4
    MACH_MAX = 0.75
    TIME_CRUISE = 25 * 60 # [s]
    TIME_MACH_MAX = 5 * 60 # [s]
    ALTITUDE_MACH_MAX = 27000 * 0.3048 # [m], (27000 in ft)
    ALTITUDE_CRUISE = 5500 # [m]


    # TURN ASSUMPTIONS:

    TIME_HALF_CIRCLE = 60 # [s]
    OMEGA_GO_AROUND = np.pi / 60 # [rad/s] -> rate 1 coordinated turn
    

    # ENGINE CONSTANTS --- ENGINE TBD ---