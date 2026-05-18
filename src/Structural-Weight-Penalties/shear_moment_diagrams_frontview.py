from shear_moment_diagrams_sideview import calculate_flight_case
from scipy.optimize import root_scalar

import numpy as np
import matplotlib.pyplot as plt
import math



def mainwing_lift_distribution(resolution, wingspan, lift, fuselage_radius, z_location_mainwing, t_wing):

    x = np.linspace(-wingspan/2, wingspan/2, resolution)
    dx = x[1] - x[0]

    
    fuselage_overlap_top = 2*fuselage_radius*math.cos(math.asin((z_location_mainwing)/fuselage_radius))
    fuselage_overlap_bottom = 2*fuselage_radius*math.cos(math.asin((z_location_mainwing-t_wing)/fuselage_radius))
    fuselage_overlap = max(fuselage_overlap_top, fuselage_overlap_bottom)
    
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

def canard_lift_distribution(canard_lift_fraction, L_main, W, chord_length, fraction_root_thickness, z_location_canard, fuselage_radius, wingspan, lift, resolution):

    lift_canard = canard_lift_fraction * lift
    print ("Lift of Canard: ", lift_canard)
    canard_area_fraction = canard_lift_fraction/(L_main/W) # area of the canard relative to the area of the main wing.
    canard_length_fraction = math.sqrt(canard_area_fraction) # area scales with the square of linear dimensions

    canard_wingspan = wingspan * canard_length_fraction
    chord_length_canard = chord_length*canard_length_fraction
    t_canard = fraction_root_thickness * chord_length_canard

    if z_location_canard - t_canard < -fuselage_radius:
        raise ValueError("Warning: Canard extends below the bottom of the fuselage. Make z_location_canard less negative")
    
    fuselage_overlap_top = 2*fuselage_radius*math.cos(math.asin((z_location_canard)/fuselage_radius))
    fuselage_overlap_bottom = 2*fuselage_radius*math.cos(math.asin((z_location_canard-t_canard)/fuselage_radius))
    fuselage_overlap = max(fuselage_overlap_top, fuselage_overlap_bottom)

    x = np.linspace(-canard_wingspan/2, canard_wingspan/2, resolution)
    dx = x[1] - x[0]

    loads = np.zeros_like(x)

    fuselage_idx = np.abs(x) <= fuselage_overlap/2
    left_wing_idx = (~fuselage_idx) & (x < 0)
    right_wing_idx = (~fuselage_idx) & (x > 0)


    numerical_left_length = np.sum(left_wing_idx) * dx
    numerical_right_length = np.sum(right_wing_idx) * dx
    numerical_fuselage_length = np.sum(fuselage_idx) * dx

    q_lift_left = (lift_canard / 2) / numerical_left_length
    q_lift_right = (lift_canard / 2) / numerical_right_length
    q_fuselage = -lift_canard / numerical_fuselage_length
    
        
    loads[left_wing_idx] = q_lift_left
    loads[right_wing_idx] = q_lift_right
    loads[fuselage_idx] = q_fuselage

    title = f"Canard Lift Distribution"

    return {"x": x, "dx": dx, "loads": loads, "title": title, "fuselage_overlap": fuselage_overlap, "chord_length_canard": chord_length_canard, "t_canard": t_canard}


def cumulative_shear_and_moment(x, dx, loads, title):
    # Shear is the integral of load
    shear = np.cumsum(loads) * dx
    # Moment is the integral of shear
    moment = np.cumsum(shear) * dx

    return x, shear, moment

def solid_wingbox_deflection_at_root(x, dx, moment, fuselage_overlap, youngs_modulus, I):
    center_idx = (x > 0) & (x <= fuselage_overlap/2)
    moment_half = np.zeros_like(moment)
    moment_half[center_idx] = moment[center_idx]
    
    slope = np.cumsum(moment_half) * dx / (youngs_modulus * I)
    deflection = np.cumsum(slope) * dx
    
    
    deflection_edge = deflection[center_idx][-1]

    return deflection_edge


def required_wingbox_stiffness(x, dx, moment, fuselage_overlap, youngs_modulus, target_deflection_m):
    
    center_idx = (x > 0) & (x <= fuselage_overlap/2)
    moment_half = np.zeros_like(moment)
    moment_half[center_idx] = moment[center_idx]
    
    unscaled_slope = np.cumsum(moment_half)*dx
    unscaled_deflection = np.cumsum(unscaled_slope)*dx
    
    
    unscaled_deflection_edge = unscaled_deflection[center_idx][-1]
    
    EI_required = np.abs(unscaled_deflection_edge / target_deflection_m)
    I_required = EI_required / youngs_modulus

    print(f"Target Max Deflection inside clamp: {target_deflection_m * 1000:.1f} mm")
    print(f"Required Clamp Stiffness (I): {I_required:.2e} N·m²")
     
    return I_required

def required_mainwing_wingbox_skin_thickness(I_req, deflection, chord, t_root):
    I_solid = (chord * t_root**3) / 12.0
    
    # Sanity check: If required I is larger than a solid block, it's impossible.
    if I_req > I_solid:
        raise ValueError(
            f"Required I ({I_req:.2e}) cannot be fulfilled by a hollow wingbox of these dimensions. "
            f"Deflection at the root with a solid wingbox: {deflection:.2f} m."
        )
        
    # 2. Define the equation we want to drive to zero
    def I_error(t_skin):
        b_in = chord - 2 * t_skin
        h_in = t_root - 2 * t_skin
        
        I_guess = (chord * t_root**3) / 12.0 - (b_in * h_in**3) / 12.0
        
        return I_guess - I_req
        
    solution = root_scalar(I_error, bracket=[0, t_root/2], method='brentq')
    
    if solution.converged:
        t_required = solution.root
        print(f"Required Skin Thickness for {I_req:.2e} m^4: {t_required * 1000:.2f} mm")
        return t_required
    else:
        raise RuntimeError("Failed to converge on a valid skin thickness.")


def required_canard_rod_thickness(I_required, t_canard, deflection):
    D = t_canard
    I_solid = (D**4) / 64
    if I_required > I_solid:
        raise ValueError(
            f"Required I ({I_required:.2e}) cannot be fullfilled by a hollow wingbox of these dimensions. "
            f"Deflection at the root with a solid wingbox: {deflection:.2f} m."
        )

    d = (D**4-64*I_required / math.pi)**(0.25)
    rod_thickness = (D - d) / 2
    
    return rod_thickness




"""
def deflection_from_moment(x, dx, moment, E, I, fuselage_overlap):
    free_wing_idx = x > fuselage_overlap/2
    
    deflection_moment = np.zeros_like(moment)
    deflection_moment[free_wing_idx] = moment[free_wing_idx]
    
    slope = np.cumsum(deflection_moment) * dx / (E * I)

    slope[x <= fuselage_overlap/2] = 0.0
    
    deflection = np.cumsum(slope) * dx
    
    deflection[x <= fuselage_overlap/2] = 0.0

    left_side = x < 0
    right_side = x > 0
    deflection[left_side] = np.flip(deflection[right_side])

    return deflection
"""