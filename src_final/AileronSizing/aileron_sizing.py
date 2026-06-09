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

def compute_p(b1, b2, delta_a_max, V, chords_ratio, n_sections, planform:Planform):
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
    

def size_ailerons(delta_a_max, Vmin, Vmax, chords_ratio, n_sections, planform:Planform, roll_rate_min:float, roll_rate_max:float, y_fus:float)->list[tuple[float, float]]:
    halfspan = planform.span / 2
    quarterspan = planform.span / 4
    aileron_opt:list[tuple[float, float]] = [(y_fus, halfspan)]
    tot_length_current = halfspan

    #option one - single aileron
    for i, b1 in enumerate(np.linspace(y_fus, halfspan, n_sections)):
        for b2 in np.linspace(b1, halfspan, n_sections-i):
            roll_rate_min_computed = compute_p(b1, b2, delta_a_max, Vmin, chords_ratio, n_sections, planform)
            roll_rate_max_computed = compute_p(b1, b2, delta_a_max, Vmax, chords_ratio, n_sections, planform)
            if (roll_rate_min_computed > roll_rate_min) and (roll_rate_max > roll_rate_max_computed) and ((b2 - b1) < tot_length_current):
                aileron_opt = [(b1, b2)]
                tot_length_current = b2 - b1
                break
            
    #option two - inboard and outboard aileron
    #inboard aileron for high speed
    inboard_aileron:tuple[float, float] = (y_fus, quarterspan)
    tot_length_inboard = quarterspan - y_fus
    for i, b1 in enumerate(np.linspace(0, quarterspan, n_sections //2)):
        for b2 in np.linspace(b1, quarterspan, n_sections //2 - i):
            roll_rate_computed = compute_p(b1, b2, delta_a_max, Vmax, chords_ratio, n_sections, planform)
            if (roll_rate_max > roll_rate_computed > roll_rate_min) and ((b2-b1) < tot_length_inboard):
                inboard_aileron = (b2, b1)
                tot_length_current = b2 - b1
                break

    #outboard_aileron for lowspeed
    for i, b1 in enumerate(np.linspace(quarterspan, halfspan, n_sections //2)):
        for b2 in np.linspace(b1, halfspan, n_sections //2 - i):
            roll_rate_computed = compute_p(b1, b2, delta_a_max, Vmin, chords_ratio, n_sections, planform)
            if (roll_rate_computed > roll_rate_min) and ((b2 - b1 + tot_length_inboard) < tot_length_current):
                aileron_opt = [inboard_aileron, (b2, b1)]
                tot_length_current = tot_length_inboard + b2 - b1
                break

    assert tot_length_current < halfspan - y_fus
    
    return aileron_opt









# Objective: find tau, b1, and b2 for the given wing parameters

