import pytest
import numpy as np
import matplotlib.pyplot as plt
import math
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))

from src_final.structural_analysis import parameters
from src_final.structural_analysis.parameters import *
from scipy.interpolate import interp1d
from scipy.integrate import cumulative_trapezoid

from src_final.structural_analysis.Material import Material
from src_final.global_parameters import CONSTANTS,Assumptions
from src_final.structural_analysis.wing_loading import WingModel
from src_final.Aircraft.Planform import Planform

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
def planform():
    return Planform(
        aspect_ratio=20.0,
        span=10.0,
        sweep_quarter_deg=0.0,
        taper=0.5,
        thickness_to_chord=0.12,
        cm_quarter_chord=1.0,
        wetted_surface_ratio=1.0,
        interference_factor=1.0,
        clmax=1.5,
        flap=False,
    )


@pytest.fixture
def wing_model(material,planform):
    return WingModel(
        wing_leng_m=5,
        wing_skin_thickness_m=0.005,
        number_of_nodes=2,
        material_1=material,
        material_2=material,
        planform=planform,
    )


class TestWingModel:

    def test_perimeter_and_area(self,
                                wing_model):
        c_stations  = np.array([2, 0])
        thickness_to_chord = 0.12
        perim, area  = wing_model.perimeter_area_of_section(c_stations, thickness_to_chord)

        a = c_stations/2
        b = a*thickness_to_chord

        expected_area = np.pi*a*b
        h = (a - b) ** 2 / (a + b) ** 2
        expected_perimeter = np.pi * (a + b) * (
            1 + (3 * h ** 2) / (10 + np.sqrt(4 - 3 * h ** 2))
        )
        assert area[0] == pytest.approx(expected_area[0])
        assert perim[0] == pytest.approx(expected_perimeter[0])
    
    def test_area_moment_inertia(self,
                                 wing_model
                                 ):
        c_stations  = np.array([2, 0])
        thickness_to_chord = 0.12
        Ix,Iy = wing_model.area_moment_inertia(c_stations,thickness_to_chord)
        a= c_stations/2
        b = a * thickness_to_chord
        Ix_expected = 1/4 * a * b**3 * np.pi
        Iy_expected = 1/4 * a ** 3 * b * np.pi
        #print (Ix)
        assert Ix[0] == pytest.approx(Ix_expected[0])
        assert Iy[0] == pytest.approx(Iy_expected[0])
    


    def test_torsion_determination(self, wing_model):
        c_stations = np.array([30.0, 20.0, 2.0, 4.0])

        reduced_sectional_spanwise_positions = np.array([0.0, 1.0])
        modified_sectional_lifts_schrenk = np.array([8.0, 12.0])

        y_stations = np.array([0.0, 1.0])

        torsion = wing_model.step_torsion_determination(
            c_stations=c_stations,
            y_stations=y_stations,
            reduced_sectional_spanwise_positions=reduced_sectional_spanwise_positions,
            modified_sectional_lifts_schrenk=modified_sectional_lifts_schrenk,
            plot = False
        )

        expected_torsion = np.array([16.0, 16.0, 16.0, 12.0])

        assert len(torsion) == len(c_stations)
        assert np.all(np.isfinite(torsion))
        assert torsion == pytest.approx(expected_torsion)
        
    def test_wing_rotation(self, wing_model, material):
        y_poz = np.array([0.0, 1.0, 2.0])
        chords = np.array([2.0, 2.0, 2.0])
        torsion = np.array([0.0, 10.0, 20.0])

        thickness_to_chord = 0.12

        rotation = wing_model.step_rotation_of_wing(
            G1=material.shear_modulus,
            thicknes_to_chord=0.12,
            skin_thickness=wing_model.wing_skin_thickness_m,
            chords=chords,
            torsion=torsion,
            y_poz=y_poz,
            plot = False,
        )[0]

        perimeter, area = wing_model.perimeter_area_of_section(
            chords,
            thickness_to_chord
        )

        perimeter = np.squeeze(perimeter)
        area = np.squeeze(area)

        expected_rotation_rate = torsion * perimeter / (
            4 * area ** 2 * material.shear_modulus * wing_model.wing_skin_thickness_m
        )

        expected_rotation = cumulative_trapezoid(
            expected_rotation_rate,
            y_poz,
            initial=0.0
        )

        assert len(rotation) == len(y_poz)
        assert np.all(np.isfinite(rotation))
        assert rotation[0] == pytest.approx(0.0)
        np.testing.assert_allclose(rotation, expected_rotation)
    
    # def test_wing_deflection(self,wing_model,material,planform):
    #     y_poz = np.array([0.0, 1.0, 2.0])
    #     chords = np.array([2.0, 2.0, 2.0])
    #     moments = np.array([200.0, 100.0, 0])
    #     def fake_step_moment(debug=False, plot=False):
    #         return moments

    #     monkeypatch.setattr(wing_model, "step_moment", fake_step_moment)
    #     monkeypatch.setattr(plt, "show", lambda: None)

    #     theta, deflection = wing_model.step_vertical_defletion(y_poz,material.elastic_modulus,
    #                                                      chords,planform.thickness_to_chord,False)
        
    #     Ix,_ = wing_model.area_moment_inertia(chords,planform.thickness_to_chord)
    #     Ix = np.squeeze(Ix)
    #     EI = Ix * material.elastic_modulus
    #     MEI = moments/EI
    #     expected_theta =cumulative_trapezoid(
    #         MEI,
    #         y_poz,
    #         initial=0.0
    #     )
    #     expected_deflection = cumulative_trapezoid(
    #         expected_theta,
    #         y_poz,
    #         initial=0.0
    #     )

    #     assert len(theta) == len(y_poz)
    #     assert len(displacement) == len(y_poz)

    #     assert np.all(np.isfinite(theta))
    #     assert np.all(np.isfinite(deflection))

    #     assert theta[0] == pytest.approx(0.0)
    #     assert deflection[0] == pytest.approx(0.0)

    #     np.testing.assert_allclose(theta, expected_theta)
    #     np.testing.assert_allclose(deflection, expected_deflection)
#python -m pytest tests_final/test_wing_geometry.py -v
