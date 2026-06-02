import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Drag import Component

class Fuselage(Component):
    def __init__(self, surface_wetted:float, length_total:float, laminar_fraction:float=.05):
        super().__init__(
            interference_factor = 1., #fuselage serves asthe base of the buildup
            surface_wetted = surface_wetted,
            characteristic_length = length_total,
            laminar_fraction = laminar_fraction 
        )