import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Drag.Component import Component


import numpy as np

class Planform(Component):
    def __init__(self, interference_factor, geometry_params:dict[str, float], laminar_fraction, surface_reynolds_factor = 0.00000405):

        
        
        self.interference_factor = interference_factor
        self.geometry_params = geometry_params
        self.laminar_fraction = laminar_fraction
        self.surface_reynolds_factor = surface_reynolds_factor
    
        
        surface_exposed = self.geometry_params['chord_root']*self.geometry_params['taper_ratio']* (self.geometry_params['fuselage_diameter'] / 2) / (self.geometry_params['wing_span'] / 2)
        surface_wetted = 1.07 * 2 * surface_exposed

        # MAC
        characteristic_length = (2 / 3) * self.geometry_params['chord_root'] * (1 + self.geometry_params['taper_ratio'] + self.geometry_params['taper_ratio'] ** 2) / (1 + self.geometry_params['taper_ratio'])
        

        super().__init__(interference_factor, surface_exposed, surface_wetted, characteristic_length, laminar_fraction, surface_reynolds_factor)

    
    def form_factor(self, mach):

        gp = self.geometry_params
        
        FF = ( 1 + 0.6 / gp['pos_max_cambre'] * gp['thickness_to_chord_ratio'] + 100 * gp['thickness_to_chord_ratio'] ** 4 ) * (1.34 * mach ** 0.18 * np.cos( gp['sweep_mean_chord']) ** 0.28)

        return FF