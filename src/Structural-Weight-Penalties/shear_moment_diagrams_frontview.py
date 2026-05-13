from parameters import *
from shear_moment_diagrams_sideview import *
import numpy as np
import matplotlib.pyplot as plt
import math



def mainwing_lift_distribution(lift):
    x = np.linspace(-wingspan/2, wingspan/2, resolution)
    dx = x[1] - x[0]

    
    wing_fuselage_overlap_top = 2*fuselage_radius*math.cos(math.asin((fuselage_radius-z_location_mainwing)/fuselage_radius))
    if z_location_mainwing - t_wing < -fuselage_radius:
        wing_fuselage_overlap_bottom = 2*fuselage_radius*math.cos(math.asin((fuselage_radius-(z_location_mainwing-t_wing)/fuselage_radius)))
        wing_fuselage_overlap = max(wing_fuselage_overlap_top, wing_fuselage_overlap_bottom)
    else:
        wing_fuselage_overlap = wing_fuselage_overlap_top
    
    semi_wing_length = (wingspan - wing_fuselage_overlap) / 2
    
    q_lift = (lift / 2) / semi_wing_length 
    q_fuselage = -W / fuselage_diameter 
    
    loads = np.zeros_like(x)
    
    left_wing_idx = x < -wing_fuselage_overlap/2
    right_wing_idx = x > wing_fuselage_overlap/2
    fuselage_idx = (x >= -wing_fuselage_overlap/2) & (x <= wing_fuselage_overlap/2)
    
    # Apply loads
    loads[left_wing_idx] = q_lift
    loads[right_wing_idx] = q_lift
    loads[fuselage_idx] = q_fuselage

    title = f"Main Wing Lift Distribution"

    return x, dx, loads, title


def canard_lift_distribution(lift):
    x = np.linspace(-wingspan/2, wingspan/2, resolution)
    dx = x[1] - x[0]



    canard_size_fraction = canard_lift_fraction/(L_main/W) 
    chord_length_canard = chord_length*canard_size_fraction
    t_canard = fraction_root_thickness * chord_length_canard

    if z_location_canard - t_canard < -fuselage_radius:
        raise ValueError("Warning: Canard extends below the bottom of the fuselage. Increase z_location_canard")
    
    
    canard_fuselage_overlap_top = 2*fuselage_radius*math.cos(math.asin((fuselage_radius-z_location_canard)/fuselage_radius))
    if z_location_canard - t_canard > -fuselage_radius:
        canard_fuselage_overlap_bottom = 2*fuselage_radius*math.cos(math.asin((fuselage_radius-(z_location_canard-t_canard)/fuselage_radius)))
        canard_fuselage_overlap = max(canard_fuselage_overlap_top, canard_fuselage_overlap_bottom)
    else:
        canard_fuselage_overlap = canard_fuselage_overlap_top
    
    wing_fuselage_overlap_top = 2*fuselage_radius*math.cos(math.asin((fuselage_radius-z_location_mainwing)/fuselage_radius))
    if z_location_mainwing - t_wing < -fuselage_radius:
        wing_fuselage_overlap_bottom = 2*fuselage_radius*math.cos(math.asin((fuselage_radius-(z_location_mainwing-t_wing)/fuselage_radius)))
        wing_fuselage_overlap = max(wing_fuselage_overlap_top, wing_fuselage_overlap_bottom)
    else:
        wing_fuselage_overlap = wing_fuselage_overlap_top
    
    semi_wing_length = (wingspan - wing_fuselage_overlap) / 2
    semi_canard_length = semi_wing_length * canard_size_fraction

    
    q_lift = (lift / 2) / semi_wing_length 
    q_fuselage = -W / fuselage_diameter 
    
    loads = np.zeros_like(x)
    
    left_wing_idx = x < -wing_fuselage_overlap/2
    right_wing_idx = x > wing_fuselage_overlap/2
    fuselage_idx = (x >= -wing_fuselage_overlap/2) & (x <= wing_fuselage_overlap/2)
    
    # Apply loads
    loads[left_wing_idx] = q_lift
    loads[right_wing_idx] = q_lift
    loads[fuselage_idx] = q_fuselage

    title = f"Canard Lift Distribution"

    return x, dx, loads, title


def integrate_and_plot(x, dx, loads, title):
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


L_main = calculate_flight_case()["L_main"]
L_canard = calculate_flight_case()["L_canard"]


canard_span = wingspan / ((L_main/W)/canard_lift_fraction)