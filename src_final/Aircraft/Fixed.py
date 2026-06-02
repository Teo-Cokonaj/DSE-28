import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src_final.Drag.Fuselage import Fuselage
from src_final.Drag.LandingGear import LandingGear
from src_final.Drag.Bay import Bay

class Fixed:
    def __init__(self, mass:float, x_cg:float, z_cg:float, x_LE_canard:float, x_LE_wing:float, x_LE_tail:float, x_nose_gear:float, 
                 x_main_gear:float, y_main_gear:float, fuselage:Fuselage, nose_gear:LandingGear, main_gear:LandingGear, 
                 gear_bay:Bay, engine_bay:Bay):
    
        self.mass = mass
        self.x_cg = x_cg
        self.z_cg = z_cg

        self.x_LE_canard = x_LE_canard
        self.x_LE_wing = x_LE_wing
        self.x_LE_tail = x_LE_tail

        self.x_nose_gear = x_nose_gear
        self.x_main_gear = x_main_gear
        self.y_main_gear = y_main_gear

        self.fuselage = fuselage
        self.nose_gear = nose_gear
        self.main_gear = main_gear
        self.gear_bay = gear_bay
        self.engine_bay = engine_bay


    def drag_components(self, gear_down:bool):
        if gear_down:
            return [self.fuselage, self.nose_gear, self.main_gear, self.main_gear, self.gear_bay, self.gear_bay, self.engine_bay, self.engine_bay]
        else:
            return [self.fuselage, self.gear_bay, self.gear_bay, self.engine_bay, self.engine_bay]