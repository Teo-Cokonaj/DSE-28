import sys
import os
import scipy.optimize as opti
import aerosandbox.numpy as np


# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Calculating the length of the landing gear:


# Tip-back angle

def lg_pos_and_length(L1, L2, L3, x_cg, up_sweep_angle, diameter_fuselage):

    # Convert inputs to radians

    sigma = up_sweep_angle * np.pi / 180
    theta = 15 * np.pi /180


    # To be searched by optimiser
    x_main_lg = 0 # TBD (it will have to be moved)
    Y_lg = 0


    x_cone_start = L1 + L2
    x_tail_tip = L1 + L2 + L3
    R = diameter_fuselage / 2



    def tail_point_near(l_landing_gear);
        return (x_cone_start, l_landing_gear - R)
    
    def tail_point_far(l_landing_gear):
        return (x_tail_tip, l_landing_gear - R + L3 * np.tan(sigma))
    
    def scrape_angle(x_main_lg, tail_point):
        return np.arctan2(tail_pint[1] tail_point[0] - x_main_lg)
    
    def beta_angle(x_main_lg, l_landing_gear):
        return np.arctan(x_main_lg - x_cg, l_landing_gear)
    
    def nose_gear_pos(x_main_lg):
        return (x_cg - x_main_lg * 0.85) / 0.15
    
    def turn_over_angle(x_main_lg, Y_lg, l_landing_gear):

        x_nose_lg = nose_gear_pos(x_main_lg)
        d = x_main_lg - x_front_lg
        alpha = np.arctan( Y_lg / d )
        c = (x_cg - x_nose_lg) * np.sin(alpha)

        return np.arctan2(c, l_landing_gear)
    

    # Objective:

    def objective(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return l_landing_gear
    

    # Constraints: 



                
    



    return length_main_lg, x_pos_main_lg, x_pos_front_lg


