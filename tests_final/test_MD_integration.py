import sys
import os
import numpy as np
import aerosandbox as asb
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src_final.Aircraft.Aircraft import Aircraft
from src_final.Aircraft.Planform import Planform
from src_final.Aircraft.Fixed import Fixed
from src_final.Requirements.MDReq import MDReq
from src_final.MatchingDiagram.MatchingDiagramJet import MatchingDiagramJet
from src_final.global_parameters import CONSTANTS, Assumptions

wing = Planform(
    aspect_ratio=27.0,
    span=4.0,
    sweep_quarter_deg=14.33,
    taper=0.5,
    thickness_to_chord=0.12,
    cm_quarter_chord=-0.05,
    wetted_surface_ratio=18,
    interference_factor=1.0,
    clmax=1.22,
    flap=False
)

canard = Planform(
    aspect_ratio=5,
    span=1.0,
    sweep_quarter_deg=13,
    taper=0.5,
    thickness_to_chord=0.12,
    cm_quarter_chord=-0.05,
    wetted_surface_ratio=2,
    interference_factor=1.1,
    clmax=0.8,
    flap=False
)

empennage = Planform(
    aspect_ratio=4,
    span=2.5,
    sweep_quarter_deg=14,
    taper=0.5,
    thickness_to_chord=0.12,
    cm_quarter_chord=0,
    wetted_surface_ratio=2.5,
    interference_factor=1.04,
    clmax=1.0,
    flap=False
)

# Add mass caches
wing.mass_cache = 5.0
canard.mass_cache = 1.0
empennage.mass_cache = 2.0


planforms = [wing, canard, empennage]

fixed = Fixed(
    mass=40,
    fuel_mass=15,
    x_cg_min=0, 
    x_cg_max=0, 
    x_tail_cone=0, 
    z_cg=0, 
    z_tail_cone=0, 
    z_wing=0, 
    x_LE_canard=0, 
    x_LE_wing=0, 
    x_LE_tail=0, 
    x_nose_gear=0, 
    x_main_gear=0, 
    y_main_gear=0, 
    fuselage=None, 
    nose_gear=None, 
    main_gear=None, 
    gear_bay=None, 
    engine_bay=None
)

aircraft = Aircraft(
    fixed=fixed,
    planforms=planforms
)
# Hardcode CD0 dummy values 
aircraft.CD0_mach_max = 0.024
aircraft.CD0_cruise = 0.023
aircraft.CD0_takeoff = 0.028
aircraft.CD0_go_around = 0.023

matching_diagram = MatchingDiagramJet(n_engines=2)

assumptions = Assumptions()

results = MDReq().assess(aircraft, wing, fixed, matching_diagram, assumptions)
for label, passed in results.items():
    print(f"{label}: {'PASS' if passed else 'FAIL'}")

#print(wing.oswald)
#print(wing.inviscid_ratio)