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

def thickness_for_yield_stress(V, x, tau_yield, fuselage_radius):

    # t =  V*Q/(I*tau_yield)
    # t, Q, I are all dependant on thickness, thus t_vars = (t*I)/Q
    t_vars =  np.abs(V)/tau_yield
    t_skin = []

    def t_vars_error(t):
        Q, I = moments_of_area(fuselage_radius, t)
        print(f"DEBUG: Q is {type(Q)}, I is {type(I)}")
        t_vars_guess = (t*I)/Q
        print(f"DEBUG: t_vars_guess is {t_vars_guess}")
        return t_vars_guess - t_vars_req
    
    for i in range(len(x)):
        t_vars_req = t_vars[i] 
        solution = root_scalar(t_vars_error, bracket=[0.000000001, fuselage_radius], method='brentq')
        
        if solution.converged:
            t_required = solution.root
            t_skin.append(t_required)
        else:
            raise RuntimeError("Failed to converge on a valid skin thickness.")
        
    return t_skin

    
def cylindricalBucklingStress(E, t_skin, fuselage_radius):
    # sigma_cr = (E * t_skin) / (sqrt(3*(1-nu^2)) * R)
    nu = 0.3  # Poisson's ratio for CFRP
    sigma_cr = (E * t_skin) / (math.sqrt(3*(1-nu**2)) * fuselage_radius)
    return sigma_cr
    
x, dx, loads, title, L_main, L_empennage, L_canard = calculate_flight_case(fuselage_length, resolution, W, canard_lift_fraction, main_wing_loc, empennage_loc, cg_loc, canard_loc).values()
plot_loads(x, loads, title)


x, shear, moment = cumulative_shear_and_moment(x, dx, loads).values()
plot_shear_and_moment_diagrams(x, shear, moment)

t_skin = thickness_for_yield_stress(shear, x, CFRP[1], fuselage_radius)

print(t_skin)    
