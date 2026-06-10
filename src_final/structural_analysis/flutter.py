#input properties: wing root chord, wing taper ratio, wing thickness, E, G, skin thickness
#formulas: the integration, I, J for a hollow elipse

import numpy as np
import scipy.integrate as integrate
import scipy.linalg as la
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))
from src_final.structural_analysis.Material import Material
from src_final.global_parameters import CONSTANTS, Assumptions

assumptions = Assumptions ()
constants = CONSTANTS ()

## Inputs ##
root_chord = 0.131
wing_span = 2.67
semi_span = wing_span/2
wing_taper_ratio = 0.5
thickness_to_chord = 0.12
wing_skin_thickness = 0.002
E = 69e9
G = 5.6e9


rho = assumptions.air_density_cruise_altitude


## Formulas ##

def chord_along_span(semi_span, wing_taper_ratio, root_chord, y):
    #rise over run. unrise 0.5RC, run semispan. Start at rc. c = -tr*y* + rc
    if y > semi_span:
        raise ValueError("y cannot be greater than semi-span")

    c_y = -((wing_taper_ratio*root_chord)/semi_span) * y + root_chord

    return c_y

## turn this into a pytest --> print(0.5*root_chord, chord_along_span(semi_span, wing_taper_ratio, root_chord, semi_span))

def thickness_along_span(c_y, thickness_to_chord):
    t_y = thickness_to_chord * c_y

    return t_y

## turn this into a pytest --> print(0.5*root_chord*thickness_to_chord, thickness_along_span(c_y, thickness_to_chord))

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