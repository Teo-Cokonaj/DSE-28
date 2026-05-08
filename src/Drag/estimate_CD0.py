import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Drag.Component import Component

def estimate_CD0(components:list[Component], altitude:float, mach:float, surface_reference:float, excrescense_leakage_fraction:float=.05) -> float:

    surface_wetted_total = sum([component.surface_wetted for component in components])
    CD0_from_average =  sum([component.surface_wetted * component.CD0_contribution(altitude, mach) for component in components]) / surface_wetted_total

    CD0_from_drag_areas = sum([component.drag_area_contribution(mach) for component in components]) / surface_reference

    return (CD0_from_average + CD0_from_drag_areas) / (1 - excrescense_leakage_fraction)