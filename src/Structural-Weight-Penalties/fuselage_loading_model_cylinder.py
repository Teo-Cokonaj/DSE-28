import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import math
from scipy.optimize import root_scalar
from parameters import *



def calculate_flight_case(fuselage_length, resolution, W, canard_lift_fraction, main_wing_loc, empennage_loc, cg_loc, canard_loc):
    x = np.linspace(0, fuselage_length, resolution)
    dx = x[1] - x[0]
 

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

    return {"x": x, "dx": dx, "loads": loads, "title": title, "L_main": L_main, "L_empennage": L_empennage, "L_canard": L_canard}

def plot_loads(x, loads, title):
    plt.figure(figsize=(10, 4))
    plt.plot(x, loads, label='Distributed Load (N/m)', color='green')
    plt.title(title)
    plt.xlabel('Position along Fuselage (m)')
    plt.ylabel('Load (N/m)')
    plt.grid()
    plt.legend()
    plt.show()


def cumulative_shear_and_moment(x, dx, loads, **kwargs):
    # Shear is the integral of load
    shear = np.cumsum(loads)
    # Moment is the integral of shear
    moment = np.cumsum(shear) * dx

    return {"x" : x, "shear": shear, "moment": moment}


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

def thickness_for_combined_failure(
    shear,
    moment,
    x,
    tau_allow,
    sigma_allow,
    E,
    fuselage_radius,
    safety_factor=1.0,
    t_min=0.0005,   # 0.5 mm min thickness
):
    t_skin = []
    critical_mode = []

    def get_utils(t, V_i, M_i):
        Q, I = moments_of_area(fuselage_radius, t)

        V_i = abs(V_i)
        M_i = abs(M_i)

        tau_shear = V_i * Q / (I * t)
        sigma_bending = M_i * fuselage_radius / I
        sigma_buckling = cylindricalBucklingStress(E, t, fuselage_radius)

        shear_util = safety_factor * tau_shear / tau_allow
        bending_util = safety_factor * sigma_bending / sigma_allow
        buckling_util = safety_factor * sigma_bending / sigma_buckling

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

def plotReqThickness(x, t_skin, critical_mode):
    plt.figure(figsize=(10, 4))
    plt.plot(x, t_skin * 1000)
    plt.xlabel("Position along fuselage x [m]")
    plt.ylabel("Required skin thickness [mm]")
    plt.title("Required Fuselage Skin Thickness")
    plt.grid()
    plt.show()
    
x, dx, loads, title, L_main, L_empennage, L_canard = calculate_flight_case(fuselage_length, resolution, W, canard_lift_fraction, main_wing_loc, empennage_loc, cg_loc, canard_loc).values()
plot_loads(x, loads, title)

x, shear, moment = cumulative_shear_and_moment(x, dx, loads).values()
plot_shear_and_moment_diagrams(x, shear, moment)

sigma_allow = CFRP[1]  # Allowable bending stress for CFRP (example value)
tau_allow = sigma_allow  # Tresca criterion for shear yield from bending yield strength
E = CFRP[2]  # Young's modulus for CFRP

t_skin, critical_mode = thickness_for_combined_failure(
    shear=shear,
    moment=moment,
    x=x,
    tau_allow=tau_allow,
    sigma_allow=sigma_allow,
    E=E,
    fuselage_radius=fuselage_radius,
    safety_factor=1.5
)
plotReqThickness(x, t_skin, critical_mode)
print(t_skin)    
