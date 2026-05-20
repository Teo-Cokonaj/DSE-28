from scipy.optimize import root_scalar

import numpy as np
import math




def cumulative_shear_and_moment(x, dx, loads, **kwargs):
    # Shear is the integral of load
    shear = np.cumsum(loads)
    # Moment is the integral of shear
    moment = np.cumsum(shear) * dx

    return {"x" : x, "shear": shear, "moment": moment}



def wing_deflection(x, dx, moment, E, I_wingbox, I_wing, fuselage_overlap):
    free_wing_index = x > fuselage_overlap/2
    center_index = (x > 0) & (x <= fuselage_overlap/2)
    
    deflection = np.zeros_like(moment)

    # Wingbox deflection
    slope = np.cumsum(moment) * dx / (E * I_wingbox)
    slope[x <= fuselage_overlap/2] = 0.0
    deflection = np.cumsum(slope) * dx
    deflection[x <= fuselage_overlap/2] = 0.0

    # Add the fuselage overlap moment

    



    left_side = x < 0
    right_side = x > 0
    deflection[left_side] = np.flip(deflection[right_side])

    return deflection



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



import numpy as np
import matplotlib.pyplot as plt
import sympy as sp

# 1. Define Symbolic Variables
x, L, w0, EI = sp.symbols('x L w0 EI', real=True)
C3, C4 = sp.symbols('C3 C4', real=True)

# Define known reactions based on static equilibrium
R1 = w0 * L / 4
R2 = w0 * L / 4

# Define Macaulay bracket helper function logically: max(0, x - a)**n
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp

# 1. Define Symbols
x, L, w0 = sp.symbols('x L w0', real=True)
EI1, EI2 = sp.symbols('EI1 EI2', real=True)
C1, C2, C3, C4, C5, C6 = sp.symbols('C1 C2 C3 C4 C5 C6', real=True)

R1 = w0 * L / 4
R2 = w0 * L / 4

def macauley(x, a, n):
    return sp.Piecewise((0, x < a), ((x - a)**n, True))

# 2. Global Bending Moment Equation
M = (
    - (w0 / 2) * macauley(x, -L/2, 2)
    + (w0 / 2) * macauley(x, -L/4, 2)
    + R1 * macauley(x, -L/4, 1)
    - (w0 / 2) * macauley(x, L/4, 2)
    + R2 * macauley(x, L/4, 1)
)

# 3. Integrate Moment Indefinitely to get the base integrals
# Sympy's integrate handles Piecewise expressions natively
int_M = sp.integrate(M, x)
int_int_M = sp.integrate(int_M, x)

# 4. Define Sectional Slopes and Deflections
# Zone 1: [-L/2, -L/4] -> EI1
theta1 = (1 / EI1) * int_M + C1
y1 = (1 / EI1) * int_int_M + C1 * x + C2

# Zone 2: [-L/4, L/4] -> EI2
theta2 = (1 / EI2) * int_M + C3
y2 = (1 / EI2) * int_int_M + C3 * x + C4

# Zone 3: [L/4, L/2] -> EI1
theta3 = (1 / EI1) * int_M + C5
y3 = (1 / EI1) * int_int_M + C5 * x + C6

# 5. Set up Boundary and Continuity Equations
eqs = [
    y1.subs(x, -L/4),                             # 1. Support 1 Deflection = 0
    y2.subs(x, L/4),                              # 2. Support 2 Deflection = 0
    (theta1 - theta2).subs(x, -L/4),              # 3. Slope continuity at -L/4
    (y1 - y2).subs(x, -L/4),                      # 4. Displacement continuity at -L/4
    (theta2 - theta3).subs(x, L/4),               # 5. Slope continuity at L/4
    (y2 - y3).subs(x, L/4)                        # 6. Displacement continuity at L/4
]

# Solve for the 6 constants
constants = sp.solve(eqs, (C1, C2, C3, C4, C5, C6))

# Substitute constants back into expressions
y1_sol = y1.subs(constants)
y2_sol = y2.subs(constants)
y3_sol = y3.subs(constants)

# Combine into a single global Piecewise function for easy evaluation
y_global = sp.Piecewise(
    (y1_sol, x <= -L/4),
    (y2_sol, x <= L/4),
    (y3_sol, True)
)

# 6. Numerical Evaluation and Plotting
L_val = 3
w0_val = 7450
EI1_val = 80e9 * (0.28 * 0.1**3 / 12 - 0.2*0.05**3 / 12)  # Rigidity of overhangs
EI2_val = 80e9 * 0.28 * 0.1**3 / 12   # Rigidity of center span (e.g., stiffer/reinforced section)

# Map symbolic expression to a fast numpy function
y_numeric = sp.lambdify(x, y_global.subs({L: L_val, w0: w0_val, EI1: EI1_val, EI2: EI2_val}), 'numpy')

x_vals = np.linspace(-L_val/2, L_val/2, 500)
y_vals = y_numeric(x_vals)

# Plotting the result
plt.figure(figsize=(10, 5))
plt.plot(x_vals, y_vals, label='Deflection (Variable EI)', color='darkgreen', linewidth=2)
plt.plot([-L_val/4, L_val/4], [0, 0], 'ro', label='Supports at ±L/4')
plt.axvline(-L_val/4, color='grey', linestyle=':', alpha=0.5)
plt.axvline(L_val/4, color='grey', linestyle=':', alpha=0.5)
plt.axhline(0, color='black', linestyle='--', linewidth=0.5)

plt.title('Deflection Curve with Variable EI (Stiffer Center Span)')
plt.xlabel('Beam Position (x)')
plt.ylabel('Deflection (y)')
plt.gca().invert_yaxis()
plt.grid(True, which='both', linestyle=':', alpha=0.7)
plt.legend()
plt.show()