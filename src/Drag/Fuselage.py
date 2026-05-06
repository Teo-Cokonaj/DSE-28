import sys
import os
import numpy as np

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Drag.Component import Component

class Fuselage(Component):
    def __init__(self, interference_factor, geometry_params:dict[str, float], laminar_fraction, surface_reynolds_factor = 0.00000405):
        surface_wetted, characteristic_length = 0 #TODO compute from geometry
        
        super().__init__(interference_factor, surface_wetted, characteristic_length, laminar_fraction, surface_reynolds_factor)
        geometry_params["Fuselage_diameter"] = 10
        geometry_params["L1_lengh"] = 2
        geometry_params["L2_lengh"] = 6
        geometry_params["L3_lengh"] = 2

    @statiicmethod  
    def _wetted_area_fuselage(geometry_param):
        S_wet_fus = np.pi * geom 