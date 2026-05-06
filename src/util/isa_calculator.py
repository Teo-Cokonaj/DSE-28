import math

import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from global_parameters import CONSTANTS

def temp_eq (h):
        return CONSTANTS.TEMPERATURE_SEA_LEVEL+CONSTANTS.TEMPERATURE_LAPSE*(h)

def press_eq (tempalt):
    return CONSTANTS.PRESSURE_SEA_LEVEL*(tempalt/CONSTANTS.TEMPERATURE_SEA_LEVEL)**(-CONSTANTS.G0/(CONSTANTS.GAS_CONSTANT_AIR*CONSTANTS.TEMPERATURE_LAPSE))


def dens_eq (pressalt, tempalt):
    return (pressalt/(CONSTANTS.GAS_CONSTANT_AIR*tempalt))

def dens_at_h(h):
    tempalt = temp_eq(h)
    pressalt = press_eq(tempalt)
    return dens_eq(pressalt, tempalt)

def speed_of_sound_at_h(h):
    return math.sqrt(CONSTANTS.GAMMA_AIR*CONSTANTS.GAS_CONSTANT_AIR*temp_eq(h)) 