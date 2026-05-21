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
        dy = tail_point[1]
        dx = tail_point[0] - x_main_lg
        return np.arctan2(dy, dx) 

    def beta_angle(x_main_lg, l_landing_gear):
        return np.arctan2(x_main_lg - x_cg_from_nose, l_landing_gear)

    def nose_gear_pos(l_landing_gear):
        # Dynamic calculation: Since it retracts forwards, the pivot point (x_nose_lg) 
        # must be at least one gear-length away from the nose tip (L1 * 0.1)
        # Plus an arbitrary small margin (e.g., 0.05m) for structural clearance.
        x_nose_tip_clearance = L1 * 0.1
        return x_nose_tip_clearance + l_landing_gear + 0.05

    def nose_gear_load_fraction(x_main_lg, l_landing_gear):
        x_nlg = nose_gear_pos(l_landing_gear)
        # Static weight fraction on nose gear = (x_mlg - x_cg) / (x_mlg - x_nlg)
        return (x_main_lg - x_cg_from_nose) / (x_main_lg - x_nlg)

    def turn_over_angle(x_main_lg, Y_lg, l_landing_gear):
        x_nlg = nose_gear_pos(l_landing_gear)
        d = x_main_lg - x_nlg
        alpha = np.arctan2(Y_lg, d)                       
        c = (x_cg_from_nose - x_nlg) * np.sin(alpha)
        psi = np.arctan2(l_landing_gear, c)
        return psi
    
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
        return beta_angle(x_main_lg, l_landing_gear) - theta

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
        return x_cone_start + L3 - x_main_lg

    def constraint_Y_lg_min(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return Y_lg - R
    
    def constraint_wing_tip_clearance(v):
        l_landing_gear, x_main_lg, Y_lg = v
        phi = wing_tip_to_lg_angle(Y_lg, l_landing_gear, wing_height_from_centre_line, wing_span)
        return phi - phi_min   
    
    def constraint_nose_load_min(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return nose_gear_load_fraction(x_main_lg, l_landing_gear) - 0.08

    def constraint_nose_load_max(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return 0.15 - nose_gear_load_fraction(x_main_lg, l_landing_gear)

    def constraint_nose_gear_behind_cg(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return x_cg_from_nose - nose_gear_pos(l_landing_gear)


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
        # {'type': 'ineq', 'fun': constraint_nose_load_min},
        # {'type': 'ineq', 'fun': constraint_nose_load_max},
        {'type': 'ineq', 'fun': constraint_nose_gear_behind_cg},
    ]

    x0 = [R*1.5, x_cg_from_nose*1.05, R*1.5]

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
    x_nlg_opt = nose_gear_pos(l_opt)

    if debug:
        return l_opt, x_mlg_opt, Y_lg_opt, x_nlg_opt, constraints, result

    return l_opt, x_mlg_opt, Y_lg_opt, x_nlg_opt


if __name__ == '__main__':

    L1 = 1.0
    L2 = 1.5
    L3 = 0.8
    x_cg = 1.6
    up_sweep_angle_rad = 15 * np.pi / 180
    diameter_fuselage = 0.315
    wing_height_from_centre_line = -0.315 / 2
    wing_span = 6.0

    l_opt, x_mlg_opt, Y_lg_opt, x_nlg_opt, constr, res = lg_pos_and_length(
        L1, L2, L3, x_cg, up_sweep_angle_rad, diameter_fuselage,
        wing_height_from_centre_line, wing_span, debug=True
    )

    print("\n--- Optimized Configurations ---")
    print(f"Strut length  l_gear : {l_opt:.4f} m")
    print(f"MLG x-position       : {x_mlg_opt:.4f} m from nose")
    print(f"MLG lateral track    : {Y_lg_opt:.4f} m from centreline")
    print(f"NLG x-position       : {x_nlg_opt:.4f} m from nose")

    print("\n--- Constraint Violations (Negative values mean violated) ---")
    for c in constr:
        print(f"{c['fun'].__name__}: {c['fun'](res.x):.6f}")