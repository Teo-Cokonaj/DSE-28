import sys
import os
import scipy.optimize as opti
import aerosandbox.numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def lg_pos_and_length(L1, L2, L3, x_cg, up_sweep_angle, diameter_fuselage):

    sigma = up_sweep_angle * np.pi / 180
    theta = 15 * np.pi / 180

    x_cone_start = L1 + L2
    x_tail_tip   = L1 + L2 + L3
    R            = diameter_fuselage / 2

    def tail_point_near(l_landing_gear):
        return (x_cone_start, l_landing_gear - R)

    def tail_point_far(l_landing_gear):
        return (x_tail_tip, l_landing_gear - R + L3 * np.tan(sigma))

    def scrape_angle(x_main_lg, tail_point):
        return np.arctan2(tail_point[1], tail_point[0] - x_main_lg) 

    def beta_angle(x_main_lg, l_landing_gear):
        return np.arctan2(x_main_lg - x_cg, l_landing_gear)

    def nose_gear_pos(x_main_lg):
        return (x_cg - x_main_lg * 0.85) / 0.15

    def turn_over_angle(x_main_lg, Y_lg, l_landing_gear):
        x_nose_lg = nose_gear_pos(x_main_lg)
        d         = x_main_lg - x_nose_lg
        alpha     = np.arctan2(Y_lg, d)                       
        c         = (x_cg - x_nose_lg) * np.sin(alpha)
        return np.arctan2(c, l_landing_gear)

    def objective(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return l_landing_gear

    def constraint_scrape_near(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return scrape_angle(x_main_lg, tail_point_near(l_landing_gear)) - theta

    def constraint_scrape_far(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return scrape_angle(x_main_lg, tail_point_far(l_landing_gear)) - theta

    def constraint_beta_scrape(v):
        l_landing_gear, x_main_lg, Y_lg = v
        theta_crit = max(
            scrape_angle(x_main_lg, tail_point_near(l_landing_gear)),
            scrape_angle(x_main_lg, tail_point_far(l_landing_gear))
        )
        return beta_angle(x_main_lg, l_landing_gear) - theta_crit

    def constraint_turnover(v):                             
        l_landing_gear, x_main_lg, Y_lg = v
        psi_max = 55.0 * np.pi / 180
        return psi_max - turn_over_angle(x_main_lg, Y_lg, l_landing_gear)

    def constraint_keel_clearance(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return l_landing_gear - R - 0.05

    def constraint_main_lg_behind_cg(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return x_main_lg - x_cg

    def constraint_main_lg_ahead_tail_cone(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return x_cone_start - x_main_lg

    def constraint_Y_lg_min(v):
        l_landing_gear, x_main_lg, Y_lg = v
        return Y_lg - R

    constraints = [                                           
        {'type': 'ineq', 'fun': constraint_scrape_near},
        {'type': 'ineq', 'fun': constraint_scrape_far},
        {'type': 'ineq', 'fun': constraint_beta_scrape},
        {'type': 'ineq', 'fun': constraint_turnover},
        {'type': 'ineq', 'fun': constraint_keel_clearance},
        {'type': 'ineq', 'fun': constraint_main_lg_behind_cg},
        {'type': 'ineq', 'fun': constraint_main_lg_ahead_tail_cone},
        {'type': 'ineq', 'fun': constraint_Y_lg_min},
    ]

    x0 = [R + 1.0, x_cg + 1.0, R]

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

    return l_opt, x_mlg_opt, Y_lg_opt, x_nlg_opt




# Small note: 
# please let me know if the optimiser works. I don't have values to test it with.

L1 = 1
L2 = 2.5
L3 = 1.25
x_cg = 3
up_sweep_angle = 13
diameter_fuselage = 1



print(lg_pos_and_length(L1, L2, L3, x_cg, up_sweep_angle, diameter_fuselage))