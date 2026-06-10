import numpy as np
import scipy as sp


# Points read off from Tau curve provided in ADSEE II slides. 
tau_points = np.array([[0.0, 0.0],
                      [0.2, 0.4],
                      [0.4, 0.6],
                      [0.7, 0.8]])

tau_points_x = tau_points[:,0]
tau_points_y = tau_points[:,1]

def tau_test_curve(x, a, b, c):
    return a * np.log(b*x + 1) + c

params, params_cov = sp.optimize.curve_fit(tau_test_curve, tau_points_x, tau_points_y)

def tau_func(x):

    a = 0.43943553769511473
    b = 7.359771100976851
    c = 0.00024515037357336454

    return a * np.log(b*x + 1) + c