import pytest
import aerosandbox.numpy as np
import math
import os
import sys
from scipy.interpolate import interp1d

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    return WingModel(
            wing_leng_m=10,
            wing_skin_thickness_m =0.01,
            number_of_nodes=100,
            material_1 = material,
            material_2 = material,
            planform = planform,
            wing_tip_choad_m = 0.1,
            wing_root_chord_m = 0.1
            )

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
                                                 reduced_sectional_spanwise_positions, modified_sectional_lifts_schrenk)

class TestShearBending:
    def test_shear_stress(self, wing_model, planform, reduced_sectional_spanwise_positions, modified_sectional_lifts_schrenk, test_torsion):

        # STEP 1: Shear stresses
        # Calculate the shear stresses with hard-coded values that can be traced back
        dummy_torsion = test_torsion
        print(f'Dummy torsion: {dummy_torsion}')
        dummy_chord_length = 1.0
        dummy_cross_thickness = dummy_chord_length * planform.thickness_to_chord
        dummy_cross_section = np.pi * 0.5 * dummy_chord_length * 0.5 * dummy_cross_thickness
        dummy_skin_thickness = 0.01

        dummy_shear_stress = dummy_torsion/(2*dummy_skin_thickness*dummy_cross_section)

        # If fails, compare the cross-sections and shear stresses to see what went wrong
        print(f'Dummy cross section [m2]: {dummy_cross_section}')
        print(f'Dummy shear stress [Pa]: {dummy_shear_stress}')

        
        # STEP 2: Shear forces
        dummy_lift_forces = interp1d(reduced_sectional_spanwise_positions, modified_sectional_lifts_schrenk)
        _, _, dummy_y_stations, _ = planform.sectional_properties(number_of_sections=wing_model.number_of_nodes)
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
        

        
        # STEP 4: Run the actual functions to see if it computes the stresses correctly
        shear_stresses_test = WingModel.step_shear_stress(wing_model, reduced_sectional_spanwise_positions,
                                    modified_sectional_lifts_schrenk, debug = False, plot = False)
        shear_forces_test = WingModel.step_shear_forces(wing_model, reduced_sectional_spanwise_positions, modified_sectional_lifts_schrenk,
                                                        debug = False, plot = False)
        bending_moments_test = WingModel.step_moment(wing_model, debug = False, plot = False)


        print(f'Computed shear stress [Pa]: {shear_stresses_test}')
        print(f'Computed shear force [N]: {shear_forces_test}')
        print(f'Computed bending moment [Nm]: {bending_moments_test}')

        assert np.allclose(dummy_shear_stress, shear_stresses_test, 1e-6, 1e-6)
        assert np.allclose(dummy_shear_force, shear_forces_test, 1e-6, 1e-6)
        assert 1>2


