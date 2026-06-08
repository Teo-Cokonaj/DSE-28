import pytest
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


    def test_assign_nonstructural_masses(self):
        #TODO
        pass

    def test_calculate_loads_flight(self,
                                    fuselage_model):
        fuselage_model.create_nodes()
        fuselage_model.assign_structural_mass()
        fuselage_model.calculate_loads_flight()

        first_term = fuselage_model.horizontal_tail_position_m*(fuselage_model.canard_lift_fraction-1)*fuselage_model.total_aircraft_mass*CONSTANTS.G0
        second_term=np.sum(fuselage_model.nodes*fuselage_model.masses*CONSTANTS.G0)
        third_term=fuselage_model.canard_lift_fraction*fuselage_model.total_aircraft_mass*CONSTANTS.G0*fuselage_model.canard_position_m
        reference_main_wing_lift = (first_term+second_term-third_term)/(fuselage_model.main_wing_position_m-fuselage_model.horizontal_tail_position_m)
        np.testing.assert_almost_equal(fuselage_model.L_main_wing,reference_main_wing_lift)
        # reference_ht_lift=
    # def test_calculate_loads_landing(self):