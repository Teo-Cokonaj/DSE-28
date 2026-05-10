import aerosandbox as asb
import os
import sys
import functools as fct

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.global_parameters import CONSTANTS

class ThrustLapse():
    def __init__(self, atmosphere:asb.Atmosphere, theta_t_break:float=1.07):
        self.atmosphere = atmosphere
        self.theta_t_break = theta_t_break

    def thrust_lapse(self, mach:float, bypass:float=0.) -> float:
        gamma_term = (CONSTANTS.GAMMA_AIR -1) / CONSTANTS.GAMMA_AIR
        temperature_total = (1 + gamma_term * mach**2) * self.atmosphere.temperature()
        pressure_total = (1 + gamma_term * mach**2)**(1 / gamma_term) * self.atmosphere.pressure()

        delta_t = pressure_total/CONSTANTS.PRESSURE_SEA_LEVEL
        theta_t = temperature_total/CONSTANTS.TEMPERATURE_SEA_LEVEL

        if bypass < 5:
            return delta_t if (theta_t < self.theta_t_break) else (delta_t * (1 - 2.1 * (theta_t - self.theta_t_break) / theta_t))
        else:
            if theta_t < self.theta_t_break:
                return delta_t * (1 - (0.43 + 0.014 * bypass) * mach**.5)
            else:
                return delta_t * (1 - (0.43 + 0.014 * bypass) * mach**.5 - 3 * (theta_t - self.theta_t_break) / (1.5 + mach))