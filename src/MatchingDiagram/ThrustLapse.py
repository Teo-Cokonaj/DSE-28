import aerosandbox as asb
import os
import sys
import functools as fct

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.global_parameters import CONSTANTS

class ThrustLapse():
    def __init__(self, altitude:float, theta_t_break:float=1.07):
        self.atmosphere = asb.Atmosphere(altitude)
        self.theta_t_break = theta_t_break

    @fct.cache
    def thrust_lapse(self, mach:float) -> float:
        gamma_term = (CONSTANTS.GAMMA_AIR -1) / CONSTANTS.GAMMA_AIR
        temperature_total = (1 + gamma_term * mach**2) * self.atmosphere.temperature()
        pressure_total = (1 + gamma_term * mach**2)**(1 / gamma_term) * self.atmosphere.pressure()

        delta_t = pressure_total/CONSTANTS.PRESSURE_SEA_LEVEL
        theta_t = temperature_total/CONSTANTS.TEMPERATURE_SEA_LEVEL

        return delta_t if (theta_t < self.theta_t_break) else (delta_t * (1 - 2.1 * (theta_t - self.theta_t_break) / theta_t))