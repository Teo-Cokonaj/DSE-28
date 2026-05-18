from parameters import *
import numpy as np
import matplotlib.pyplot as plt


def get_base_setup(fuselage_length, resolution, W):
    x = np.linspace(0, fuselage_length, resolution)
    dx = x[1] - x[0]
    # Distributed weight load (N per node)
    # Total Weight * G-load spread across the length
    w_dist = np.full_like(x, -(W / resolution))
    return x, dx, w_dist

def calculate_flight_case(fuselage_length, resolution, W, canard_lift_fraction, main_wing_loc, empennage_loc, cg_loc, canard_loc):
    x, dx, loads = get_base_setup(fuselage_length, resolution, W)
        
    L_canard = W * canard_lift_fraction             # Assumed quantity from statistics
    
    # Set up the matrices for A * x = B
    A = np.array([
        [1.0, 1.0],                                  # Force coefficients
        [main_wing_loc, empennage_loc]               # Moment coefficients
    ])
    B = np.array([
        W - L_canard,                                # Force constants
        (W * cg_loc) - (L_canard * canard_loc)       # Moment constants
    ])

    L_main, L_empennage = np.linalg.solve(A, B)

    # Apply point loads to the load vector
    for loc, val in [(canard_loc, L_canard), (main_wing_loc, L_main), (empennage_loc, L_empennage)]:
        idx = (np.abs(x - loc)).argmin()
        loads[idx] += val
    
    title = f"In-Flight (Maneuver)"

    return {"x": x, "dx": dx, "loads": loads, "title": title, "L_main": L_main, "L_empennage": L_empennage, "L_canard": L_canard}

def calculate_ground_case(fuselage_length, resolution, W, main_gear_loc, nose_gear_loc, cg_loc):
    x, dx, loads = get_base_setup(fuselage_length, resolution, W)
    total_force = W
    
    r_nose = (total_force * (main_gear_loc - cg_loc)) / (main_gear_loc - nose_gear_loc)
    r_main = total_force - r_nose
    
    for loc, val in [(nose_gear_loc, r_nose), (main_gear_loc, r_main)]:
        idx = (np.abs(x - loc)).argmin()
        loads[idx] += val
    
    title = f"Ground / Landing"

    return {"x": x, "dx": dx, "loads": loads, "title": title}

def cumulative_shear_and_moment(x, dx, loads, **kwargs):
    # Shear is the integral of load
    shear = np.cumsum(loads)
    # Moment is the integral of shear
    moment = np.cumsum(shear) * dx

    return x, shear, moment




