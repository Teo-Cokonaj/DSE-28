import sys
import os
import numpy as np

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Drag.Component import Component

class Bay(Component):
    def __init__(self, interference_factor, geometry_params:dict[str, float], laminar_fraction, surface_reynolds_factor = 0.00000405):
        self.length_to_diameter = geometry_params['L']/geometry_params['D']
        surface_wetted = geometry_params['L']*np.pi/4*geometry_params['D']**2  
        super().__init__(interference_factor, surface_wetted, geometry_params['L'], laminar_fraction, surface_reynolds_factor)

    
    def form_factor(self, mach=None):
        return 1+.35/self.length_to_diameter