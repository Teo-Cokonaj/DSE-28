import sys
import os
import aerosandbox.numpy as np

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Drag.Component import Component

class LandingGear(Component):
    def __init__(self, geometry_params:dict[str, float], enclosed:bool):
        #NOTE: the landing gear contributes to drag area only, not through wetted surface
        super().__init__(0., 0., 0., 0., 0.)

        gp = geometry_params
        surface_reference = gp["width_total"]*gp["height_total"]
        surface_frontal = gp["width_strut"]*gp["height_strut"]+gp["width_wheel"]*gp["diameter_wheel"]

        if enclosed:
            self._drag_area = 0.04955 * np.exp(5.615*surface_frontal/surface_reference) * surface_reference
        else:
            self._drag_area = 0.05328 * np.exp(5.615*surface_frontal/surface_reference) * surface_reference

    
    def form_factor(self, mach):
        return 0.
    

    def CD0_contribution(self, altitude, mach):
        return 0.
    

    def drag_area_contribution(self, mach):
        return self._drag_area