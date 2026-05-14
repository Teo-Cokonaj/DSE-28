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


def plot_shear_and_moment_diagrams(x, shear, moment):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    ax1.plot(x, shear, label='Shear Force (N)', color='blue')
    ax1.set_title('Shear Force Diagram')
    ax1.set_xlabel('Position along Fuselage (m)')
    ax1.set_ylabel('Shear Force (N)')
    ax1.grid()
    ax1.legend()
    
    ax2.plot(x, moment, label='Bending Moment (Nm)', color='red')
    ax2.set_title('Bending Moment Diagram')
    ax2.set_xlabel('Position along Fuselage (m)')
    ax2.set_ylabel('Bending Moment (Nm)')
    ax2.grid()
    ax2.legend()
    
    plt.tight_layout()
    plt.show()

"""
x, dx, loads, title, L_main, L_empennage, L_canard = calculate_flight_case(fuselage_length, resolution, W, canard_lift_fraction, main_wing_loc, empennage_loc, cg_loc, canard_loc).values()
x, shear, moment = cumulative_shear_and_moment(x, dx, loads)

#plot_shear_and_moment_diagrams(x, shear, moment)

print(f"In-Flight Case:")
print(f"Residual Shear at tail: {shear[-1]:.2f} N")
print(f"Residual Moment at tail: {moment[-1]:.2f} Nm")
print(f"Main Wing Lift Fraction: {L_main/W:.2f}")
print(f"Empennage Lift Fraction: {L_empennage/W:.2f}")

###################################################################

x, dx, loads, title = calculate_ground_case(fuselage_length, resolution, W, main_gear_loc, nose_gear_loc, cg_loc).values()
x, shear, moment = cumulative_shear_and_moment(x, dx, loads)

#plot_shear_and_moment_diagrams(x, shear, moment)

print(f"Ground Case:")
print(f"Residual Shear at tail: {shear[-1]:.2f} N")
print(f"Residual Moment at tail: {moment[-1]:.2f} Nm")

"""