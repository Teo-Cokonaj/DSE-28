import sys
import os
import scipy.optimize as opti
import aerosandbox.numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


### Assumptions
    # CG at centre-line of fuselage
    # Landing gear length given from centre-line
    # No deformation of wings on landing (Rigid Body)
    # For wing distance from centreline, down is negative, and up is positive


def lg_pos_and_length(L1, L2, L3, x_cg_from_nose, up_sweep_angle_rad, diameter_fuselage, wing_height_from_centre_line, wing_span, debug=False):

    sigma = up_sweep_angle_rad
    theta = 15 * np.pi / 180 # also airfoil stall angle
    phi_min =  7.0 * np.pi / 180  

    x_cone_start = L1 + L2
    x_tail_tip = L1 + L2 + L3
    R = diameter_fuselage / 2

    def tail_point_near(l_landing_gear):
        return (x_cone_start, l_landing_gear - R)

    def tail_point_far(l_landing_gear):
        return (x_tail_tip, l_landing_gear - R + L3 * np.tan(sigma))

    def scrape_angle(x_main_lg, tail_point):
        return np.arctan2(tail_point[1], tail_point[0] - x_main_lg) 

    def beta_angle(x_main_lg, l_landing_gear):
        return np.arctan2(x_main_lg - x_cg_from_nose, l_landing_gear)

    def nose_gear_pos(x_main_lg):
        return (x_cg_from_nose - x_main_lg * 0.85) / 0.15

    def turn_over_angle(x_main_lg, Y_lg, l_landing_gear):
        x_nose_lg = nose_gear_pos(x_main_lg)
        d = x_main_lg - x_nose_lg
        alpha = np.arctan2(Y_lg, d)                       
        c = (x_cg_from_nose - x_nose_lg) * np.sin(alpha)
        return np.arctan2(c, l_landing_gear)
    
    def wing_tip_to_lg_angle(Y_lg, l_landing_gear, wing_height_from_centre_line, wing_span):
        vertical   = l_landing_gear + wing_height_from_centre_line
        horizontal = (wing_span / 2) - Y_lg
        return np.arctan2(vertical, horizontal)


    def objective(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return np.sqrt(l_landing_gear**2 + Y_lg**2)

    def constraint_scrape_near(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return scrape_angle(x_main_lg, tail_point_near(l_landing_gear)) - theta

    def constraint_scrape_far(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return scrape_angle(x_main_lg, tail_point_far(l_landing_gear)) - theta

    def constraint_beta_scrape(v):
        l_landing_gear, x_main_lg, Y_lg = v
        # theta_crit = min(
        #     scrape_angle(x_main_lg, tail_point_near(l_landing_gear)),
        #     scrape_angle(x_main_lg, tail_point_far(l_landing_gear))
        # )
        theta_crit = theta
        print(min(
            scrape_angle(x_main_lg, tail_point_near(l_landing_gear)),
            scrape_angle(x_main_lg, tail_point_far(l_landing_gear))
        ))
        return beta_angle(x_main_lg, l_landing_gear) - theta_crit

    def constraint_turnover(v):                             
        l_landing_gear, x_main_lg, Y_lg = v
        psi_max = 55.0 * np.pi / 180
        return psi_max - turn_over_angle(x_main_lg, Y_lg, l_landing_gear)

    def constraint_keel_clearance(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return l_landing_gear - R - 0.01

    def constraint_main_lg_behind_cg(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return x_main_lg - x_cg_from_nose

    def constraint_main_lg_ahead_tail_cone(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return x_cone_start - x_main_lg

    def constraint_Y_lg_min(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return Y_lg - R
    
    def constraint_wing_tip_clearance(v):
        l_landing_gear, x_main_lg, Y_lg = v
        phi = wing_tip_to_lg_angle(Y_lg, l_landing_gear, wing_height_from_centre_line, wing_span)
        return phi - phi_min   
    

    constraints = [                                           
        {'type': 'ineq', 'fun': constraint_scrape_near},
        {'type': 'ineq', 'fun': constraint_scrape_far},
        {'type': 'ineq', 'fun': constraint_beta_scrape},
        {'type': 'ineq', 'fun': constraint_turnover},
        {'type': 'ineq', 'fun': constraint_keel_clearance},
        {'type': 'ineq', 'fun': constraint_main_lg_behind_cg},
        {'type': 'ineq', 'fun': constraint_main_lg_ahead_tail_cone},
        {'type': 'ineq', 'fun': constraint_Y_lg_min},
        {'type': 'ineq', 'fun': constraint_wing_tip_clearance},
    ]

    x0 = [R*1.25, x_cg_from_nose*1.01, R*1.25]

    result = opti.minimize(
        objective,
        x0,
        method='SLSQP',
        constraints=constraints,
        options={'ftol': 1e-9, 'disp': True, 'maxiter': 1000}
    )

    if not result.success:
        print(f"Warning: optimiser did not converge — {result.message}")

    l_opt, x_mlg_opt, Y_lg_opt = result.x
    x_nlg_opt = nose_gear_pos(x_mlg_opt)

    if debug:
        return l_opt, x_mlg_opt, Y_lg_opt, x_nlg_opt, constraints, result

    return l_opt, x_mlg_opt, Y_lg_opt, x_nlg_opt


if __name__ == '__main__': # Will only run if this file is run directly

    # Small note: 
    # please let me know if the optimiser works. I don't have values to test it with.

    L1=.3
    L2=.3
    L3=.3
    x_cg=.5
    up_sweep_angle_rad=15 * np.pi / 180
    diameter_fuselage=.15
    wing_height_from_centre_line=-.075
    wing_span=8.0


    l_opt, x_mlg_opt, Y_lg_opt, x_nlg_opt, constr, res = lg_pos_and_length(
        L1, L2, L3, x_cg, up_sweep_angle_rad, diameter_fuselage,
        wing_height_from_centre_line, wing_span, debug=True
    )

    print(f"Strut length  l_gear : {l_opt:.4f} m")
    print(f"MLG x-position       : {x_mlg_opt:.4f} m from nose")
    print(f"MLG lateral track    : {Y_lg_opt:.4f} m from centreline")
    print(f"NLG x-position       : {x_nlg_opt:.4f} m from nose")

    for c in constr:
        print(c['fun'](res.x))



"""
### Results for the above values. This is super not correct

l_opt, x_mlg_opt, Y_lg_opt, x_nlg_opt = lg_pos_and_length(
        L1, L2, L3, x_cg, up_sweep_angle, diameter_fuselage,
        wing_height_from_centre_line, wing_span
    )

    print(f"Strut length  l_gear : {l_opt:.4f} m")
    print(f"MLG x-position       : {x_mlg_opt:.4f} m from nose")
    print(f"MLG lateral track    : {Y_lg_opt:.4f} m from centreline")
    print(f"NLG x-position       : {x_nlg_opt:.4f} m from nose")

"""