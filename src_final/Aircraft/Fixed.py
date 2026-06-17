import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Drag.Fuselage import Fuselage
from Drag.LandingGear import LandingGear
from Drag.Bay import Bay
from Drag.Component import Component

# to do: add tail cone x location. (default tail upsweep is 15 degrees)
class Fixed:
    # NOTE: y_main_gear is the distance between the 2 wheels
    def __init__(self, mass:float, fuel_mass:float, x_cg_min:float, x_cg_max:float, x_tail_cone:float, z_cg:float, z_tail_cone:float, z_wing:float, x_LE_canard:float, x_LE_wing:float, x_LE_tail:float, x_nose_gear:float, 
                 x_main_gear:float, y_main_gear:float, fuselage:Fuselage, nose_gear:LandingGear, main_gear:LandingGear, 
                 engine_bay:Bay):
    
        self.mass = mass
        self.fuel_mass = fuel_mass

        self.x_cg_min = x_cg_min
        self.x_cg_max = x_cg_max
        self.x_tail_cone = x_tail_cone # Added to init by Guilherme
        self.z_cg = z_cg
        self.z_tail_cone = z_tail_cone # Added to init by Guilherme
        self.z_wing = z_wing # Added to init by Guilherme

        self.x_LE_canard = x_LE_canard
        self.x_LE_wing = x_LE_wing
        self.x_LE_tail = x_LE_tail

        self.x_nose_gear = x_nose_gear
        self.x_main_gear = x_main_gear
        self.y_main_gear = y_main_gear

        self.fuselage = fuselage
        self.nose_gear = nose_gear
        self.main_gear = main_gear
        self.engine_bay = engine_bay


    def drag_components(self, gear_down:bool) -> list[Component]:
        if gear_down:
            return [self.fuselage, self.nose_gear, self.main_gear, self.main_gear, self.engine_bay, self.engine_bay]
        else:
            return [self.fuselage, self.engine_bay, self.engine_bay]