import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Drag.Component import Component

def CD0_from_cache(name:str, components:list[Component], surface_reference:float, excrescense_leakage_fraction:float=.05) -> float:
    surface_wetted_total = sum([component.surface_wetted for component in components])

    CD0_from_average =  sum([component.surface_wetted * component.CD0_cache[name] for component in components]) / surface_wetted_total

    CD0_from_drag_areas = sum([component.drag_area_cache[name] for component in components]) / surface_reference

    return (CD0_from_average + CD0_from_drag_areas) / (1 - excrescense_leakage_fraction)
