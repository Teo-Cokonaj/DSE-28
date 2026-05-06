import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Drag.Component import Component

class Bay(Component):
    def __init__(self, interference_factor, geometry_params:dict[str, float], laminar_fraction, surface_reynolds_factor = 0.00000405):
        surface_wetted, characteristic_length = 0 #TODO compute from geometry
        
        super().__init__(interference_factor, surface_wetted, characteristic_length, laminar_fraction, surface_reynolds_factor)

    
    def form_factor(self, mach):
        #TODO: implement
        pass