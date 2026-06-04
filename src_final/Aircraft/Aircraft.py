import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    
        



    

    
