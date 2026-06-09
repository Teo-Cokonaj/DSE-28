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

def compute_p(b1, b2, delta_a_max, V, chords_ratio, n_sections, planform:Planform, altitude: float = 0.0, mach: float = 0.0, cd0_cache_name: str = "takeoff"):
    C_l_alpha = planform.airfoil_lift_slope
    S_ref = planform.wing_area
    b = planform.span
    tau = tau_func(chords_ratio)

    if cd0_cache_name not in planform.CD0_cache:
        planform.add_cache_entry(cd0_cache_name, mach, altitude)
    c_d0 = planform.CD0_cache[cd0_cache_name]

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

    coefficient_C_l_p = -4 * (C_l_alpha + c_d0) / (S_ref * b ** 2)
    C_l_p_integral = np.sum(y_mid**2 * c_mid * dy)
    C_l_p = coefficient_C_l_p * C_l_p_integral

    P = -C_l_delta_a / C_l_p * delta_a_max * (2 * V / b)
    return P

planform = Planform(
    aspect_ratio=27.0,
    span=2.66,
    sweep_quarter_deg=15.0,
    taper=0.5,
    thickness_to_chord=0.12,
    cm_quarter_chord=0.0,
    wetted_surface_ratio=0.9,
    interference_factor=1.0,
    clmax=1.44,
    flap=False,
)
planform.add_cache_entry("takeoff", mach=0.18, altitude=0.0)

b1 = planform.half_span * 0.375
b2 = planform.half_span * 0.625
print("Roll rate (P):", compute_p(b1, b2, np.deg2rad(20.0), 50.0, 0.2, 100, planform))