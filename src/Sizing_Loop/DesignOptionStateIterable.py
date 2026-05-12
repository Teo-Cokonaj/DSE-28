from dataclasses import dataclass

import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.objects.aircraft_parameters import AircraftParameters
from src.objects.lifting_surface_planform import LiftingSurfacePlanform
from src.objects.propulsion_parameters import PropulsionParameters
from src.objects.performance_parameters import PerformanceParameters
from src.global_parameters import CONSTANTS

@dataclass
class DesignOptionStateIterable:
    aircraft_parameters:AircraftParameters
    lifting_surfaces:list[LiftingSurfacePlanform]
    propulsion_parameters:PropulsionParameters
    performance_parameters:PerformanceParameters

    def wing_loading(self):
        return CONSTANTS.G0 * self.aircraft_parameters.total_mass / self.lifting_surfaces[0].wing_area
    