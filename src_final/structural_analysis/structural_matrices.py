#input properties: wing root chord, wing taper ratio, wing thickness, E, G, skin thickness
#formulas: the integration, I, J for a hollow elipse

import numpy as np
import scipy.integrate as integrate
import scipy.linalg as la
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))
from src_final.structural_analysis.Material import Material
from src_final.Aircraft.Planform import Planform
from src_final.global_parameters import CONSTANTS, Assumptions

assumptions = Assumptions ()
constants = CONSTANTS ()

class StructuralMatrices:
    def __init__(self,
                 planform: Planform,
                 material: Material,
                 skin_thickness: float,
                 number_of_sections: int
                 ):
        self.root_chord = planform.c_root
        self.wing_span = planform.span
        self.semi_span = planform.half_span
        self.taper_ratio = planform.taper
        self.thickness_to_chord = planform.thickness_to_chord
        self.skin_thickness=skin_thickness
        self.E = material.elastic_modulus
        self.G=material.shear_modulus
        self.number_of_sections = number_of_sections
        self.chords, self.areas, self.y_stations,self. dy=planform.sectional_properties(self.number_of_sections)
        self.wing_thicknesses=self.thickness_to_chord*self.chords
        self.skin_thicknesses=np.ones_like(self.wing_thicknesses)*self.skin_thickness


    def kinetic_energy_b():

        # m * (doubleintegral 0-s and 0-c)((y/s)^4*q_dot_b+(y/s)^3*(x-x_f)*q_dot_t)dx*dy

        return

    def kinetic_energy_t():

        # m * (doubleintegral 0-s and 0-c)((y/s)^3*(x-x_f)*q_dot_b+(y/s)^2*(x-x_f)^2*q_dot_t)dx*dy

        return


    def A_matrix():

        a_bb = m*(   (n/6)*(s**2) + (rc/5)*s    )
        a_bt = m*(    (n/5)*(s**2) + (rc/4)*s    )


        return a_bb, a_bt, a_tb, a_tt



    def elastic_energy_b():

        # integral 

        return