import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.Drag.LandingGear import LandingGear
from src.global_parameters import Assumptions, CONSTANTS
import aerosandbox.numpy as np

# Load assumptions from global_parameters
assumptions = Assumptions()

# Main gear params
D_main = float(assumptions.main_gear_diameter_wheel)
W_main = float(assumptions.main_gear_width_wheel)
height_main_strut = float(assumptions.main_gear_height_strut)
width_main_strut = float(assumptions.main_gear_width_strut)
main_enclosed_default = bool(assumptions.main_gear_enclosed)

# Nose gear params
D_nose = float(assumptions.nose_gear_diameter_wheel)
W_nose = float(assumptions.nose_gear_width_wheel)
height_nose_strut = float(assumptions.nose_gear_height_strut)
width_nose_strut = float(assumptions.nose_gear_width_strut)
nose_enclosed_default = bool(assumptions.nose_gear_enclosed)

mach_cruise = float(CONSTANTS.MACH_CRUISE)

main_gear_geometry = {
    'diameter_wheel': D_main,
    'width_wheel': W_main,
    'height_strut': height_main_strut,
    'width_strut': width_main_strut,
    'height_total': D_main / 2 + height_main_strut,
    'width_total': width_main_strut + W_main,
}

nose_gear_geometry = {
    'diameter_wheel': D_nose,
    'width_wheel': W_nose,
    'height_strut': height_nose_strut,
    'width_strut': width_nose_strut,
    'height_total': D_nose / 2 + height_nose_strut,
    'width_total': width_nose_strut + W_nose,
}

def pretty_print_geom(name: str, geom: dict):
    print(f"{name} geometry:")
    for k, v in geom.items():
        print(f"  {k}: {v}")


if __name__ == '__main__':
    pretty_print_geom('Main gear (from assumptions)', main_gear_geometry)
    pretty_print_geom('Nose gear (from assumptions)', nose_gear_geometry)

    # Instances: both enclosed and open for comparison
    main_open = LandingGear(main_gear_geometry, False)
    main_enclosed = LandingGear(main_gear_geometry, True)

    nose_open = LandingGear(nose_gear_geometry, False)
    nose_enclosed = LandingGear(nose_gear_geometry, True)

    print('\nComputed drag-area contributions (m^2):')
    print(f" Main open : {float(main_open.drag_area_contribution(mach_cruise))}")
    print(f" Main enclosed : {float(main_enclosed.drag_area_contribution(mach_cruise))}")
    print(f" Nose open : {float(nose_open.drag_area_contribution(mach_cruise))}")
    print(f" Nose enclosed : {float(nose_enclosed.drag_area_contribution(mach_cruise))}")

    print('\nInternal _drag_area values:')
    print(f" Main open _drag_area: {float(main_open._drag_area)}")
    print(f" Main enclosed _drag_area: {float(main_enclosed._drag_area)}")
    print(f" Nose open _drag_area: {float(nose_open._drag_area)}")
    print(f" Nose enclosed _drag_area: {float(nose_enclosed._drag_area)}")
