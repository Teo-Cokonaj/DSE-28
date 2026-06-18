from dataclasses import dataclass, field

import sys
import copy
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src_midterm.objects.aircraft_parameters import AircraftParameters
from src_midterm.objects.lifting_surface_planform import LiftingSurfacePlanform
from src_midterm.objects.propulsion_parameters import PropulsionParameters
from src_midterm.objects.performance_parameters import PerformanceParameters
from src_midterm.objects.lading_gear import LandingGear

@dataclass
class DesignOptionStateIterable:
    aircraft_parameters:AircraftParameters
    lifting_surfaces:list[LiftingSurfacePlanform]
    propulsion_parameters:PropulsionParameters
    performance_parameters:PerformanceParameters
    landing_gear:LandingGear