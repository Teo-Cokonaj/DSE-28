import pytest
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import math
import parameters
from scipy.interpolate import interp1d
from parameters import *
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))
from src_final.structural_analysis.Material import Material
from src_final.global_parameters import CONSTANTS,Assumptions
#from src_final.Aircraft.Planform import Planform

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
        wing_lengh_m = 5,
        wing_skin_thickness_m = 0.005,
        number_of_nodes = 2,
        material1 = material,
        material2 = material,
        planform=planform,
        
    )
    

