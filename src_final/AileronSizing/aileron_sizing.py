import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Aircraft.Planform import Planform
from tau_curve_approximation import tau_func


# Roll rate:

# P = d(phi)/d(t)

# P = - (C_l_delta_a) / (C_l_p) * delta_a * (2*V/b)

# C_l_delta_a = 2*C_l_alpha*tau / (S_ref * b) integral from b1 to b2 of c(y)*y*dy
    # parameters from wing and airfoil:
        # C_l_alpha
        # S_ref
        # b
        # c(y)
    # parameters from literature
        # tau = tau(0.3)
            # Extrapolate Tau function from 4 points 

def aileron_sizing(b1, b2, delta_a_max, V, chords_ratio, n_sections, planform:Planform):
    C_l_alpha = planform.airfoil_lift_slope
    S_ref = planform.wing_area
    b = planform.span
    tau = tau_func(chords_ratio)
    c_d0 = planform.CD0_cache["take_off"]
    c_y, _, y, dy = planform.sectional_properties(n_sections)


    Z = 2 * C_l_alpha * tau / (S_ref * b)


    C_l_alpha_integral = np.sum((c_y * y * dy)[b1:b2])

    C_l_delta_a = Z * C_l_alpha_integral
    
    coefficient_C_l_p = - 4 * (C_l_alpha + c_d0) / (S_ref * b **2) 

    C_l_p_integral = np.sum((y ** 2 * c_y * dy)[0:b/2])

    C_l_p = coefficient_C_l_p * C_l_p_integral

    P = - C_l_delta_a /C_l_p * delta_a_max * (2 * V / b) # Roll rate in radians per second

    return P
    

    










# Objective: find tau, b1, and b2 for the given wing parameters

