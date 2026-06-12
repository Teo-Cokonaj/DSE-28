import pytest
import numpy as np
import scipy.linalg as la
import matplotlib.pyplot as plt
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
from src_final.structural_analysis.aerodynamic_matrices import AerodynamicMatrices
from src_final.structural_analysis.Material import Material
from src_final.Aircraft.Planform import Planform


@pytest.fixture
def material():
    return Material(density=1600,
                                elastic_modulus=50e9,
                                shear_modulus=5e9,
                                poisson_ratio=0.3,
                                yield_strength=600e6,
                                fracture_strength=600e6
                                )

@pytest.fixture
def planform_wing():
    return Planform(
            aspect_ratio=27.0,
            span=2.67,
            sweep_quarter_deg=0.0,
            taper=1.0,
            thickness_to_chord=0.12,
            cm_quarter_chord=1.0,
            wetted_surface_ratio=1.0,
            interference_factor=1.0,
            clmax=1.5,
            flap=False,
        )

@pytest.fixture
def aerodynamic_matrices(planform_wing,
                        material):
    return AerodynamicMatrices(planform=planform_wing,
                               material=material,
                               skin_thickness=0.01,
                               number_of_sections=100,
                               airspeed=100.0,
                               altitude_m=6000.0)

class TestAerodynamicMatrices:
    def test_B_matrix(self,
                      planform_wing,
                      aerodynamic_matrices
                      ):
        S=planform_wing.half_span
        c=aerodynamic_matrices.chords[0]
        a_w=planform_wing.CL_alpha
        e=aerodynamic_matrices.e
        atmosphere = aerodynamic_matrices.atmosphere
        airspeed = aerodynamic_matrices.airspeed

        reference_B = atmosphere.density()*airspeed*np.matrix([
            [c*S/10 * a_w, 0],
            [-c**2*S/8 * e * a_w, -c**3*S/24*(-1.2)]
        ])

        print('reference B: ',reference_B)
        print('actual B: ',aerodynamic_matrices.B_matrix())

        np.testing.assert_allclose(aerodynamic_matrices.B_matrix(),
                                   reference_B,
                                   rtol=1e-3)
        
    def test_C_matrix(self,
                      planform_wing,
                      aerodynamic_matrices,
                      ):

        S=planform_wing.half_span
        c=aerodynamic_matrices.chords[0]
        a_w=planform_wing.CL_alpha
        e=aerodynamic_matrices.e
        atmosphere = aerodynamic_matrices.atmosphere
        airspeed = aerodynamic_matrices.airspeed

        reference_C = atmosphere.density()*airspeed**2*np.matrix([
            [0.0, c*S/8*a_w],
            [0.0, -c**2*S/6*e*a_w]
        ])

        print('reference C: ',reference_C)
        print('actual C: ',aerodynamic_matrices.C_matrix())

        np.testing.assert_allclose(aerodynamic_matrices.C_matrix(),
                                   reference_C,
                                   rtol=1e-3)
        
        