import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import math
from scipy.optimize import root_scalar
import parameters
from parameters import *

def x_range(fuselage_length, resolution):
    x = np.linspace(0, fuselage_length, resolution)
    dx = x[1] - x[0]
    return x, dx

def calculate_flight_case(x, W, canard_lift_fraction, main_wing_loc, empennage_loc, cg_loc, canard_loc):
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
    loads = np.zeros_like(x)

    # Apply point loads to the load vector
    for loc, val in [(canard_loc, L_canard), (cg_loc, -W), (main_wing_loc, L_main), (empennage_loc, L_empennage)]:
        idx = (np.abs(x - loc)).argmin()
        loads[idx] += val
    
    title = f"In-Flight"

    return {"loads": loads, "title": title, "L_main": L_main, "L_empennage": L_empennage, "L_canard": L_canard}

def plot_loads(x, loads, title):
    plt.figure(figsize=(10, 4))
    plt.plot(x, loads, label='Distributed Load (N/m)', color='green')
    plt.title(title)
    plt.xlabel('Position along Fuselage (m)')
    plt.ylabel('Load (N/m)')
    plt.grid()
    plt.legend()
    plt.show()


def cumulative_shear_and_moment(dx, loads, **kwargs):
    # Shear is the integral of load
    shear = np.cumsum(loads)
    # Moment is the integral of shear
    moment = np.cumsum(shear) * dx

    return {"shear": shear, "moment": moment}


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

def moments_of_area(fuselage_radius, t_skin):
    r_o = fuselage_radius
    r_i = r_o - t_skin
    y_bar = (4/3*math.pi)*(r_o**2 + r_o*r_i + r_i**2)/(r_o+r_i)
    area = (math.pi/2)*(r_o**2 - r_i**2)
    Q = y_bar * area

    I_xx = 0.1098*(r_o**4 - r_i**4) - 0.283*r_o**2*r_i**2*(r_o-r_i)/(r_o+r_i)

    return Q, I_xx

def thickness_for_combined_failure(shear, moment, x,  yield_strength, E, fuselage_radius, t_min=0.0003):
    t_skin = []
    critical_mode = []

    def get_utils(t, V, M):
        Q, I = moments_of_area(fuselage_radius, t)

        V_i = abs(V)
        M_i = abs(M)

        tau_shear = V_i * Q / (I * t)
        sigma_bending = M_i * fuselage_radius / I
        sigma_buckling = cylindricalBucklingStress(E, t, fuselage_radius)

        shear_util = tau_shear / yield_strength
        bending_util = sigma_bending / yield_strength
        buckling_util = sigma_bending / sigma_buckling

        return {
            "shear": shear_util,
            "bending_yield": bending_util,
            "buckling": buckling_util,
        }

    def utilization_error(t, V_i, M_i):
        utils = get_utils(t, V_i, M_i)
        return max(utils.values()) - 1.0

    for i in range(len(x)):
        V_i = shear[i]
        M_i = moment[i]

        # If no internal load, use minimum thickness
        if abs(V_i) < 1e-9 and abs(M_i) < 1e-9:
            t_skin.append(t_min)
            critical_mode.append("minimum")
            continue

        t_low = t_min
        t_high = fuselage_radius

        f_low = utilization_error(t_low, V_i, M_i)
        f_high = utilization_error(t_high, V_i, M_i)

        # Case 1: even minimum thickness is safe
        if f_low <= 0:
            t_required = t_low

        # Case 2: even maximum allowed thickness is unsafe
        elif f_high > 0:
            raise RuntimeError(
                f"No feasible thickness at x = {x[i]:.3f} m. "
                f"Utilization at t_high = {t_high*1000:.2f} mm is {f_high + 1:.2f}. "
                f"Increase radius, use stronger material, add frames/stringers, or check section properties."
            )

        # Case 3: normal root-finding
        else:
            solution = root_scalar(
                utilization_error,
                args=(V_i, M_i),
                bracket=[t_low, t_high],
                method="brentq"
            )

            if not solution.converged:
                raise RuntimeError(f"Failed to converge at x = {x[i]:.3f} m")

            t_required = solution.root

        # Determine critical mode at selected thickness
        utils = get_utils(t_required, V_i, M_i)
        mode = max(utils, key=utils.get)

        t_skin.append(t_required)
        critical_mode.append(mode)

    return np.array(t_skin), critical_mode



def cylindricalBucklingStress(E, t_skin, fuselage_radius):
    # sigma_cr = (E * t_skin) / (sqrt(3*(1-nu^2)) * R)
    nu = 0.3  # Poisson's ratio for CFRP
    sigma_cr = (E * t_skin) / (math.sqrt(3*(1-nu**2)) * fuselage_radius)
    return sigma_cr


def variable_port_iteration(x, wing_location, chord, canard_lift_fraction):
    main_lift_range = (x >= (wing_location - chord)) & (x <= (wing_location + chord))
    wing_loc_range = x[main_lift_range]

    max_shear = np.zeros_like(x)
    max_moment = np.zeros_like(x)
    
    # 1. Initialize a single figure with 2 stacked subplots sharing the X-axis
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 8))
    
    for i in wing_loc_range:         
        loads = calculate_flight_case(x=x, W=W, canard_lift_fraction=canard_lift_fraction, main_wing_loc=i, empennage_loc=empennage_loc, cg_loc=cg_loc, canard_loc=canard_loc)["loads"]
        shear, moment = cumulative_shear_and_moment(dx=dx, loads=loads).values()
        
        # 2. Vectorized envelope updates (Replacing the slow 'for j' loop)
        mask_s = np.abs(shear) > np.abs(max_shear)
        max_shear[mask_s] = shear[mask_s]
        
        mask_m = np.abs(moment) > np.abs(max_moment)
        max_moment[mask_m] = moment[mask_m]
        
        # 3. Plot each individual flight case with high transparency
        #ax1.plot(x, shear, color='blue', alpha=0.5, linewidth=0.5)
        #ax2.plot(x, moment, color='orange', alpha=0.5, linewidth=0.5)
        
    # 4. Plot the ultimate absolute worst-case envelopes on top after the loop
    #ax1.plot(x, max_shear, color='darkblue', linewidth=2, label='Max Shear Envelope')
    #ax1.plot(x, -np.abs(max_shear), color='darkblue', linestyle='--', linewidth=1, alpha=0.7)
    
    #ax2.plot(x, max_moment, color='darkred', linewidth=2, label='Max Moment Envelope')
    #ax2.plot(x, -np.abs(max_moment), color='darkred', linestyle='--', linewidth=1, alpha=0.7)
    
    # 5. Figure Formatting & Labels
    #ax1.set_title('Fuselage Loading Envelopes Across Varied Wing Locations', fontsize=12, fontweight='bold')
    #ax1.set_ylabel('Shear Force [N]')
    #ax1.grid(True, linestyle=':', alpha=0.6)
    #ax1.legend(loc='upper right')
    
    #ax2.set_ylabel('Bending Moment [Nm]')
    #ax2.set_xlabel('Fuselage Station x [m]')
    #ax2.grid(True, linestyle=':', alpha=0.6)
    #ax2.legend(loc='upper right')
    
    #plt.tight_layout()  # Prevents overlapping text elements
    #plt.show()
    
    return max_shear, max_moment

def fuselage_skin_mass(x, dx, t_skin, fuselage_radius):
    # volume = area of ring * dx
    volume = 0
    for i in range(len(x)):
        r_i = fuselage_radius - t_skin[i]
        area = (math.pi/2)*(fuselage_radius**2 - r_i**2)
        volume = volume + area * dx

    fuselage_mass = volume * CFRP[0]

    return fuselage_mass

def plotReqThickness(x, t_skin):
    plt.figure(figsize=(10, 4))
    plt.plot(x, t_skin * 1000)
    plt.xlabel("Position along fuselage x [m]")
    plt.ylabel("Required skin thickness [mm]")
    plt.title("Required Fuselage Skin Thickness")
    plt.grid()
    plt.show()


canard_lift_fraction = 0

x, dx = x_range(fuselage_length = fuselage_length, resolution = resolution)

loads, title, L_main, L_empennage, L_canard = calculate_flight_case(x=x, W=W, canard_lift_fraction=canard_lift_fraction, main_wing_loc=main_wing_loc, empennage_loc=empennage_loc, cg_loc=cg_loc, canard_loc=canard_loc).values()

shear, moment = cumulative_shear_and_moment(dx=dx, loads=loads).values()

t_skin_no_canard_static, critical_mode = thickness_for_combined_failure(shear=shear, moment=moment, x=x, yield_strength=CFRP[1], E = CFRP[2], fuselage_radius=fuselage_radius, t_min=minimum_thickness)

fuselage_mass_no_canard_static = fuselage_skin_mass(x=x, dx=dx, t_skin=t_skin_no_canard_static, fuselage_radius=fuselage_radius)

#plot_loads(x, loads, title)
#plot_shear_and_moment_diagrams(x, shear, moment)
#plotReqThickness(x, t_skin_no_canard_static)
#print(f"Static Port, No Canard Fuselage Mass: {fuselage_mass_no_canard_static} kg")

max_shear, max_moment = variable_port_iteration(x=x, wing_location=main_wing_loc, chord=chord_length, canard_lift_fraction=canard_lift_fraction)
t_skin_no_canard_variable, critical_mode = thickness_for_combined_failure(shear=max_shear, moment=max_moment, x=x, yield_strength=CFRP[1], E = CFRP[2], fuselage_radius=fuselage_radius, t_min=minimum_thickness)
fuselage_mass_no_canard_variable = fuselage_skin_mass(x=x, dx=dx, t_skin=t_skin_no_canard_variable, fuselage_radius=fuselage_radius)
#plot_shear_and_moment_diagrams(x, max_shear, max_moment)
#plotReqThickness(x, t_skin_no_canard_variable)

#print(f"Variable-Port, No Canard Fuselage Mass: {fuselage_mass_no_canard_variable} kg")



canard_lift_fraction = parameters.canard_lift_fraction

loads= calculate_flight_case(x=x, W=W, canard_lift_fraction=canard_lift_fraction, main_wing_loc=main_wing_loc, empennage_loc=empennage_loc, cg_loc=cg_loc, canard_loc=canard_loc)["loads"]
shear, moment = cumulative_shear_and_moment(dx=dx, loads=loads).values()
t_skin_canard_static, critical_mode = thickness_for_combined_failure(shear=shear, moment=moment, x=x, yield_strength=CFRP[1], E = CFRP[2], fuselage_radius=fuselage_radius, t_min=minimum_thickness)
t_skin_fuselage = np.maximum(t_skin_no_canard_static, t_skin_canard_static)
fuselage_mass_canard_static = fuselage_skin_mass(x=x, dx=dx, t_skin=t_skin_fuselage, fuselage_radius=fuselage_radius)

#plot_loads(x, loads, title)
#plot_shear_and_moment_diagrams(x, shear, moment)
#plotReqThickness(x, t_skin_canard_static)
#print(f"Static Port, Canard Fuselage Mass: {fuselage_mass_canard_static} kg")

max_shear, max_moment = variable_port_iteration(x=x, wing_location=main_wing_loc, chord=chord_length, canard_lift_fraction=canard_lift_fraction)
t_skin_canard_variable, critical_mode = thickness_for_combined_failure(shear=max_shear, moment=max_moment, x=x, yield_strength=CFRP[1], E = CFRP[2], fuselage_radius=fuselage_radius, t_min=minimum_thickness)
t_skin_fuselage = np.maximum(t_skin_no_canard_variable, t_skin_canard_variable)
fuselage_mass_canard_variable = fuselage_skin_mass(x=x, dx=dx, t_skin=t_skin_fuselage, fuselage_radius=fuselage_radius)
#print(f"Variable Port, Canard Fuselage Mass: {fuselage_mass_canard_variable} kg")