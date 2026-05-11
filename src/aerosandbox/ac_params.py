import aerosandbox.numpy as np

g = 9.81 #m/s^2, gravitational acceleration

def sweep_le_to_qc_deg(sweep_le_deg, aspect_ratio, taper):
    sweep_le = np.radians(sweep_le_deg)
    return np.rad2deg(np.arctan(np.tan(sweep_le) - (1-taper)/(aspect_ratio*(1+taper))))
#--------------------------------------WING PLANFORMS--------------------------------------
# DAST ARW-2 input parameters
b_DAST = 5.79 #m
AR_DAST = 10.3
lambda_DAST = 0.4
Lambda_LE_DAST = 28.8 #degrees
Lambda_qc_DAST = sweep_le_to_qc_deg(Lambda_LE_DAST, AR_DAST, lambda_DAST) # radians
tip_twist_DAST = 0 #radians, tip twist of DAST ARW-2

# X-56A input parameters
b_X = 8.53
AR_X = 14
lambda_X = 0.46
Lambda_LE_X = 22.0 #degrees
Lambda_qc_X = sweep_le_to_qc_deg(Lambda_LE_X, AR_X, lambda_X) # radians
tip_twist_X = 0 #radians, tip twist of X-56A

# HUGO requirements
b_HUGO = 3.36
AR_HUGO = 23
lambda_HUGO = 0.5
Lambda_LE_HUGO = 15 #degrees
Lambda_qc_HUGO = sweep_le_to_qc_deg(Lambda_LE_HUGO, AR_HUGO, lambda_HUGO) # radians
tip_twist_HUGO = 0 #radians, tip twist of HUGO

#--------------------------------------AIRCRAFT PARAMETERS--------------------------------------
# NASA DAST ARW-2
m_DAST = 1060 #kg, mass of DAST ARW-2
# NASA X-56A
m_X = 238 #kg, mass of X-56A
# HUGO
m_HUGO = 50 #kg, mass of HUGO
W_over_S_HUGO = 1000 #N/m^2, wing loading of HUGO
horizontal_stabilizer_distance_from_wing_HUGO = 3.0 #m, distance from wing to horizontal stabilizer of HUGO
vertical_stabilizer_distance_from_wing_HUGO = 3.0 #m, distance
canard_distance_in_front_of_wing=0.5 #m, distance from wing to canard of HUGO

#--------------------------------------HORIZONTAL STABILIZER PARAMETERS-------------------------------------------
# NASA DAST ARW-2

# NASA X-56A

# HUGO
HT_AR_HUGO=3.0
HT_span_HUGO=0.5
HT_sweep_quarter_deg_HUGO=45.0
HT_taper_HUGO=1.0
HT_tip_twist_rad_HUGO=0.0

#--------------------------------------VERTICAL STABILIZER PARAMETERS-------------------------------------------
# NASA DAST ARW-2

# NASA X-56A

# HUGO
VT_AR_HUGO=1.5
VT_span_HUGO=0.5
VT_sweep_quarter_deg_HUGO=45.0
VT_taper_HUGO=1.0
VT_tip_twist_rad_HUGO=0.0

#--------------------------------------CANARD PARAMETERS-------------------------------------------
# NASA DAST ARW-2

# NASA X-56A

# HUGO
CN_AR_HUGO=3.0
CN_span_HUGO=0.5
CN_sweep_quarter_deg_HUGO=45.0
CN_taper_HUGO=1.0
CN_tip_twist_rad_HUGO=0.0