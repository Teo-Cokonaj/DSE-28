import pytest
import copy
import aerosandbox as asb
import numpy as np
import numpy.testing as nte
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src_final.global_parameters import CONSTANTS, Assumptions
from src_final.Aircraft.Planform import Planform
from src_final.structural_analysis.Material import Material
from src_final.structural_analysis.fuselage_loading_model_cylinder import FuselageModel
from src_final.global_parameters import CONSTANTS
from scipy.interpolate import interp1d
from scipy.integrate import cumulative_trapezoid

@pytest.fixture
def material():
    return Material(density=1600.0,
                            elastic_modulus=70e9,
                            shear_modulus=5e9,
                            poisson_ratio=0.3,
                            yield_strength=600e6,
                            fracture_strength=600e6
                            )

@pytest.fixture
def fuselage_model(material):
    return   FuselageModel(
                 fuselage_length_m=3.0,
                 fuselage_diameter_m= 0.3,
                 minimum_fuselage_thickness_mm=1e-6,
                 material=material,
                 main_wing_position_m=1.0,
                 main_wing_mass_kg=10.0,
                 horizontal_tail_position_m=3.0,
                 horizontal_tail_mass_kg=3.0,
                 landing_gear_position_m=1.5,
                 landing_gear_mass_kg=3.0,
                 number_of_nodes=1000,
                 canard_position_m=0.2,
                 canard_mass_kg=1.0,
                 canard_lift_fraction=0.20,             
                 )


class TestFuselageModel:
    def test_create_nodes(self,
                          fuselage_model):
        fuselage_model.create_nodes()

        reference_nodes=np.linspace(0.0,
                                    fuselage_model.fuselage_length_m,
                                    fuselage_model.number_of_nodes)
        np.testing.assert_allclose(fuselage_model.nodes,reference_nodes)
        
    def test_assign_structural_masses(self,
                           fuselage_model,
                           material):
        fuselage_model.create_nodes()
        fuselage_model.assign_structural_mass()

        reference_fuselage_radius=fuselage_model.fuselage_diameter_m/2
        reference_fuselage_structural_mass=2*np.pi*reference_fuselage_radius*fuselage_model.minimum_thickness_mm/1000*fuselage_model.fuselage_length_m*material.density
        reference_total_aircraft_mass=reference_fuselage_structural_mass+fuselage_model.main_wing_mass_kg+fuselage_model.canard_mass_kg+fuselage_model.landing_gear_mass_kg+fuselage_model.horizontal_tail_mass_kg
        np.testing.assert_almost_equal(reference_total_aircraft_mass,np.sum(fuselage_model.masses))


    def test_assign_nonstructural_masses(self,
                                         fuselage_model):
        fuselage_model.create_nodes()
        fuselage_model.assign_nonstructural_mass(component_mass=10.0,
                                                 component_cg_position_along_fuselage=fuselage_model.fuselage_length_m/2,
                                                 component_length_m=5.0)
        assert abs(np.sum(fuselage_model.masses)-10.0)<0.02


    # def test_calculate_loads_flight(self,
    #                                 material):
    #     fuselage_model=FuselageModel(
    #              fuselage_length_m=3.0,
    #              fuselage_diameter_m= 0.3,
    #              minimum_fuselage_thickness_mm=1e-6,
    #              material=material,
    #              main_wing_position_m=1.0,
    #              main_wing_mass_kg=10.0,
    #              horizontal_tail_position_m=3.0,
    #              horizontal_tail_mass_kg=3.0,
    #              landing_gear_position_m=1.5,
    #              landing_gear_mass_kg=3.0,
    #              number_of_nodes=10,
    #              canard_position_m=0.2,
    #              canard_mass_kg=1.0,
    #              canard_lift_fraction=0.20,             
    #              )
    #     fuselage_model.create_nodes()
    #     fuselage_model.assign_structural_mass()
    #     fuselage_model.calculate_loads_flight(load_factor=9.0)

    #     first_term = fuselage_model.horizontal_tail_position_m*(fuselage_model.canard_lift_fraction-1)*9.0*fuselage_model.total_aircraft_mass*CONSTANTS.G0
    #     second_term=np.sum(fuselage_model.nodes*fuselage_model.masses*CONSTANTS.G0)
    #     third_term=fuselage_model.canard_lift_fraction*9.0*fuselage_model.total_aircraft_mass*CONSTANTS.G0*fuselage_model.canard_position_m
    #     reference_main_wing_lift = (first_term+second_term-third_term)/(fuselage_model.main_wing_position_m-fuselage_model.horizontal_tail_position_m)
    #     np.testing.assert_almost_equal(fuselage_model.L_main_wing,reference_main_wing_lift)
    #     reference_ht_lift=(1-fuselage_model.canard_lift_fraction)*9.0*fuselage_model.total_aircraft_mass*CONSTANTS.G0-reference_main_wing_lift
    #     np.testing.assert_almost_equal(fuselage_model.L_horizontal_tail,reference_ht_lift)
    #     np.testing.assert_almost_equal(np.sum(fuselage_model.loads),8.0*fuselage_model.total_aircraft_mass*CONSTANTS.G0)
    #     reference_loads=-fuselage_model.masses*CONSTANTS.G0
    #     locs = [fuselage_model.canard_position_m, fuselage_model.main_wing_position_m, fuselage_model.horizontal_tail_position_m]
    #     vals = [fuselage_model.L_canard, fuselage_model.L_main_wing, fuselage_model.L_horizontal_tail]
    #     for loc, val in zip(locs, vals):
    #         reference_loads[np.argmin(np.abs(fuselage_model.nodes-loc))] += val
    #     np.testing.assert_allclose(reference_loads,fuselage_model.loads)
    #     reference_internal_shear_forces=interp1d(fuselage_model.nodes,
    #                                           np.cumsum(reference_loads),
    #                                           kind='zero',
    #                                           fill_value='extrapolate')

    #     np.testing.assert_allclose(reference_internal_shear_forces(np.linspace(0.0,fuselage_model.fuselage_length_m,10)),
    #                                fuselage_model.internal_shear_forces(np.linspace(0.0,fuselage_model.fuselage_length_m,10)))
        
    #     fine_nodes = np.linspace(fuselage_model.nodes[0], fuselage_model.nodes[-1], 100 * len(fuselage_model.nodes))
    #     shear_fine = reference_internal_shear_forces(fine_nodes)
    #     reference_internal_bending_moments = np.concatenate([[0], cumulative_trapezoid(shear_fine, fine_nodes)])
    #     reference_internal_bending_moments = interp1d(
    #                                  fine_nodes,
    #                                  reference_internal_bending_moments,
    #                                  kind='linear')
    #     np.testing.assert_allclose(reference_internal_bending_moments(np.linspace(0.0,fuselage_model.fuselage_length_m,10)),
    #                                fuselage_model.internal_bending_moments(np.linspace(0.0,fuselage_model.fuselage_length_m,10)))


    # def test_calculate_loads_landing(self,
    #                                 material):
    #     fuselage_model=FuselageModel(
    #              fuselage_length_m=3.0,
    #              fuselage_diameter_m= 0.3,
    #              minimum_fuselage_thickness_mm=1e-6,
    #              material=material,
    #              main_wing_position_m=1.0,
    #              main_wing_mass_kg=10.0,
    #              horizontal_tail_position_m=3.0,
    #              horizontal_tail_mass_kg=3.0,
    #              landing_gear_position_m=1.5,
    #              landing_gear_mass_kg=3.0,
    #              number_of_nodes=10,
    #              canard_position_m=0.2,
    #              canard_mass_kg=1.0,
    #              canard_lift_fraction=0.20,             
    #              )
    #     fuselage_model.create_nodes()
    #     fuselage_model.assign_structural_mass()
    #     fuselage_model.calculate_loads_landing(landing_load_factor=2.0)

    #     first_term = fuselage_model.horizontal_tail_position_m*(fuselage_model.canard_lift_fraction-1)*fuselage_model.total_aircraft_mass*CONSTANTS.G0
    #     second_term=np.sum(fuselage_model.nodes*fuselage_model.masses*CONSTANTS.G0)
    #     third_term=fuselage_model.canard_lift_fraction*fuselage_model.total_aircraft_mass*CONSTANTS.G0*fuselage_model.canard_position_m+2.0*fuselage_model.total_aircraft_mass*CONSTANTS.G0*fuselage_model.landing_gear_position_m
    #     reference_main_wing_lift = (first_term+second_term-third_term)/(fuselage_model.main_wing_position_m-fuselage_model.horizontal_tail_position_m)
    #     np.testing.assert_almost_equal(fuselage_model.L_main_wing,reference_main_wing_lift)
    #     reference_ht_lift=(1-fuselage_model.canard_lift_fraction)*fuselage_model.total_aircraft_mass*CONSTANTS.G0-reference_main_wing_lift
    #     np.testing.assert_almost_equal(fuselage_model.L_horizontal_tail,reference_ht_lift)
    #     np.testing.assert_almost_equal(np.sum(fuselage_model.loads),2.0*fuselage_model.total_aircraft_mass*CONSTANTS.G0)
    #     reference_loads=-fuselage_model.masses*CONSTANTS.G0
    #     locs = [fuselage_model.canard_position_m, fuselage_model.main_wing_position_m, fuselage_model.horizontal_tail_position_m,fuselage_model.landing_gear_position_m]
    #     vals = [fuselage_model.L_canard, fuselage_model.L_main_wing, fuselage_model.L_horizontal_tail, fuselage_model.force_landing_gear]
    #     for loc, val in zip(locs, vals):
    #         reference_loads[np.argmin(np.abs(fuselage_model.nodes-loc))] += val
    #     np.testing.assert_allclose(reference_loads,fuselage_model.loads)
    #     reference_internal_shear_forces=interp1d(fuselage_model.nodes,
    #                                           np.cumsum(reference_loads),
    #                                           kind='zero',
    #                                           fill_value='extrapolate')

    #     np.testing.assert_allclose(reference_internal_shear_forces(np.linspace(0.0,fuselage_model.fuselage_length_m,10)),
    #                                fuselage_model.internal_shear_forces(np.linspace(0.0,fuselage_model.fuselage_length_m,10)))
        
    #     fine_nodes = np.linspace(fuselage_model.nodes[0], fuselage_model.nodes[-1], 100 * len(fuselage_model.nodes))
    #     shear_fine = reference_internal_shear_forces(fine_nodes)
    #     reference_internal_bending_moments = np.concatenate([[0], cumulative_trapezoid(shear_fine, fine_nodes)])
    #     reference_internal_bending_moments = interp1d(
    #                                  fine_nodes,
    #                                  reference_internal_bending_moments,
    #                                  kind='linear')
    #     np.testing.assert_allclose(reference_internal_bending_moments(np.linspace(0.0,fuselage_model.fuselage_length_m,10)),
    #                                fuselage_model.internal_bending_moments(np.linspace(0.0,fuselage_model.fuselage_length_m,10)))


    def test_compute_sectional_properties(self,
                                          fuselage_model):
        r_o = fuselage_model.fuselage_diameter_m/2
        r_i = r_o - 1.0/1000
        y_bar = (4/(3*np.pi))*(r_o**2 + r_o*r_i + r_i**2)/(r_o+r_i)
        area = (np.pi/2)*(r_o**2 - r_i**2)
        Q = y_bar * area
        I_xx =np.pi/4*(r_o**4 - r_i**4)

        np.testing.assert_allclose(fuselage_model.compute_sectional_properties(1.0)[0],Q)
        np.testing.assert_allclose(fuselage_model.compute_sectional_properties(1.0)[1],I_xx)


    def test_buckling_stress(self,
                             fuselage_model,
                             material):

        reference_phi=1/16*np.sqrt(fuselage_model.fuselage_diameter_m/2/3.0)
        reference_gamma=1.0-0.901*(1-np.exp(-reference_phi))
        reference_sigma_cr=reference_gamma*(material.elastic_modulus*3.0)/(np.sqrt(3*(1-material.poisson_ratio**2))*fuselage_model.fuselage_diameter_m/2)
        np.testing.assert_almost_equal(fuselage_model.calculate_buckling_stress(3.0),reference_sigma_cr)


    # def test_thickness_utils(self,
    #                          fuselage_model,
    #                          material):

    #     reference_fuselage_model = copy.deepcopy(fuselage_model)
    #     reference_fuselage_model.create_nodes()
    #     reference_fuselage_model.assign_structural_mass()
    #     reference_fuselage_model.calculate_loads_flight(9.0)
    #     thicknesses_mm=np.ones_like(reference_fuselage_model.nodes)*0.1

    #     Q, I, enclosed_area = reference_fuselage_model.compute_sectional_properties(t_skin_mm=thicknesses_mm)
    #     tau_shear = reference_fuselage_model.internal_shear_forces(reference_fuselage_model.nodes) * Q / (I * thicknesses_mm/1000)
    #     sigma_bending = reference_fuselage_model.internal_bending_moments(reference_fuselage_model.nodes)*reference_fuselage_model.fuselage_diameter_m/(2*I)
    #     sigma_buckling = reference_fuselage_model.calculate_buckling_stress(thicknesses_mm/1000)
    #     maximum_allowed_normal_stress = np.minimum(0.7*material.yield_strength, sigma_buckling)
    #     maximum_allowed_shear_stress = 0.5*material.yield_strength #Tresca
    #     reference_bending_util = sigma_bending / maximum_allowed_normal_stress
    #     reference_shear_util = tau_shear / maximum_allowed_shear_stress

    #     fuselage_model.create_nodes()
    #     fuselage_model.assign_structural_mass()
    #     fuselage_model.calculate_loads_flight(9.0)
    #     bending_util, shear_util=fuselage_model.thickness_utils(thicknesses_mm/1000)

    #     np.testing.assert_almost_equal(bending_util, reference_bending_util)
    #     np.testing.assert_almost_equal(shear_util, reference_shear_util)

    #     reference_fuselage_model.create_nodes()
    #     reference_fuselage_model.assign_structural_mass()
    #     reference_fuselage_model.calculate_loads_landing(4.0)
    #     thicknesses_mm=np.ones_like(reference_fuselage_model.nodes)*0.1

    #     Q, I = reference_fuselage_model.compute_sectional_properties(t_skin_mm=thicknesses_mm)
    #     tau_shear = reference_fuselage_model.internal_shear_forces(reference_fuselage_model.nodes) * Q / (I * thicknesses_mm/1000)
    #     sigma_bending = reference_fuselage_model.internal_bending_moments(reference_fuselage_model.nodes)*reference_fuselage_model.fuselage_diameter_m/(2*I)
    #     sigma_buckling = reference_fuselage_model.calculate_buckling_stress(thicknesses_mm/1000)
    #     maximum_allowed_normal_stress = np.minimum(0.7*material.yield_strength, sigma_buckling)
    #     maximum_allowed_shear_stress = 0.5*material.yield_strength #Tresca
    #     reference_bending_util = sigma_bending / maximum_allowed_normal_stress
    #     reference_shear_util = tau_shear / maximum_allowed_shear_stress

    #     fuselage_model.create_nodes()
    #     fuselage_model.assign_structural_mass()
    #     fuselage_model.calculate_loads_landing(4.0)
    #     bending_util, shear_util=fuselage_model.thickness_utils(thicknesses_mm/1000)

