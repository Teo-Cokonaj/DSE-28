import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Drag.Component import Component

class Planform(Component):
    def __init__(self, interference_factor, geometry_params:dict[str, float], laminar_fraction, surface_reynolds_factor = 0.00000405):

        surface_exposed = geometry_params[chord_root]*geometry_params[taper_ratio]* (geometry_params[fuselage_diameter] / 2) / (geometry_params[wing_span] / 2)


        surface_wetted = 1.07 * 2 * surface_exposed
        
        # MAC
        characteristic_length = (2 / 3) * geometry_params[chord_root] * (1 + geometry_params[taper_ratio] + geometry_params[taper_ratio] ** 2) / (1 + geometry_params[taper_ratio])
        
        0 #TODO compute from geometry
        


        super().__init__(interference_factor, surface_wetted, characteristic_length, laminar_fraction, surface_reynolds_factor)

    
    def form_factor(self, mach):
        #TODO: implement

        sweep_mean_chord = # todo
        
        FF = ( 1 + 0.6 / geometry_params[pos_max_cambre] * geometry_params[thickness_to_chord_ratio] + 100 geometry_params[thickness_to_chord_ratio] ** 4 ) * (1.34 * mach ** 0.18 * np.cos(sweep_mean_chord)**0.28)