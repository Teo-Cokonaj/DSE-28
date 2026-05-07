import sys
import os
import numpy as np

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Drag.Component import Component

class Bay(Component):
    def __init__(self, interference_factor, length:float, diameter:float, laminar_fraction, surface_reynolds_factor = 0.00000405):
        self.length_to_diameter = length/diameter
        surface_wetted = length*np.pi/4*diameter**2  
        super().__init__(interference_factor, surface_wetted, length, laminar_fraction, surface_reynolds_factor)

    
    def form_factor(self, mach=None)->float:
        return 1+.35/self.length_to_diameter