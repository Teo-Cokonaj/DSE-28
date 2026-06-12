import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import math
from scipy.optimize import root_scalar
from scipy.integrate import cumulative_trapezoid
from scipy.interpolate import interp1d
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))
from scipy.interpolate import interp1d


from src_final.structural_analysis.Material import Material
from src_final.global_parameters import CONSTANTS
from src_final.Aircraft.Planform import Planform
from src_final.structural_analysis.wing_loading import WingModel

def find_planform_thickness(planform:Planform, thicknesses:list[float], fuselage_diameter:float, material:Material, load_factor:float=6., load_factor_maneuver:float=1.) -> float:
    for thickness in thicknesses:
        wing_model= WingModel(
                    wing_skin_thickness_m = thickness,
                    number_of_nodes=100,
                    material_1 = material,
                    planform = planform,
                    load_factor = load_factor,
                    inertial_load=1.,
                    cm=planform.cm_quarter_chord,
                    V=200.,
                    local_fuselage_diameter=fuselage_diameter
                    )
        wing_model.planform_data(diameter_fuselage=fuselage_diameter)
        plot_1 = False

        force_distribution, lift, weight = wing_model.force_per_unit(plot=plot_1)

        torque = wing_model.step_torsion_determination(plot=plot_1)

        shear_force = wing_model.step_shear_forces(debug=False, plot=plot_1)

        bending_moment = wing_model.step_moment(debug=False, plot=plot_1)

        twist_rad, twist_deg = wing_model.step_rotation_of_wing(
            torsion=torque,
            plot=plot_1
        )

        slope_rad, deflection_m = wing_model.step_vertical_deflection(
            plot=plot_1,
            moments=bending_moment
        )

        # crushing_pressure = wing_model.step_crushing_pressure(
        #     moments=bending_moment
        # )

        shear_stress = wing_model.step_shear_stress_total(
            debug=False,
            plot=plot_1
        )

        buckling_stress = wing_model.buckling_model()
        are_we_buckling = wing_model.wing_stres_per_com()
        normal_stress = wing_model.bending_stresses()

        print(f"Stresses {np.max(shear_stress)}, {np.max(np.abs(normal_stress))}, {thickness}")

        if (np.max(shear_stress) < material.fracture_strength / 3) and (np.any(are_we_buckling) > 0) and (np.max(np.abs(normal_stress)) < material.fracture_strength / 1.5) and (np.max(np.abs(twist_deg))<10.) and (np.max(np.abs(deflection_m)) < .15*planform.span):
            return thickness
        
    raise ValueError("None of the provided material thicknesses satisfy the constraints")


def find_planform_mass_cg(planform:Planform, thickness:float, density_core:float, density_skin:float, number_of_sections:int=20, safety_factor = 1.5)->tuple[float, float]:
    
    chord_boundary, chord_stations, y_boundary, dy = planform.sectional_properties(number_of_sections)

    y_stations = .5 * (y_boundary[1:] + y_boundary[:-1])
    
    x_cg_stations = planform.c_root / 2 + np.tan(planform.sweep_half_rad) * y_stations
    crossec_area_stations = np.pi * chord_stations**2 * planform.thickness_to_chord

    h_ellipse = ((1 - planform.thickness_to_chord) / (1 + planform.thickness_to_chord))**2
    p_ellispse_to_chord = np.pi * (1 + planform.thickness_to_chord) * (1 + 3 * h_ellipse / (10 + np.sqrt(4 - 3 * h_ellipse)))
    crossec_perimeter_stations = p_ellispse_to_chord * chord_stations

    masses_core_stations = crossec_area_stations * dy * density_core
    masses_skin_stations = crossec_perimeter_stations * thickness * dy * density_skin
    masses_tot_stations = (masses_core_stations + masses_skin_stations) * safety_factor

    mass_tot = np.sum(masses_tot_stations)

    return mass_tot * 2, np.sum(masses_tot_stations * x_cg_stations) / mass_tot #NOTE: 2 accounts for the fact we have a wing on each side of the fuselage


def size_planform(planform:Planform, thicknesses:list[float], fuselage_diameter:float, material_skin:Material, density_core:float, number_of_sections = 20, safety_factor = 1.5, load_factor=1., load_factor_maneuver=6.) -> None:
    '''Updates theplanform mass and cg caches'''
    thickness = find_planform_thickness(planform, thicknesses, fuselage_diameter, material_skin, load_factor, load_factor_maneuver)
    pf_mass, pf_x_cg = find_planform_mass_cg(planform, thickness, density_core, material_skin.density, number_of_sections, safety_factor)
    planform.mass_cache = pf_mass
    planform.x_cg_cache = pf_x_cg


if __name__ == "__main__":
    planform = Planform(
            aspect_ratio=27.0,
            span=2.67,
            sweep_quarter_deg=15,
            taper=0.5,
            thickness_to_chord=0.12,
            cm_quarter_chord=1.0,
            wetted_surface_ratio=1.0,
            interference_factor=1.0,
            clmax=1.5,
            flap=False,
        )
    
    material_skin = Material(density=1570,
                            elastic_modulus=69e9,
                            shear_modulus=5.58e9,
                            poisson_ratio=0.048,
                            yield_strength=600e6,
                            fracture_strength=600e6
        )
    
    thicknesses = np.linspace(0.0004, 0.004, 30)
    dfus = 0.33
    print(find_planform_thickness(planform, thicknesses, dfus, material_skin))
    
    size_planform(planform, thicknesses=thicknesses, fuselage_diameter=dfus, material_skin=material_skin, density_core=200.)
    

    print(planform.mass_cache, planform.x_cg_cache)
