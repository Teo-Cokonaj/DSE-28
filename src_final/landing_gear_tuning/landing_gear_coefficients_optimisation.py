import sys
import os
import control.matlab as ml
import scipy.optimize as opti
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

#from src_final.landing_gear_tuning.landing_gear_tuning import landing_gear_response

from landing_gear_tuning import landing_gear_response


def spring_and_damper_optimiser(c_max:float,
                                k_max:float,
                                downward_landing_speed:float = 0.5,
                                displacement_constraint_compression:float = 0.0095, 
                                force_requirement: float = 4, 
                                dt:float = 0.01, 
                                t:int = 5, 
                                m:float = 50, 
                                L:float = 35, 
                                plotting:bool = False, 
                                debug:bool = False):


    g = 9.80665                                                                                 # [m/s]
    max_allowable_force = force_requirement * g * m


    # Objective Function
    def objective(v):                                                                           # Minimising the force and displacement of the landing gear
        c, k = v                
        y_disp, y_force, _ = landing_gear_response(k = k, 
                                                   c = c, 
                                                   downward_landing_speed = downward_landing_speed, 
                                                   displacement_constraint_compression = displacement_constraint_compression, 
                                                   force_requirement = force_requirement, 
                                                   dt = dt, 
                                                   t = t, 
                                                   m = m, 
                                                   L = L, 
                                                   plotting = False, 
                                                   debug = False)
        # normalising the displacement and force

        normalised_displacement = np.max(np.abs(y_disp)) / displacement_constraint_compression
        normalised_force = np.max(np.abs(y_force)) / max_allowable_force
        
        return 0.5 * normalised_displacement + 0.5 * normalised_force                                                                             
    
    # constraints

    # Basic Stuff:

    def constraint_no_overdamping(v):
        c, k = v
        return (4 * m * k) - (c**2)
    
    def constraint_max_force(v):
        c, k = v
        _, y_force, _ = landing_gear_response(  k = k, 
                                                c = c, 
                                                downward_landing_speed = downward_landing_speed, 
                                                displacement_constraint_compression = displacement_constraint_compression, 
                                                force_requirement = force_requirement, 
                                                dt = dt, 
                                                t = t, 
                                                m = m, 
                                                L = L, 
                                                plotting = False, 
                                                debug = False)
        return max_allowable_force - np.max(np.abs(y_force))
    
    def constraint_max_displacement(v):
        c, k = v
        y_disp, _, _ = landing_gear_response(   k = k, 
                                                c = c, 
                                                downward_landing_speed = downward_landing_speed, 
                                                displacement_constraint_compression = displacement_constraint_compression, 
                                                force_requirement = force_requirement, 
                                                dt = dt, 
                                                t = t, 
                                                m = m, 
                                                L = L, 
                                                plotting = False, 
                                                debug = False)
        return displacement_constraint_compression - np.max(np.abs(y_disp))

    # Final Constraints list: 
    constraints = [                                           
        {'type': 'ineq', 'fun': constraint_no_overdamping},
        {'type': 'ineq', 'fun': constraint_max_force},
        {'type': 'ineq', 'fun': constraint_max_displacement},
    ]


    # bounds

    bounds = [
    (1e-3, c_max),  # Bounds for c (using a tiny positive number instead of absolute 0)
    (1e-3, k_max)   # Bounds for k
]

    # Initial Guess:                                                       
    x0 = [100, 50000]

    #_________________________________________________________________________Optimiser output_______________________________________________________________________
    result = opti.minimize(
        objective,
        x0,
        method='COBYLA',
        bounds = bounds,
        constraints=constraints,
        options={'ftol': 1e-9, 'disp': True, 'maxiter': 1000}
    )

    c_opt, k_opt = result.x

    if not result.success:
        print(f"Warning: optimiser did not converge — {result.message}")

    if debug:
        return c_opt, k_opt,constraints, result

    return c_opt, k_opt



if __name__ == "__main__":
    c_opt, k_opt = spring_and_damper_optimiser(c_max = 1000000, k_max = 1500000)

    print("optimal damping constant: ", c_opt)
    print("optimal spring constant: ", k_opt)