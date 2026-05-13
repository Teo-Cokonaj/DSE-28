from parameters import *
import numpy as np
import matplotlib.pyplot as plt


def get_base_setup():
    x = np.linspace(0, fuselage_length, resolution)
    dx = x[1] - x[0]
    # Distributed weight load (N per node)
    # Total Weight * G-load spread across the length
    w_dist = np.full_like(x, -(W / resolution))
    return x, dx, w_dist

def calculate_flight_case():
    x, dx, loads = get_base_setup()
        
    L_canard = W * canard_lift_fraction # Assumed quantity from statistics
    
    # Solve for Main Wing and Empennage Lift simultaneously
    # Forces: L_main + L_empennage = W - L_canard
    # Moments: L_main*main_wing_loc + L_empennage*empennage_loc = W*cg_loc - L_canard*canard_loc
    
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

    print(f"Main Wing Lift Fraction: {L_main/W:.2f}")
    print(f"Empennage Lift Fraction: {L_empennage/W:.2f}")

    # Apply point loads to the load vector
    for loc, val in [(canard_loc, L_canard), (main_wing_loc, L_main), (empennage_loc, L_empennage)]:
        idx = (np.abs(x - loc)).argmin()
        loads[idx] += val
    
    title = f"In-Flight (Maneuver)"

    return {"x": x, "dx": dx, "loads": loads, "title": title, "L_main": L_main, "L_empennage": L_empennage, "L_canard": L_canard}

def calculate_ground_case():
    x, dx, loads = get_base_setup()
    # On ground, g-load is usually different, but we'll keep max_g for "hard landing"
    total_force = W
    
    # Solve for Nose Gear Reaction (Rn) using Sum of Moments = 0 at Main Gear
    # Equation: Weight*(main_gear - cg) - Rn*(main_gear - nose_gear) = 0
    r_nose = (total_force * (main_gear_loc - cg_loc)) / (main_gear_loc - nose_gear_loc)
    r_main = total_force - r_nose
    
    for loc, val in [(nose_gear_loc, r_nose), (main_gear_loc, r_main)]:
        idx = (np.abs(x - loc)).argmin()
        loads[idx] += val
    
    title = f"Ground / Landing"

    return {"x": x, "dx": dx, "loads": loads, "title": title}

def integrate_and_plot(x, dx, loads, title, **kwargs):
    # Shear is the integral of load
    shear = np.cumsum(loads)
    # Moment is the integral of shear
    moment = np.cumsum(shear) * dx
    
    print(f"--- {title} ---")
    print(f"Residual Shear at tail: {shear[-1]:.2f} N")
    print(f"Residual Moment at tail: {moment[-1]:.2f} Nm")

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


plot_shear_and_moment_diagrams(*integrate_and_plot(**calculate_flight_case()))
plot_shear_and_moment_diagrams(*integrate_and_plot(**calculate_ground_case()))
