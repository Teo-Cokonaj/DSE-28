import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Drag.Component import Component

class Fuselage(Component):
    def __init__(self, surface_wetted:float, length_total:float, diameter_max:float, upsweep:float, base_area:float, laminar_fraction:float=.05, surface_reynolds_factor:float=.405e-5):
        
        super().__init__(
            interference_factor = 1., #fuselage serves asthe base of the buildup
            surface_wetted = surface_wetted,
            characteristic_length = length_total,
            laminar_fraction = laminar_fraction,
            surface_reynolds_factor = surface_reynolds_factor
        )

        #in m
        self.diameter_max = diameter_max

        #in m, from the nose:
        self.upsweep = upsweep
        self.base_area = base_area


    def form_factor(self, mach:float)->float:
        length_to_diameter = self.characteristic_length/self.diameter_max
        return 0.9+5/length_to_diameter**1.5 +length_to_diameter/400
    
    def drag_area_contribution(self, mach):
        upsweep_contribution = 3.83 * self.upsweep**2.5 * self.cross_section_area_max
        base_drag_contribution = (.139 + .419*(mach-.161)**2) * self.area_base
        return upsweep_contribution + base_drag_contribution