import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Aircraft import Aircraft
from Drag import Component

class Planform(Component):
    def __init__(self,
                 surface_wetted:float,
                 length_total:float,
                 laminar_fraction:float=.05,
                 taper: float = 1.0,
                 ):
        super().__init__(
            interference_factor = 1., #fuselage serves as the base of the buildup
            surface_wetted = surface_wetted,
            characteristic_length = length_total,
            laminar_fraction = laminar_fraction 
        )
        self.taper=taper
