from parameters import *
from shear_moment_diagrams_sideview import calculate_flight_case
import numpy as np
import matplotlib.pyplot as plt
import math



def mainwing_lift_distribution(lift):

    x = np.linspace(-wingspan/2, wingspan/2, resolution)
    dx = x[1] - x[0]

    
    fuselage_overlap_top = 2*fuselage_radius*math.cos(math.asin((z_location_mainwing)/fuselage_radius))
    fuselage_overlap_bottom = 2*fuselage_radius*math.cos(math.asin((z_location_mainwing-t_wing)/fuselage_radius))
    fuselage_overlap = max(fuselage_overlap_top, fuselage_overlap_bottom)

    
    semi_wing_length = (wingspan - fuselage_overlap) / 2
    
    loads = np.zeros_like(x)
    
 
    fuselage_idx = np.abs(x) <= fuselage_overlap/2
    left_wing_idx = (~fuselage_idx) & (x < 0)
    right_wing_idx = (~fuselage_idx) & (x > 0)

    numerical_left_length = np.sum(left_wing_idx) * dx
    numerical_right_length = np.sum(right_wing_idx) * dx
    numerical_fuselage_length = np.sum(fuselage_idx) * dx

    q_lift_left = (lift / 2) / numerical_left_length
    q_lift_right = (lift / 2) / numerical_right_length
    q_fuselage = -lift / numerical_fuselage_length
    
    # Apply loads
    loads[left_wing_idx] = q_lift_left
    loads[right_wing_idx] = q_lift_right
    loads[fuselage_idx] = q_fuselage

    title = f"Main Wing Lift Distribution"
    return {"x": x, "dx": dx, "loads": loads, "title": title, "fuselage_overlap": fuselage_overlap}

def canard_lift_distribution(lift):

    canard_size_fraction = canard_lift_fraction/(L_main/W) 
    chord_length_canard = chord_length*canard_size_fraction
    t_canard = fraction_root_thickness * chord_length_canard

    if z_location_canard - t_canard < -fuselage_radius:
        raise ValueError("Warning: Canard extends below the bottom of the fuselage. Make z_location_canard less negative")
    
    fuselage_overlap_top = 2*fuselage_radius*math.cos(math.asin((z_location_canard)/fuselage_radius))
    fuselage_overlap_bottom = 2*fuselage_radius*math.cos(math.asin((z_location_canard-t_canard)/fuselage_radius))
    fuselage_overlap = max(fuselage_overlap_top, fuselage_overlap_bottom)

    semi_wing_length = (wingspan - fuselage_overlap) / 2
    semi_canard_length = semi_wing_length * canard_size_fraction

    x = np.linspace((-semi_canard_length-fuselage_radius), (semi_canard_length+fuselage_radius), resolution)
    dx = x[1] - x[0]

    loads = np.zeros_like(x)

    fuselage_idx = np.abs(x) <= fuselage_overlap/2
    left_wing_idx = (~fuselage_idx) & (x < 0)
    right_wing_idx = (~fuselage_idx) & (x > 0)


    numerical_left_length = np.sum(left_wing_idx) * dx
    numerical_right_length = np.sum(right_wing_idx) * dx
    numerical_fuselage_length = np.sum(fuselage_idx) * dx

    q_lift_left = (lift / 2) / numerical_left_length
    q_lift_right = (lift / 2) / numerical_right_length
    q_fuselage = -lift / numerical_fuselage_length
    
        
    loads[left_wing_idx] = q_lift_left
    loads[right_wing_idx] = q_lift_right
    loads[fuselage_idx] = q_fuselage

    title = f"Canard Lift Distribution"

    return {"x": x, "dx": dx, "loads": loads, "title": title, "fuselage_overlap": fuselage_overlap}


def cumulative_shear_and_moment(x, dx, loads, title):
    # Shear is the integral of load
    shear = np.cumsum(loads) * dx
    # Moment is the integral of shear
    moment = np.cumsum(shear) * dx
    
    print(f"--- {title} ---")
    print(f"Residual Shear at right tip: {shear[-1]:.2f} N")
    print(f"Residual Moment at right tip: {moment[-1]:.2f} Nm")

    return x, shear, moment


"""
def deflection_from_moment(x, dx, moment, E, I, fuselage_overlap, title):
    free_wing_idx = x > fuselage_overlap/2
    
    # 2. Zero out the bending moment inside the clamped region
    # (The internal structure takes this load; it doesn't contribute to wing bending)
    effective_moment = np.zeros_like(moment)
    effective_moment[free_wing_idx] = moment[free_wing_idx]
    
    # 3. Integrate Moment to get Slope (Theta)
    slope = np.cumsum(effective_moment) * dx / (E * I)
    
    # Enforce boundary condition: Rigid clamp cannot angle up or down
    slope[x <= fuselage_overlap/2] = 0.0
    
    # 4. Integrate Slope to get Deflection (v)
    deflection = np.cumsum(slope) * dx
    
    # Enforce boundary condition: Rigid clamp cannot move vertically
    deflection[x <= fuselage_overlap/2] = 0.0
    
    # 5. Mirror the right semispan to visualize the full wing
    x_full = np.concatenate((-np.flip(x[1:]), x))
    deflection_full = np.concatenate((np.flip(deflection[1:]), deflection))

"""    

def deflection_from_moment(dx, moment, E, I):

    slope = np.cumsum(moment) * dx / (E * I)
    
    # Boundary condition: The clamped root (x=0) cannot angle upwards.
    slope = slope - slope[0] 
    
    # 2. Integrate Slope to get Deflection (v)
    deflection = np.cumsum(slope) * dx
    
    # Boundary condition: The clamped root (x=0) cannot move vertically.
    deflection = deflection - deflection[0] 
    
    # 3. Mirror the right semispan to visualize the full wing
    # We slice [1:] to avoid duplicating the zero-point at the root
    x_full = np.concatenate((-np.flip(x[1:]), x))
    deflection_full = np.concatenate((np.flip(deflection[1:]), deflection))


    curvature = np.cumsum(moment) * dx / (E * I)
    slope = np.cumsum(curvature) * dx
    deflection = np.cumsum(slope) * dx
    
    return deflection


def plot_loads(x, loads, title):
    plt.figure(figsize=(10, 4))
    plt.plot(x, loads, label='Distributed Load (N/m)', color='green')
    plt.title(title)
    plt.xlabel('Position along Fuselage (m)')
    plt.ylabel('Load (N/m)')
    plt.grid()
    plt.legend()
    plt.show()


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

def plot_deflection_diagrams(x, deflection):
    plt.figure(figsize=(10, 4))
    plt.plot(x, deflection, label='Deflection (m)', color='purple')
    plt.title(f"Deflection from Bending Moment")
    plt.xlabel('Position along Fuselage (m)')
    plt.ylabel('Deflection (m)')
    plt.grid()
    plt.legend()
    plt.show()


L_main = calculate_flight_case()["L_main"]
L_canard = calculate_flight_case()["L_canard"]

#Main Wing
x, dx, loads, title, fuselage_overlap = mainwing_lift_distribution(L_main).values()
x, shear, moment = cumulative_shear_and_moment(x, dx, loads, title)
deflection = deflection_from_moment(dx, moment, wing_yield_strength, wing_I_xx)
#plot_loads(x, loads, title)
plot_shear_and_moment_diagrams(x, shear, moment)
plot_deflection_diagrams(x, deflection)

max_idx = np.argmax(moment)


print(f"Max Value: {moment[max_idx]}, Index: {max_idx}")


#Canard
x, dx, loads, title = canard_lift_distribution(L_canard)
x, shear, moment = cumulative_shear_and_moment(x, dx, loads, title)
deflection = deflection_from_moment(dx, moment, wing_yield_strength, wing_I_xx)
#plot_loads(x, loads, title)
#plot_shear_and_moment_diagrams(x, shear, moment)
#plot_deflection_diagrams(x, deflection)

