import sys
import os
import control.matlab as ml
import scipy.optimize as opti
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src_final.landing_gear_tuning.landing_gear_tuning import landing_gear_response


def spring_and_damper_optimiser(downward_landing_speed:float = 15, 
                                displacement_constraint_compression:float = 0.0095, 
                                force_requirement: float = 4, 
                                dt:float = 0.01, 
                                t:int = 5, 
                                m:float = 50, 
                                L:float = 35, 
                                plotting:bool = False, 
                                debug:bool = False):






    # Objective Function
    def objective(v):                                                                           # Minimising the force and displacement of the landing gear
        F, S = v                
        return                                                                                  # Objective TBD



    # constraints

    # maximum allowable spring constant (will depend on the design of the lg)

    # maximum allowable dashpot constant (will depend on the design of the lg)

    # maximum allowed damping (Z>1 would be overdamped)

    # maximum allowable force (dictated by CS-23)

    # maximum allowable displacement in compression (parameter given by Alex)



    # Final Constraints list:                                                                   # TO DO!!!!!
    constraints = [                                           
        {'type': 'ineq', 'fun': },
        {'type': 'ineq', 'fun': },
        {'type': 'ineq', 'fun': },
        {'type': 'ineq', 'fun': },
        {'type': 'ineq', 'fun': },
    ]


    # Initial Guess:                                                                            # TO DO!!!!!
    x0 = 

    #_________________________________________________________________________Optimiser output_______________________________________________________________________
    result = opti.minimize(
        objective,
        x0,
        method='SLSQP',
        constraints=constraints,
        options={'ftol': 1e-9, 'disp': True, 'maxiter': 1000}
    )

    if not result.success:
        print(f"Warning: optimiser did not converge — {result.message}")

    if debug:
        return 

    return 



