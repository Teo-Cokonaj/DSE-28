import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Aircraft.Planform import Planform
from AileronSizing.tau_curve_approximation import tau_func


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

def compute_p(b1, b2, delta_a_max, V, chords_ratio, n_sections, planform:Planform, cd0_cache_name: str = "takeoff", print_=False):

    #V = V * np.cos(planform.sweep_quarter_rad)
    C_l_alpha = planform.airfoil_lift_slope
    S_ref = planform.wing_area
    b = planform.span
    tau = tau_func(chords_ratio)

    c_d0 = planform.CD0_cache[cd0_cache_name]
    #c_d0 = 0

    c_stations, _, y_stations, dy = planform.sectional_properties(n_sections)
    y_mid = 0.5 * (y_stations[:-1] + y_stations[1:])
    c_mid = 0.5 * (c_stations[:-1] + c_stations[1:])

    mask = (y_mid >= b1) & (y_mid <= b2)
    if not np.any(mask):
        raise ValueError(
            f"Aileron limits must be inside the half-span [0, {planform.half_span:.3f}] m: got b1={b1}, b2={b2}"
        )

    C_l_alpha_integral = np.sum(c_mid[mask] * y_mid[mask] * dy[mask])
    C_l_delta_a = 2 * C_l_alpha * tau / (S_ref * b) * C_l_alpha_integral

    if print_:
        print(f"Clda: {-C_l_delta_a}")

    #C_l_delta_a = 0.19

    coefficient_C_l_p = -4 * (C_l_alpha + c_d0) / (S_ref * b ** 2)
    C_l_p_integral = np.sum(y_mid**2 * c_mid * dy)
    C_l_p = coefficient_C_l_p * C_l_p_integral
    #C_l_p = -0.76

    if print_:
       print(f"Cldp: {C_l_p}") 

    P = -C_l_delta_a / C_l_p * delta_a_max * (2 * V / b)

    # print("C_l_delta_a: ", C_l_delta_a)
    # print("C_l_p: ", C_l_p)
    # print("P in degrees: ", np.degrees(P))
    return P



def size_ailerons(delta_a_max, Vmin, Vmax, chords_ratio, n_sections, planform:Planform, roll_rate_min:float, roll_rate_max:float, y_fus:float)->list[tuple[float, float]]:
    halfspan = planform.span / 2
    quarterspan = planform.span / 4
    aileron_opt:list[tuple[float, float]] = [(y_fus, halfspan)]
    tot_length_current = halfspan - y_fus

    #option one - single aileron
    for i, b1 in enumerate(np.linspace(y_fus, halfspan, n_sections)):
        for b2 in np.linspace(b1, halfspan, n_sections-i)[1:]:
            roll_rate_min_computed = compute_p(b1, b2, delta_a_max, Vmin, chords_ratio, n_sections * 2, planform)
            roll_rate_max_computed = compute_p(b1, b2, delta_a_max, Vmax, chords_ratio, n_sections * 2, planform)
            if (roll_rate_min_computed > roll_rate_min) and (roll_rate_max > roll_rate_max_computed) and ((b2 - b1) < tot_length_current):
                aileron_opt = [(b1, b2)]
                tot_length_current = b2 - b1
                break
            
    #option two - inboard and outboard aileron
    #inboard aileron for high speed
    inboard_aileron:tuple[float, float] = (y_fus, quarterspan)
    tot_length_inboard = quarterspan - y_fus
    for i, b1 in enumerate(np.linspace(0, quarterspan, n_sections //2)):
        for b2 in np.linspace(b1, quarterspan, n_sections //2 - i)[1:]:
            roll_rate_computed = compute_p(b1, b2, delta_a_max, Vmax, chords_ratio, n_sections* 2, planform)
            if (roll_rate_max > roll_rate_computed > roll_rate_min) and ((b2-b1) < tot_length_inboard):
                inboard_aileron = (b1, b2)
                tot_length_inboard = b2 - b1
                break

    #outboard_aileron for lowspeed
    for i, b1 in enumerate(np.linspace(quarterspan, halfspan, n_sections //2)):
        for b2 in np.linspace(b1, halfspan, n_sections //2 - i)[1:]:
            roll_rate_computed = compute_p(b1, b2, delta_a_max, Vmin, chords_ratio, n_sections * 2, planform)
            if (roll_rate_computed > roll_rate_min) and ((b2 - b1 + tot_length_inboard) < tot_length_current):
                aileron_opt = [inboard_aileron, (b1, b2)]
                tot_length_current = tot_length_inboard + b2 - b1
                break

    assert tot_length_current < halfspan - y_fus
    
    return aileron_opt








if __name__ == "__main__":
    # Objective: find tau, b1, and b2 for the given wing parameters
    planform = Planform(
        aspect_ratio=27.0,
        span=3.4,
        sweep_quarter_deg=15.0,
        taper=0.3,
        thickness_to_chord=0.12,
        cm_quarter_chord=0.0,
        wetted_surface_ratio=1.07,
        interference_factor=1.0,
        clmax=1.22,
        flap=False,
    )
    planform.add_cache_entry("takeoff", mach=0.147, altitude=0.0)

    b1 = 0.6375
    b2 = 1.0625
    print("Roll rate (P):", np.rad2deg(compute_p(b1, b2, np.deg2rad(20.00), 50.0, 0.2, 1000, planform, print_=True)))

    # ailerons = size_ailerons(np.deg2rad(20), 50., 200., 0.3, 60, planform, np.deg2rad(45), np.deg2rad(180), 0.33)
    # print(ailerons)
    # inb_aileron = ailerons[0]
    # oub_aileron = ailerons[-1]
    # print(np.degrees(compute_p(inb_aileron[0], inb_aileron[1], np.deg2rad(20.00), 200.0, 0.3, 120, planform)))
    # print(np.degrees(compute_p(oub_aileron[0], oub_aileron[1], np.deg2rad(20.00), 50.0, 0.3, 120, planform)))

    # #plot of aileron
    # stall_speed = 46.
    # maximum_speed = np.linspace(50., 250., 20)

    # ailerons = [size_ailerons(np.deg2rad(20), stall_speed, Vmax, 0.3, 300, planform, np.deg2rad(45), np.deg2rad(180), 0.33) for Vmax in maximum_speed]
    # b1_inb = [aileron[0][0] for aileron in ailerons]
    # b2_inb = [aileron[0][1] for aileron in ailerons]
    # b1_oub = [aileron[-1][0] for aileron in ailerons]
    # b2_oub = [aileron[-1][1] for aileron in ailerons]

    # plt.plot(maximum_speed, b1_inb, label="b1 inboard")
    # plt.plot(maximum_speed, b2_inb, label="b2 inboard")
    # plt.plot(maximum_speed, b1_oub, label="b1 outboard")
    # plt.plot(maximum_speed, b2_oub, label="b1 outboard")
    # plt.legend()
    # plt.show()
    
    