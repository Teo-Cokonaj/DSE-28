import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import numpy as np
import aerosandbox as asb

from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed
from global_parameters import CONSTANTS, Assumptions
from Drag.estimate_CD0 import CD0_from_cache

class Aircraft:
    def __init__(self,
                 fixed: Fixed,
                 planforms:list[Planform]
                 ):
        self.fixed = fixed
        self.planforms = planforms
        
        #self.CD0_go_around = CD0_from_cache("go_around", fixed.drag_components(False) + planforms, planforms[0].wing_area)
        #self.CD0_takeoff = CD0_from_cache("takeoff", fixed.drag_components(True) + planforms, planforms[0].wing_area)
        #self.CD0_mach_max = CD0_from_cache("mach_max", fixed.drag_components(False) + planforms, planforms[0].wing_area)
        #self.CD0_cruise = CD0_from_cache("cruise", fixed.drag_components(False) + planforms, planforms[0].wing_area)

    def total_mass(self)->float:
        return self.fixed.mass + sum(planform.mass_cache for planform in self.planforms)

    def reference_wing_area(self)->float:
        if len(self.planforms) == 0:
            raise ValueError("Cannot compute wing loading without at least one planform.")

        # Use the largest lifting surface as reference wing by default.
        return max(planform.wing_area for planform in self.planforms)

    def wing_loading(self)->float:
        return self.total_mass() * CONSTANTS.G0 / self.reference_wing_area()
    
    def thrust_to_weight(self)->float:
        return Assumptions().thrust_available / self.total_mass()
    
        



    
    def mach_go_around(self, assumptions:Assumptions):
 
        #Define atmosphere for go-around
        atmosphere_go_around = asb.Atmosphere(assumptions.altitude_go_round)         
        density_go_around = atmosphere_go_around.density()     
        Temperature_go_around = atmosphere_go_around.temperature()
        speed_of_sound_go_around = atmosphere_go_around.speed_of_sound()              

        wing_loading = self.total_mass() * CONSTANTS.G0 / self.planforms[0].wing_area
        inviscid_ratio = np.pi*self.planforms[0].aspect_ratio*self.planforms[0].oswald

        # CL_max_glide_ratio from Midterm performance_parameters.py
        CL_max_glide_ratio = np.sqrt(inviscid_ratio * self.CD0_go_around)

        quadratic_b_term = assumptions.omega_go_round**2/CONSTANTS.G0**2 * wing_loading * 2/density_go_around / CL_max_glide_ratio
        load_factor_go_around = .5*(quadratic_b_term + np.sqrt(quadratic_b_term**2+4))

        airspeed_go_around = np.sqrt(wing_loading * 2/density_go_around * load_factor_go_around/CL_max_glide_ratio)

        mach_go_around = airspeed_go_around / speed_of_sound_go_around

        return mach_go_around
    
    def glide_ratio(self, mach:float, altitude:float, CD0:float) -> float:

        #TODO: Fix CD0 and Component imports (Marek)
        
        atmosphere_at_altitude = asb.Atmosphere(altitude)
        density_at_altitude = atmosphere_at_altitude.density()
        Temperature_at_altitude = atmosphere_at_altitude.temperature()
        speed_of_sound_at_altitude = atmosphere_at_altitude.speed_of_sound()                                                                                                  
        airspeed_at_altitude = speed_of_sound_at_altitude*mach
        total_weight = self.total_mass() * CONSTANTS.G0

        CL_at_altitude = 2*(total_weight/self.planforms[0].wing_area)*1/(airspeed_at_altitude**2)*1/density_at_altitude

        CD_at_altitude = CD0 + CL_at_altitude**2/(np.pi*self.planforms[0].aspect_ratio*self.planforms[0].oswald)
        glide_ratio = CL_at_altitude/CD_at_altitude

        return glide_ratio, CL_at_altitude
