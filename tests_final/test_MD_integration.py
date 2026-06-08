import sys
import os
import numpy as np
import aerosandbox as asb
import pickle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src_final.Drag.Fuselage import Fuselage
from src_final.Drag.Bay import Bay
from src_final.Drag.LandingGear import LandingGear
from src_final.Aircraft.Aircraft import Aircraft
from src_final.Aircraft.Planform import Planform
from src_final.Aircraft.Fixed import Fixed
from src_final.Requirements.MDReq import MDReq
from src_final.MatchingDiagram.MatchingDiagramJet import MatchingDiagramJet
from src_final.global_parameters import CONSTANTS, Assumptions

with open("src_final/notebooks/pickles/planform_pickle_official.pcl", "r+b") as f:
    plaforms_recovered:list[tuple[Planform, str, bool]] = pickle.load(f)

assumptions = Assumptions()

#TODO load the fuselage here
main_gear_bay = Bay(surface_wetted=np.pi*0.02*0.5, length=0.5, diameter=0.02)
engine_bay = Bay(surface_wetted=np.pi*0.02*0.5, length=0.5, diameter=0.02)
main_gear = LandingGear(wheel_width=assumptions.main_gear_width_wheel, exposed_height=0.02, wheel_diameter=0.03, strut_width=0.01)
nose_gear = LandingGear(wheel_width=assumptions.main_gear_width_wheel, exposed_height=0.02, wheel_diameter=0.03, strut_width=0.01)
fuselage = Fuselage(surface_wetted=np.pi*0.03*3.4, length_total=3.4, diameter_max=0.03, upsweep=np.pi/12, base_area=np.pi/4*0.007**2)
fixed = Fixed(mass=25., fuel_mass=10., x_cg_min=1.6, x_cg_max=2., x_tail_cone=2.3, z_cg=0.04, z_tail_cone=0.02, z_wing=0.05, x_LE_canard=0.01,
              x_LE_wing=1.6, x_LE_tail=3.25, x_nose_gear=0.1, x_main_gear=1.8, y_main_gear=0.02, fuselage=fuselage, nose_gear=nose_gear,
              main_gear=main_gear, gear_bay=main_gear_bay, engine_bay=engine_bay)

for component in fixed.drag_components(False):
    component.add_cache_entry("go_around", assumptions.airspeed_approach/asb.Atmosphere(assumptions.altitude_go_round).speed_of_sound(), assumptions.altitude_go_round)
    component.add_cache_entry("mach_max", assumptions.mach_max, assumptions.altitude_mach_max)
    component.add_cache_entry("cruise", assumptions.mach_cruise, assumptions.altitude_cruise)
for component in fixed.drag_components(True):
    component.add_cache_entry("takeoff", assumptions.airspeed_approach/asb.Atmosphere().speed_of_sound(), 0.)

aircraft:list[Aircraft] = list()

for planform_recovered in plaforms_recovered:
    main_wing = planform_recovered[0]
    planform_type = planform_recovered[1]
    
    # Add cache entries for the planforms
    main_wing.add_cache_entry("go_around", assumptions.airspeed_approach/asb.Atmosphere(assumptions.altitude_go_round).speed_of_sound(), assumptions.altitude_go_round)
    main_wing.add_cache_entry("mach_max", assumptions.mach_max, assumptions.altitude_mach_max)
    main_wing.add_cache_entry("cruise", assumptions.mach_cruise, assumptions.altitude_cruise)
    main_wing.add_cache_entry("takeoff", assumptions.airspeed_approach/asb.Atmosphere().speed_of_sound(), 0.)

    aircraft_planforms = [main_wing, ] #TODO add the empennage
    aircraft.append(Aircraft(
        fixed=fixed, #TODO: add the fuselage from CAD
        planforms=aircraft_planforms 
    ))

matching_diagram = MatchingDiagramJet(n_engines=2)

passing = []

for i, ac in enumerate(aircraft):
    matching_diagram = MatchingDiagramJet(n_engines=2)
    results = MDReq(matching_diagram, assumptions).assess(ac)
    print(f"\nAircraft {i}:")
    for label, passed in results.items():
        print(f"  {label}: {'PASS' if passed else 'FAIL'}")
    
    print(f"  Wing loading: {ac.wing_loading():.2f} N/m²")
    print(f"  Thrust to weight: {ac.thrust_to_weight():.4f}")

    print(f"  W/S constraints:")
    for label, ws_limit in matching_diagram.constraints_wing_loading.items():
        print(f"    {label}: {ws_limit:.2f} N/m²")

    print(f"  T/W constraints at actual W/S:")
    for label, tw_curve in matching_diagram.constraints_thrust_weight.items():
        print(f"    {label}: {tw_curve(ac.wing_loading()):.4f}")

    if all(results.values()):
        passing.append(i)

print(f"\nAircraft satisfying all constraints: {passing}")
