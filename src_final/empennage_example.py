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

# ---------------------------------------------------------------------------
# Wing (light twin, ~22 m²)
# ---------------------------------------------------------------------------
wing = Planform(
    aspect_ratio              = 9.0,
    span                      = 14.0,       # m
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
print(f"Wing:  S = {wing.wing_area:.2f} m²   b = {wing.span:.2f} m   MAC = {wing.MAC:.3f} m")

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
# Example 1: conventional tail  (x_LE_canard = nan → TailFinder)
# ---------------------------------------------------------------------------
fixed_tail = Fixed(
    mass        = 6_000,        # kg
    x_cg        = 5.5,          # m from nose
    z_cg        = 0.5,
    x_LE_canard = np.nan,       # no canard
    x_LE_wing   = 4.5,
    x_LE_tail   = 10.5,
    x_nose_gear = 1.2,
    x_main_gear = 5.0,
    y_main_gear = 2.0,
    fuselage    = fuselage,
    nose_gear   = nose_gear,
    main_gear   = main_gear,
    gear_bay    = gear_bay,
    engine_bay  = engine_bay,
)

tail_stable   = EmpenageFinder.find_empenage(wing, fixed_tail, stable=True)
tail_unstable = EmpenageFinder.find_empenage(wing, fixed_tail, stable=False)

print(f"\n[Tail – stable (scissor plot, SM = {5}%)]")
print(f"  S_h   = {tail_stable.wing_area:.3f} m²")
print(f"  b_h   = {tail_stable.span:.3f} m")
print(f"  MAC_h = {tail_stable.MAC:.3f} m")

print(f"\n[Tail – unstable (FBW, volume coefficient)]")
print(f"  S_h   = {tail_unstable.wing_area:.3f} m²")
print(f"  b_h   = {tail_unstable.span:.3f} m")

# ---------------------------------------------------------------------------
# Example 2: canard  (x_LE_canard set → CanardFinder)
#   CG placed forward of wing AC for a canard-stable configuration
# ---------------------------------------------------------------------------
fixed_canard = Fixed(
    mass        = 6_000,
    x_cg        = 5.0,          # m from nose; wing AC is ~5.3 m, CG must be just forward
    z_cg        = 0.5,
    x_LE_canard = 1.5,          # m from nose
    x_LE_wing   = 4.5,
    x_LE_tail   = np.nan,       # no aft tail
    x_nose_gear = 1.2,
    x_main_gear = 5.0,
    y_main_gear = 2.0,
    fuselage    = fuselage,
    nose_gear   = nose_gear,
    main_gear   = main_gear,
    gear_bay    = gear_bay,
    engine_bay  = engine_bay,
)

canard_stable   = EmpenageFinder.find_empenage(wing, fixed_canard, stable=True)
canard_unstable = EmpenageFinder.find_empenage(wing, fixed_canard, stable=False)

print(f"\n[Canard – stable (max area for SM = {5}%)]")
print(f"  S_c   = {canard_stable.wing_area:.3f} m²")
print(f"  b_c   = {canard_stable.span:.3f} m")
print(f"  MAC_c = {canard_stable.MAC:.3f} m")

print(f"\n[Canard – unstable (FBW, volume coefficient)]")
print(f"  S_c   = {canard_unstable.wing_area:.3f} m²")
print(f"  b_c   = {canard_unstable.span:.3f} m")
