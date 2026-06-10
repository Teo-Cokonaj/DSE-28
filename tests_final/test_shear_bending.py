import pytest
import aerosandbox.numpy as np
import math
import os
import sys
from scipy.interpolate import interp1d
from scipy.integrate import cumulative_trapezoid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import src_final.structural_analysis.wing_loading as wing_loading_module
from src_final.structural_analysis.Material import Material
from src_final.global_parameters import CONSTANTS
from src_final.Aircraft.Planform import Planform

from src_final.structural_analysis.wing_loading import WingModel

@pytest.fixture
def material():
    return Material(density=1000.0,
                        elastic_modulus=10e9,
                        shear_modulus=1e9,
                        poisson_ratio=0.3,
                        yield_strength=100e6,
                        fracture_strength=100e6
                        )

@pytest.fixture
def planform():
    return Planform(
        aspect_ratio=10.0,
        span=10.0,
        sweep_quarter_deg=0.0,
        taper=1.0,
        thickness_to_chord=0.1,
        cm_quarter_chord=1.0,
        wetted_surface_ratio=1.0,
        interference_factor=1.0,
        clmax=1.5,
        flap=False,
    )

@pytest.fixture
def wing_model(planform, material):
    model = WingModel(
            wing_skin_thickness_m =0.01,
            number_of_nodes=100,
            material_1 = material,
            planform = planform,
            load_factor=10.0,
            )

    wing_loading_module.planform = planform
    wing_loading_module.material_1 = material

    model.planform_data()
    model.force_per_unit(plot=False)

    return model

@pytest.fixture
def conservative_lift_distribution(planform, wing_model):
    return planform.estimate_conservative_lift_distribution(
                                                     diameter_fuselage=1.0,
                                                     positive_manoeuvring_limit_load_factor=10.0,
                                                     initial_total_aircraft_mass=100.0,
                                                     number_of_stations = wing_model.number_of_nodes)

@pytest.fixture
def reduced_sectional_spanwise_positions(conservative_lift_distribution):
    return conservative_lift_distribution[0]

@pytest.fixture
def modified_sectional_lifts_schrenk(conservative_lift_distribution):
    return conservative_lift_distribution[1]

@pytest.fixture
def test_torsion(planform, wing_model, reduced_sectional_spanwise_positions, modified_sectional_lifts_schrenk):
    return wing_model.step_torsion_determination(planform.sectional_properties(number_of_sections=wing_model.number_of_nodes)[0],planform.sectional_properties(number_of_sections=wing_model.number_of_nodes)[2],
                                                 reduced_sectional_spanwise_positions, modified_sectional_lifts_schrenk, plot = False)

class TestShearBending:
    def test_shear_stress(self, wing_model, planform):
        reduced_sectional_spanwise_positions = wing_model.span_poz
        modified_sectional_lifts_schrenk = wing_model.force_distribution

        # STEP 1: Shear stresses
        # Calculate the shear stresses with hard-coded values that can be traced back
        dummy_torsion = wing_model.step_torsion_determination(plot=False)
        c_stations, _, y_stations, _ = planform.sectional_properties(number_of_sections=wing_model.number_of_nodes)
        dummy_chord_lengths_cop = c_stations[-np.size(reduced_sectional_spanwise_positions):]
        dummy_cross_thickness_cop = dummy_chord_lengths_cop * planform.thickness_to_chord
        dummy_cross_sections_cop = np.pi * 0.5 * dummy_chord_lengths_cop * 0.5 * dummy_cross_thickness_cop
        dummy_skin_thickness = wing_model.wing_skin_thickness_m

        dummy_shear_stress_cop = dummy_torsion[-np.size(reduced_sectional_spanwise_positions):]/(2*dummy_skin_thickness*dummy_cross_sections_cop)
        dummy_shear_stress_int = interp1d(reduced_sectional_spanwise_positions,
                                          dummy_shear_stress_cop,
                                          kind="zero",
                                          fill_value="extrapolate")
        dummy_shear_stress = dummy_shear_stress_int(reduced_sectional_spanwise_positions)
        dummy_shear_stress = np.concatenate((np.full(np.size(c_stations) - np.size(dummy_shear_stress),
                                                     dummy_shear_stress[0]), dummy_shear_stress))

        # If fails, compare the cross-sections and shear stresses to see what went wrong
        print(f'Dummy cross section [m2]: {dummy_cross_sections_cop}')
        print(f'Dummy shear stress [Pa]: {dummy_shear_stress}')

        
        # STEP 2: Shear forces
        dummy_lift_forces = interp1d(reduced_sectional_spanwise_positions, modified_sectional_lifts_schrenk)
        dummy_y_stations = y_stations
        dummy_y_stations_cop = dummy_y_stations[-np.size(reduced_sectional_spanwise_positions):]
        dummy_lift_cont_cop = dummy_lift_forces(dummy_y_stations_cop)

        dummy_internal_shear_forces_cop = np.cumsum(dummy_lift_cont_cop[::-1])[::-1]


        dummy_internal_shear_forces_cop_int = interp1d(dummy_y_stations_cop, dummy_internal_shear_forces_cop,
                                                        kind="zero",
                                                        fill_value="extrapolate")

        dummy_shear_each_node = dummy_internal_shear_forces_cop_int(dummy_y_stations)
        dummy_shear_force = np.concatenate((np.full(np.size(dummy_y_stations) - np.size(dummy_shear_each_node),
                                                dummy_shear_each_node[0]), dummy_shear_each_node))
        
        print(f'Dummy shear force [N]: {dummy_shear_force}')
        
        # STEP 3: Bending moments
        #dummy_internal_bending_moments_cop = np.concatenate([[0], cumulative_trapezoid(dummy_internal_shear_forces_cop[::-1], dummy_y_stations_cop[::-1])])[::-1]
        dummy_y_stations_cop_fine = np.linspace(
            dummy_y_stations_cop[0],
            dummy_y_stations_cop[-1],
            len(dummy_y_stations_cop),
        )
        dummy_internal_shear_forces_cop_fine = dummy_internal_shear_forces_cop_int(
            dummy_y_stations_cop_fine
        )
        dummy_internal_bending_moments_cop = np.concatenate(
            [
                [0],
                cumulative_trapezoid(
                    dummy_internal_shear_forces_cop_fine[::-1],
                    dummy_y_stations_cop_fine[::-1],
                ),
            ]
        )[::-1]
        dummy_internal_bending_moments_int = interp1d(dummy_y_stations_cop,
                                     dummy_internal_bending_moments_cop,
                                     kind='zero',
                                     bounds_error=False,
                                     fill_value='extrapolate')
        
        dummy_internal_bending_moments_int = dummy_internal_bending_moments_int(dummy_y_stations)       
        
        # STEP 4: Run the actual functions to see if it computes the stresses correctly
        shear_stresses_test = wing_model.step_shear_stress(debug = False, plot = False)
        shear_forces_test = wing_model.step_shear_forces(debug = False, plot = False)
        bending_moments_test = wing_model.step_moment(debug = False, plot = False)


        print(f'Computed shear stress [Pa]: {shear_stresses_test}')

