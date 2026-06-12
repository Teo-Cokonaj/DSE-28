import sys
import os
import numpy as np

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Drag.Component import Component

class Bay(Component):
    def __init__(self, surface_wetted:float, length:float, diameter:float, interference_factor=1.3, laminar_fraction=.1, surface_reynolds_factor=.405e-5):
        super().__init__(
            interference_factor=interference_factor,
            surface_wetted=surface_wetted,
            characteristic_length=length,
            laminar_fraction=laminar_fraction,
            surface_reynolds_factor=surface_reynolds_factor
        )

        self.diameter = diameter

    def form_factor(self, mach=None)->float:
        return 1+.35/self.characteristic_length/self.diameter
        
    