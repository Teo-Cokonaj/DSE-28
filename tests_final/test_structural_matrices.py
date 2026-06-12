import pytest
import numpy as np
import scipy.linalg as la
import matplotlib.pyplot as plt
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
from src_final.structural_analysis.structural_matrices import StructuralMatrices
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
def structural_matrices(planform_wing,
                        material):
    return StructuralMatrices(planform=planform_wing,
                                                material=material,
                                                skin_thickness=0.01,
                                                number_of_sections=100)

class TestStructuralMatrices:
    def test_A_matrix(self,
                      planform_wing,
                      structural_matrices
                      ):
        S=planform_wing.half_span
        c=structural_matrices.chords[0]
        xf= structural_matrices.xf[0]
        structural_matrices._mass_per_unit_area()

        reference_A = structural_matrices.mass_per_unit_area*np.matrix([
            [S*c/5, (S/4)*(c**2/2 - c*xf)],
            [(S/4)*(c**2/2 - c*xf), (S/3)*(c**3/3 - c**2*xf + xf**2*c)]
        ])

        print(type(reference_A))
        print(type(structural_matrices.A_matrix()))

        print(reference_A.shape)
        print(structural_matrices.A_matrix().shape)

        print('reference A: ',reference_A)
        print('actual A: ',structural_matrices.A_matrix())

        np.testing.assert_allclose(np.asarray(structural_matrices.A_matrix()),
                                   np.asarray(reference_A),
                                   rtol=1e-2,
                                   atol=1e-15)
        
    def test_E_matrix(self,
                      planform_wing,
                      structural_matrices,
                      material):

        s=planform_wing.half_span

        reference_E= np.matrix([
            [4*material.elastic_modulus*structural_matrices.I()[0]/s**3, 0],
            [0, material.shear_modulus*structural_matrices.J()[0]/s]
        ])

        print('reference E: ',reference_E)
        print('actual E: ',structural_matrices.E_matrix())

        np.testing.assert_allclose(structural_matrices.E_matrix(),
                                   reference_E)
        
        