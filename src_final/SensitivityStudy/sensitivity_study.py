import os
import sys
import pickle
import numpy as np
from numba import njit
import itertools as itt
import aerosandbox as asb
import pathlib
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed
from Drag.Fuselage import Fuselage
from Drag.Bay import Bay
from Drag.LandingGear import LandingGear
from Aircraft.Aircraft import Aircraft
from global_parameters import Assumptions
from Requirements.FuelReq import FuelReq
from Requirements.LGReq import LGReq
from Requirements.MassReq import MassReq
from Requirements.MDReq import MDReq
from Requirements.EmpennageReq import EmpennageReq
from Requirements.Requirement import Requirement
from EmpennageSizing.TailFinder import TailFinder
from EmpennageSizing.CanardFinder import CanardFinder
from structural_analysis.iterative_planform_sizing import size_planform, Material

assumptions = Assumptions()

#TODO load the fuselage here
#with open("../notebooks/pickles/fixed_pickle.pcl", "rb") as f:
    #fixed: Fixed = pickle.load(f)

_HERE = pathlib.Path(__file__).parent
pickle_path = _HERE / ".." / "notebooks" / "pickles" / "fixed_pickle.pcl"

with open(pickle_path, "rb") as f:
    fixed: Fixed = pickle.load(f)

fixed.x_LE_wing = 1.255
delta_z = 0.01
fixed.z_tail_cone += delta_z
fixed.z_cg += delta_z
fixed.fuel_mass = 13.54
fixed.x_cg_min = 1.378 #m #1.381
fixed.x_cg_max = 1.381 #m # 1.378
fixed.mass = 40.782#kg 
fixed.fuselage.diameter_max = 0.315

for component in fixed.drag_components(False):
    component.add_cache_entry("go_around", assumptions.airspeed_approach/asb.Atmosphere(assumptions.altitude_go_round).speed_of_sound(), assumptions.altitude_go_round)
    component.add_cache_entry("mach_max", assumptions.mach_max, assumptions.altitude_mach_max)
    component.add_cache_entry("cruise", assumptions.mach_cruise, assumptions.altitude_cruise)
for component in fixed.drag_components(True):
    component.add_cache_entry("takeoff", assumptions.airspeed_approach/asb.Atmosphere().speed_of_sound(), 0.)


standard_wing = Planform(aspect_ratio=27, span=3.4, sweep_quarter_deg=15., taper=.3, thickness_to_chord=0.12, cm_quarter_chord=0,
                         wetted_surface_ratio=1.07, interference_factor=1.0, clmax=1.22, flap=False)

material_skin = Material(assumptions.cfrp_density, elastic_modulus=assumptions.cfrp_Young_modulus, 
                         poisson_ratio=assumptions.cfrp_poisson, shear_modulus=assumptions.cfrp_Young_modulus / 2 / (1 + assumptions.cfrp_poisson),
                         yield_strength=assumptions.cfrp_yield_strength, fracture_strength=assumptions.cfrp_yield_strength)

fuselage_diameter = fixed.fuselage.diameter_max
size_planform(planform=standard_wing, 
              thicknesses=assumptions.allowable_thicknesses, 
              fuselage_diameter=fuselage_diameter, 
              material_skin=material_skin, 
              density_core=assumptions.foam_denisty, 
              #safety_factor,
              ) 


go_around_atmosphere = asb.Atmosphere(assumptions.altitude_go_round)
sea_level_atmosphere = asb.Atmosphere()

standard_wing.add_cache_entry('cruise', assumptions.mach_cruise, assumptions.altitude_cruise)
standard_wing.add_cache_entry('mach_max', assumptions.mach_max, assumptions.altitude_mach_max)
#NOTE: not fully technically correct but prevents coupling which would be problematic, acceptable as CD0 dept. on mach is small @ low mach
standard_wing.add_cache_entry('go_around', assumptions.airspeed_approach / go_around_atmosphere.speed_of_sound(), assumptions.altitude_go_round)
standard_wing.add_cache_entry('takeoff', assumptions.airspeed_approach / sea_level_atmosphere.speed_of_sound(), 0.)

standard_wing.mass_cache = 3.
standard_wing.x_cg_cache = 0.2



def AR_variation(AR_min: float = 0.5,
                 AR_max: float = 10,
                 dAR: float = 0.5,
                 surface: str = "tail",
                 ):

    requirements = [MassReq(50.), MDReq(), FuelReq(), LGReq(), EmpennageReq()]
    requirement_labels = ["MTOM", "Matching Diagram", "Fuel", "Landing Gear", "Empennage"]

    ARs = np.arange(AR_min, AR_max + dAR, dAR)
    AR_mass_list = []
    AR_req_list = []

    for AR in ARs:

        if surface == "tail":
            surfaces = TailFinder(fixed, 
                                  material=material_skin, 
                                  core_density=assumptions.foam_denisty,
                                  thicknesses=assumptions.allowable_thicknesses,
                                  safety_factor=assumptions.structural_safety_factor,
                                  AR_h=AR,                                                                  
                                  taper_h=.7, 
                                  taper_v=.8).find_planforms(standard_wing)
            
        elif surface == "canard":
            surfaces = CanardFinder(fixed, 
                                    material=material_skin, 
                                    core_density=assumptions.foam_denisty,
                                    thicknesses=assumptions.allowable_thicknesses,
                                    safety_factor=assumptions.structural_safety_factor,
                                    AR_c=AR,                                                                 
                                    taper_c=.7, 
                                    taper_v=.8).find_planforms(standard_wing)
            
        else:
            raise ValueError(f"surface must be 'tail' or 'canard', got '{surface}'")

        for s in surfaces:
            s.add_cache_entry('cruise', assumptions.mach_cruise, assumptions.altitude_cruise)
            s.add_cache_entry('mach_max', assumptions.mach_max, assumptions.altitude_mach_max)
            s.add_cache_entry('go_around', assumptions.airspeed_approach / go_around_atmosphere.speed_of_sound(), assumptions.altitude_go_round)
            s.add_cache_entry('takeoff', assumptions.airspeed_approach / sea_level_atmosphere.speed_of_sound(), 0.)

        ac = Aircraft(fixed, [standard_wing] + surfaces)
        AR_mass_list.append((float(AR), float(ac.total_mass())))
        AR_req_list.append({
            "AR": float(AR),
            **{label: requirement.assess(ac) for requirement, label in zip(requirements, requirement_labels)}
        })

    AR_mass_array = np.array(AR_mass_list)

    return AR_mass_array, AR_req_list



def SF_variation(SF_min: float = 1.0,
                 SF_max: float = 2.5,
                 dSF: float = 0.1,
                 ):

    requirements = [MassReq(50.), MDReq(), FuelReq(), LGReq(), EmpennageReq()]
    requirement_labels = ["MTOM", "Matching Diagram", "Fuel", "Landing Gear", "Empennage"]

    SFs = np.arange(SF_min, SF_max + dSF, dSF)
    SF_mass_list = []
    SF_req_list = []

    for SF in SFs:
        size_planform(planform=standard_wing, 
                      thicknesses=assumptions.allowable_thicknesses, 
                      fuselage_diameter=fuselage_diameter,
                      material_skin=material_skin, 
                      density_core=assumptions.foam_denisty, 
                      safety_factor=SF)
        
        tail = TailFinder(fixed, 
                                  material=material_skin, 
                                  core_density=assumptions.foam_denisty,
                                  thicknesses=assumptions.allowable_thicknesses,
                                  safety_factor=SF,
                                  AR_h=3,                                                                       # might not need to be hardcoded...
                                  taper_h=.7, 
                                  taper_v=.8).find_planforms(standard_wing)
        
        canard = CanardFinder(fixed, 
                                    material=material_skin, 
                                    core_density=assumptions.foam_denisty,
                                    thicknesses=assumptions.allowable_thicknesses,
                                    safety_factor=SF,
                                    AR_c=3,                                                                     # might not need to be hardcoded...
                                    taper_c=.7, 
                                    taper_v=.8).find_planforms(standard_wing)
        
        for s in tail + canard:
                s.add_cache_entry('cruise', assumptions.mach_cruise, assumptions.altitude_cruise)
                s.add_cache_entry('mach_max', assumptions.mach_max, assumptions.altitude_mach_max)
                s.add_cache_entry('go_around', assumptions.airspeed_approach / go_around_atmosphere.speed_of_sound(), assumptions.altitude_go_round)
                s.add_cache_entry('takeoff', assumptions.airspeed_approach / sea_level_atmosphere.speed_of_sound(), 0.)

        ac_tail = Aircraft(fixed, [standard_wing] + tail)
        ac_canard = Aircraft(fixed, [standard_wing] + canard)

        SF_mass_list.append((float(SF), float(ac_tail.total_mass()), float(ac_canard.total_mass())))
        SF_req_list.append({
            "SF": float(SF),
            **{f"tail_{label}": bool(requirement.assess(ac_tail)) for requirement, label in zip(requirements, requirement_labels)},
            **{f"canard_{label}": bool(requirement.assess(ac_canard)) for requirement, label in zip(requirements, requirement_labels)},
        })

    SF_mass_array = np.array(SF_mass_list)

    return SF_mass_array, SF_req_list


if __name__ == "__main__":

    SF_mass_array, SF_req_list = SF_variation()
    tail_sensitivity, tail_reqs = AR_variation(surface="tail")
    canard_sensitivity, canard_reqs = AR_variation(surface="canard")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(SF_mass_array[:, 0], SF_mass_array[:, 1], label="Tail")
    ax1.plot(SF_mass_array[:, 0], SF_mass_array[:, 2], label="Canard")
    ax1.set_xlabel("Wing weight to wing structural weight ratio")
    ax1.set_ylabel("Total mass in the standard planform configuration [kg]")
    ax1.set_title("Safety factor sensitivity — MTOM")
    ax1.legend()

    ax2.plot(tail_sensitivity[:, 0], tail_sensitivity[:, 1], label="Tail")
    ax2.plot(canard_sensitivity[:, 0], canard_sensitivity[:, 1], label="Canard")
    ax2.set_xlabel("Empennage Aspect Ratio")
    ax2.set_ylabel("Total mass in the standard planform configuration [kg]")
    ax2.set_title("AR Sensitivity — MTOM")
    ax2.legend()

    plt.tight_layout()
    plt.show()

    for entry in SF_req_list:
        failed = [k for k, v in entry.items() if k != "SF" and not v]
        if failed:
            print(f"SF={entry['SF']:.2f} failed: {failed}")

    for entry in tail_reqs:
        failed = [k for k, v in entry.items() if k != "AR" and not v]
        if failed:
            print(f"Tail AR={entry['AR']:.1f} failed: {failed}")

    for entry in canard_reqs:
        failed = [k for k, v in entry.items() if k != "AR" and not v]
        if failed:
            print(f"Canard AR={entry['AR']:.1f} failed: {failed}")