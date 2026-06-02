import sys
import os
import numpy as np

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Drag.Component import Component

class LandingGear(Component):
    def __init__(self, tire_width:float, exposed_height:float, ):
        super().__init__(0., 0., 0., 0., 0.)

        gp = geometry_params
        for key, value in gp.items():
            assert value > 0, f"{key}, {value}"

        self.surface_reference = gp["width_total"]*gp["height_total"]
        self.surface_frontal = gp["width_strut"]*gp["height_strut"]+gp["width_wheel"]*gp["diameter_wheel"]

        self.gp = gp

        self._drag_area = 0.05328 * np.exp(5.615*self.surface_frontal/self.surface_reference) * self.surface_reference

    def drag_area_contribution(self, mach) -> float:
        return self._drag_area