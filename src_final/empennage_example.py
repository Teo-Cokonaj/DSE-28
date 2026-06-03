import sys
import os
import numpy as np

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed
from Drag.Fuselage import Fuselage
from Drag.LandingGear import LandingGear
from Drag.Bay import Bay
from EmpenageSizing.EmpenageFinder import EmpenageFinder


def report(label, tail, canard, wing_area):
    print(f"\n{label}")
    if tail is not None:
        print(f"  tail   S_h/S = {tail.wing_area/wing_area:.4f}  "
              f"S_h = {tail.wing_area:.3f} m²  b_h = {tail.span:.3f} m  MAC_h = {tail.MAC:.3f} m")
    else:
        print("  tail   — not present")
    if canard is not None:
        print(f"  canard S_c/S = {canard.wing_area/wing_area:.4f}  "
              f"S_c = {canard.wing_area:.3f} m²  b_c = {canard.span:.3f} m  MAC_c = {canard.MAC:.3f} m")
    else:
        print("  canard — not present")


# ---------------------------------------------------------------------------
# Wing (~22 m², light twin)
# ---------------------------------------------------------------------------
wing = Planform(
    aspect_ratio=27.0, span=2.66, sweep_quarter_deg=15, taper=0.5,
    thickness_to_chord=0.12, cm_quarter_chord=-0.05,
    wetted_surface_ratio=2.05, interference_factor=1.0,
    clmax=1.5, flap=False, airfoil_lift_slope=2*np.pi, cl0=0.0,
)
print(f"Wing: S = {wing.wing_area:.2f} m²  MAC = {wing.MAC:.3f} m  (wing AC ~{4.5 + wing.aerodynamic_center(50):.3f} m from nose)")

# ---------------------------------------------------------------------------
# Shared fixed geometry
# ---------------------------------------------------------------------------
fuselage   = Fuselage(surface_wetted=1.11, length_total=2.5, diameter_max=0.2,
                      upsweep=0.00, base_area=0.005)
nose_gear  = LandingGear(wheel_width=0.025, exposed_height=0.1,
                         wheel_diameter=0.05, strut_width=0.015)
main_gear  = LandingGear(wheel_width=0.025, exposed_height=0.1,
                         wheel_diameter=0.05, strut_width=0.02)
gear_bay   = Bay(surface_wetted=0.1, length=0.2)
engine_bay = Bay(surface_wetted=0.15, length=0.3)

# ---------------------------------------------------------------------------
# 1. Tail-only  (x_LE_canard = nan)
#    CG at 5.5 m, wing LE at 4.5 m, tail LE at 10.5 m
# ---------------------------------------------------------------------------
fixed_tail = Fixed(
    mass=0.8, x_cg=2.8, z_cg=0.3,
    x_LE_canard=np.nan, x_LE_wing=1.25, x_LE_tail=2.6,
    x_nose_gear=0.2, x_main_gear=1.4, y_main_gear=0.15,
    fuselage=fuselage, nose_gear=nose_gear, main_gear=main_gear,
    gear_bay=gear_bay, engine_bay=engine_bay,
)

report("[Tail-only – stable   SM = 5%]",
       *EmpenageFinder.find_empenage(wing, fixed_tail, stable=True),  wing.wing_area)
report("[Tail-only – unstable SM = 0%]",
       *EmpenageFinder.find_empenage(wing, fixed_tail, stable=False), wing.wing_area)

# ---------------------------------------------------------------------------
# 2. Canard-only  (x_LE_tail = nan)
#    CG must be just forward of wing AC (~5.3 m)
# ---------------------------------------------------------------------------
fixed_canard = Fixed(
    mass=0.45, x_cg=0.2, z_cg=-0.2,
    x_LE_canard=0.25, x_LE_wing=1.25, x_LE_tail=np.nan,
    x_nose_gear=0.1, x_main_gear=1.5, y_main_gear=0,
    fuselage=fuselage, nose_gear=nose_gear, main_gear=main_gear,
    gear_bay=gear_bay, engine_bay=engine_bay,
)

 #report("[Canard-only – stable   SM = 5% (max S_c/S)]",
       #*EmpenageFinder.find_empenage(wing, fixed_canard, stable=True),  wing.wing_area)
#report("[Canard-only – unstable SM = 0% (max S_c/S at neutral)]",
       #*EmpenageFinder.find_empenage(wing, fixed_canard, stable=False), wing.wing_area)

# ---------------------------------------------------------------------------
# 3. Three-surface  (both set)
#    Canard pinned by volume coefficient; tail sized by scissor plot
# ---------------------------------------------------------------------------
fixed_three = Fixed(
    mass=1.25, x_cg=1.25, z_cg=0,
    x_LE_canard=0.25, x_LE_wing=1.25, x_LE_tail=2.6,
    x_nose_gear=0.1, x_main_gear=1.5, y_main_gear=0,
    fuselage=fuselage, nose_gear=nose_gear, main_gear=main_gear,
    gear_bay=gear_bay, engine_bay=engine_bay,
)

report("[Three-surface – stable   SM = 5%]",
       *EmpenageFinder.find_empenage(wing, fixed_three, stable=True),  wing.wing_area)
report("[Three-surface – unstable SM = 0%]",
       *EmpenageFinder.find_empenage(wing, fixed_three, stable=False), wing.wing_area)
