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
       

    @statiicmethod  
    def _wetted_area_fuselage(geometry_param):
        D =  geometry_param["Fuselage_Diameter"]
        L1 = geometry_param["L1_fuselage"]
        L2 = geometry_param["L2_fuselage"]
        L3 = geometry_param["L3_fuselage"]
        S_wet_fus = np.pi* D/4 * (1/(3*L1**2 * (4*L1**2 + D**2/4)**(1.5) -D**3/8) - D +4*L2 +2 * np.sqrt(L3**2 + D**2/4))
        return S_wet_fus
    
    def form_factor(self, mach):
        
        
        pass