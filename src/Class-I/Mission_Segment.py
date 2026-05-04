import sys
import os
import numpy as np

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from global_parameters import CONSTANTS


class Mission_Segment():
    def __init__(self, glide_ratio:float, airspeed:float, time:float, altitude:float, airspeed_initial:float=0.):
        self.glide_ratio = glide_ratio
        self.airspeed = airspeed
        self.time = time
        self.altitude = altitude

        #equivalent range of the segment
        self.equivalent_range = 1/.7 * glide_ratio * (altitude + (airspeed**2-airspeed_initial**2)/2/CONSTANTS.G0) + airspeed*time


    def fuel_fraction(self, efficiency_engine_total:float, energy_density_saf:float):
        return 1 - np.exp( -self.equivalent_range * CONSTANTS.G0 / efficiency_engine_total / self.glide_ratio / energy_density_saf)
    


