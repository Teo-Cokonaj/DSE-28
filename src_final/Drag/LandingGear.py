import sys
import os
import numpy as np

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Drag.Component import Component

class LandingGear(Component):
    def __init__(self, wheel_width:float, exposed_height:float, wheel_diameter:float, strut_width:float):
        super().__init__(1., 1., 1., 0.1)

        width_total = wheel_width + strut_width
        height_total = exposed_height + wheel_diameter / 2

        self.surface_reference = width_total * height_total
        self.surface_frontal = strut_width * exposed_height + wheel_width * wheel_diameter

        self._drag_area = 0.05328 * np.exp(5.615*self.surface_frontal/self.surface_reference) * self.surface_reference

    def drag_area_contribution(self, mach) -> float:
        return self._drag_area
    
    def form_factor(self, mach):
        return 0.