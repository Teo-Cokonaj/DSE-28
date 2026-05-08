import sys
import os
import numpy as np

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Drag.Component import Component

class Fuselage(Component):
    def __init__(self, interference_factor, geometry_params:dict[str, float], laminar_fraction, surface_reynolds_factor = 0.00000405):

        characteristic_length = (geometry_params["length1"] + geometry_params["length2"] + geometry_params["length3"])
        surface_wetted = Fuselage._wetted_area_fuselage(geometry_params)
        self.lenght_to_diameter = characteristic_length / geometry_params["diameter"] 
        self.cross_section_area_max = np.pi/4*geometry_params["diameter"]**2
        self.upsweep = geometry_params["upsweep"]
        self.area_base = geometry_params["area_base"]

        super().__init__(interference_factor, surface_wetted, characteristic_length, laminar_fraction, surface_reynolds_factor)
        

    @staticmethod  
    def _wetted_area_fuselage(geometry_param)->float:
        D =  geometry_param["diameter"]
        L1 = geometry_param["length1"]
        L2 = geometry_param["length2"]
        L3 = geometry_param["length3"]
        S_wet_fus = np.pi*D/4*(1/(3*L1**2)*((4*L1**2+D**2/4)**1.5-D**3/8)-D+4*L2+2*np.sqrt(L3**2+D**2/4))
        return S_wet_fus
    

    def form_factor(self, mach=None)->float:
        FF_fuslage = 1+60/self.lenght_to_diameter**3 +self.lenght_to_diameter/400
    
        return FF_fuslage
    

    def drag_area_contribution(self, mach):
        upsweep_contribution = 3.83 * self.upsweep**2.5 * self.cross_section_area_max
        base_drag_contribution = (.139 + .419*(mach-.161)**2) * self.area_base
        return upsweep_contribution + base_drag_contribution
        