from dataclasses import dataclass

import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.objects.aircraft_parameters import AircraftParameters
from src.objects.lifting_surface_planform import LiftingSurfacePlanform
from src.objects.propulsion_parameters import PropulsionParameters
from src.objects.performance_parameters import PerformanceParameters

@dataclass
class DesignOptionStateIterable:
    aircraft_parameters:AircraftParameters
    lifting_surfaces:list[LiftingSurfacePlanform]
    propulsion_parameters:PropulsionParameters
    performance_parameters:PerformanceParameters