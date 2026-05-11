import aerosandbox.numpy as np
import aerosandbox as asb
import objects.lifting_surface_planform as lsp
g = 9.81 #m/s^2, gravitational acceleration

def sweep_le_to_qc_deg(sweep_le_deg, aspect_ratio, taper):
    sweep_le = np.radians(sweep_le_deg)
    return np.rad2deg(np.arctan(np.tan(sweep_le) - (1-taper)/(aspect_ratio*(1+taper))))
#--------------------------------------WING PLANFORMS--------------------------------------
# DAST ARW-2 input parameters
b_d = 5.79 #m
AR_d = 10.3
lambda_d = 0.4
Lambda_LE_d = 28.8 #degrees
Lambda_qc_d = sweep_le_to_qc_deg(Lambda_LE_d, AR_d, lambda_d) # radians
tip_twist_d = 0 #radians, tip twist of DAST ARW-2

# X-56A input parameters
b_x = 8.53
AR_x = 14
lambda_x = 0.46
Lambda_LE_x = 22.0 #degrees
Lambda_qc_x = sweep_le_to_qc_deg(Lambda_LE_x, AR_x, lambda_x) # radians
tip_twist_x = 0 #radians, tip twist of X-56A

# HUGO requirements
b_h = 3.36
AR_h = 23
lambda_h = 0.5
Lambda_LE_h = 15 #degrees
Lambda_qc_h = sweep_le_to_qc_deg(Lambda_LE_h, AR_h, lambda_h) # radians
tip_twist_h = 0 #radians, tip twist of HUGO

#--------------------------------------AIRCRAFT PARAMETERS--------------------------------------
m_d = 1060 #kg, mass of DAST ARW-2

m_x = 238 #kg, mass of X-56A

m_h = 50 #kg, mass of HUGO
W_over_S_h = 1000 #N/m^2, wing loading of HUGO


HUGO_planform = lsp.LiftingSurfacePlanform(
    aspect_ratio=AR_h,
    span=b_h,
    sweep_quarter_deg=Lambda_qc_h,
    taper=lambda_h,
    tip_twist_rad=tip_twist_h,
)

print("HUGO planform parameters:")
print(f"Aspect Ratio: {HUGO_planform.aspect_ratio}")
print(f"Span: {HUGO_planform.span}")
print(f"Sweep at Quarter Chord: {np.degrees(HUGO_planform.sweep_quarter_rad)} degrees")
print(f"Taper Ratio: {HUGO_planform.taper}")
print(f"Tip Twist: {np.degrees(HUGO_planform.tip_twist_rad)} degrees")