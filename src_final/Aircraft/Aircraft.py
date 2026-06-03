import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import numpy as np

from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed
from global_parameters import CONSTANTS, Assumptions


class Aircraft:
    def __init__(self,
                 fixed: Fixed,
                 planforms:list[Planform]
                 ):
        self.fixed = fixed
        self.planforms = planforms


    def total_mass(self)->float:
        return self.fixed.mass + sum(planform.mass_cache for planform in self.planforms)
    
    def mach_go_around(self, assumptions:Assumptions):

        #TODO: find the go-around airspeed

        Temperature_go_around = CONSTANTS.TEMPERATURE_SEA_LEVEL + CONSTANTS.TEMPERATURE_LAPSE*assumptions.altitude_go_round                                                                                                
        speed_of_sound_go_around = np.sqrt(CONSTANTS.GAMMA_AIR * CONSTANTS.GAS_CONSTANT_AIR * Temperature_go_around)


        airspeed_go_around = 1.0


        mach_go_around = airspeed_go_around / speed_of_sound_go_around

        return mach_go_around
    
    def glide_ratio(self, mach:float, altitude:float) -> float:

        #TODO: Fix CD0 and Component imports (Marek)
        
        Temperature_at_altitude = CONSTANTS.TEMPERATURE_SEA_LEVEL + CONSTANTS.TEMPERATURE_LAPSE*altitude
        density_at_altitude = CONSTANTS.AIR_DENSITY_SEA_LEVEL*(Temperature_at_altitude/CONSTANTS.TEMPERATURE_SEA_LEVEL)**(CONSTANTS.G0/(CONSTANTS.TEMPERATURE_LAPSE*CONSTANTS.GAS_CONSTANT_AIR)-1)
        speed_of_sound_at_altitude = np.sqrt(CONSTANTS.GAMMA_AIR*CONSTANTS.GAS_CONSTANT_AIR*Temperature_at_altitude)                                                                                                        
        airspeed_at_altitude = speed_of_sound_at_altitude*mach
        total_weight = self.total_mass * CONSTANTS.G0

        CL_at_altitude = 2*(total_weight/self.planforms[0].wing_area)*1/(airspeed_at_altitude**2)*1/density_at_altitude
        CD0 = CD0_from_cache(self.planforms[0], list[Component], self.planforms[0].wing_area)

        CD_at_altitude = CD0 + CL_at_altitude**2/(np.pi*self.planforms[0].aspect_ratio*self.planforms[0].oswald)
        glide_ratio = CL_at_altitude/CD_at_altitude

        return glide_ratio, CL_at_altitude