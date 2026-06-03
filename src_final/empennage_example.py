import sys
import os
import numpy as np

# Run from anywhere: add src_final/ to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed
from Drag.Fuselage import Fuselage
from Drag.LandingGear import LandingGear
from Drag.Bay import Bay
from EmpenageSizing.EmpenageFinder import EmpenageFinder

def print_surface(label, planform):
    if planform is None:
        print(f"  {label}: not present")
    else:
        print(f"  {label}: S={planform.wing_area:.3f} m²  b={planform.span:.3f} m  MAC={planform.MAC:.3f} m")

# ---------------------------------------------------------------------------
# Wing (light twin, ~22 m²)
# ---------------------------------------------------------------------------
wing = Planform(
    aspect_ratio              = 9.0,
    span                      = 14.0,
    sweep_quarter_deg         = 5.0,
    taper                     = 0.45,
    thickness_to_chord        = 0.14,
    cm_quarter_chord          = -0.05,
    wetted_surface_ratio      = 2.05,
    interference_factor       = 1.0,
    clmax                     = 1.8,
    flap                      = True,
    airfoil_lift_slope        = 2 * np.pi,
    cl0                       = 0.2,
)
print(f"Wing:  S={wing.wing_area:.2f} m²  b={wing.span:.2f} m  MAC={wing.MAC:.3f} m\n")

# ---------------------------------------------------------------------------
# Shared fuselage / gear / bay components
# ---------------------------------------------------------------------------
fuselage   = Fuselage(surface_wetted=65.0, length_total=12.0, diameter_max=1.5,
                      upsweep=0.08, base_area=0.05)
nose_gear  = LandingGear(wheel_width=0.10, exposed_height=0.45,
                         wheel_diameter=0.40, strut_width=0.06)
main_gear  = LandingGear(wheel_width=0.15, exposed_height=0.55,
                         wheel_diameter=0.50, strut_width=0.08)
gear_bay   = Bay(surface_wetted=0.8, length=0.6)
engine_bay = Bay(surface_wetted=1.2, length=1.0)

# ---------------------------------------------------------------------------
# Example 1: tail only  (x_LE_canard = nan → TailFinder)
# ---------------------------------------------------------------------------
fixed_tail = Fixed(
    mass=6_000, x_cg=5.5, z_cg=0.5,
    x_LE_canard=np.nan, x_LE_wing=4.5, x_LE_tail=10.5,
    x_nose_gear=1.2, x_main_gear=5.0, y_main_gear=2.0,
    fuselage=fuselage, nose_gear=nose_gear, main_gear=main_gear,
    gear_bay=gear_bay, engine_bay=engine_bay,
)

tail, canard = EmpenageFinder.find_empenage(wing, fixed_tail, stable=True)
print("[Tail only – stable (scissor plot)]")
print_surface("tail  ", tail)
print_surface("canard", canard)

tail, canard = EmpenageFinder.find_empenage(wing, fixed_tail, stable=False)
print("\n[Tail only – unstable (FBW)]")
print_surface("tail  ", tail)
print_surface("canard", canard)

# ---------------------------------------------------------------------------
# Example 2: canard only  (x_LE_tail = nan → CanardFinder)
#   CG must be just forward of wing AC (~5.3 m)
# ---------------------------------------------------------------------------
fixed_canard = Fixed(
    mass=6_000, x_cg=5.0, z_cg=0.5,
    x_LE_canard=1.5, x_LE_wing=4.5, x_LE_tail=np.nan,
    x_nose_gear=1.2, x_main_gear=5.0, y_main_gear=2.0,
    fuselage=fuselage, nose_gear=nose_gear, main_gear=main_gear,
    gear_bay=gear_bay, engine_bay=engine_bay,
)

tail, canard = EmpenageFinder.find_empenage(wing, fixed_canard, stable=True)
print("\n[Canard only – stable (scissor plot)]")
print_surface("tail  ", tail)
print_surface("canard", canard)

tail, canard = EmpenageFinder.find_empenage(wing, fixed_canard, stable=False)
print("\n[Canard only – unstable (FBW)]")
print_surface("tail  ", tail)
print_surface("canard", canard)

# ---------------------------------------------------------------------------
# Example 3: three-surface  (both x_LE_canard and x_LE_tail set)
#   Canard sized by volume coefficient; tail solved from stability equation
# ---------------------------------------------------------------------------
fixed_three = Fixed(
    mass=6_000, x_cg=5.5, z_cg=0.5,
    x_LE_canard=1.5, x_LE_wing=4.5, x_LE_tail=10.5,
    x_nose_gear=1.2, x_main_gear=5.0, y_main_gear=2.0,
    fuselage=fuselage, nose_gear=nose_gear, main_gear=main_gear,
    gear_bay=gear_bay, engine_bay=engine_bay,
)

tail, canard = EmpenageFinder.find_empenage(wing, fixed_three, stable=True)
print("\n[Three-surface – stable (canard: vol-coeff, tail: scissor plot)]")
print_surface("tail  ", tail)
print_surface("canard", canard)

tail, canard = EmpenageFinder.find_empenage(wing, fixed_three, stable=False)
print("\n[Three-surface – unstable (both: vol-coeff)]")
print_surface("tail  ", tail)
print_surface("canard", canard)
