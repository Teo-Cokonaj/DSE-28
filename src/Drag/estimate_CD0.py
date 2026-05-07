import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Drag.Component import Component

def estimate_CD0(components:list[Component], altitude:float, mach:float):
    surface_wetted_total = sum([component.surface_wetted for component in components])
    return sum([component.surface_wetted*component.CD0_comp(altitude, mach) for component in components]) / surface_wetted_total