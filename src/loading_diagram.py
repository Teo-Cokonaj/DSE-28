import numpy as np
from objects.aircraft_parameters import AircraftParameters
from objects.wing_planform import WingPlanform

aircraft_parameters=AircraftParameters(
    total_mass=50,
    fuselage_length=3,   
)

wing_planform=WingPlanform(
    aspect_ratio=20.0,
    span=10.0,
    sweep_quarter_deg=45,
    taper=0.4
)

C_L_max=1.0
C_L_alpha = 0.7*2*np.pi
rho=1.225
load_factor=3.8
delta_alpha=1.0 #1/rad
V_C= 100.0 #cruise_speed
V_dive=160.0 #dive speed
V_max=150.0
V_ge=10.0


C_mgc=wing_planform.wing_area/wing_planform.span
mu_g=(2*aircraft_parameters.total_mass)/(rho*C_mgc*C_L_alpha*wing_planform.wing_area)
K_g=(0.88*mu_g)/(5.3+mu_g)

V_cruise_min = np.sqrt(aircraft_parameters.total_mass*9.80665/wing_planform.wing_area) #CS-VLA 335

V_stall = np.sqrt(2*aircraft_parameters.total_mass*9.80665/rho/wing_planform.wing_area/C_L_max)

V_manoeuvre=np.sqrt(load_factor*aircraft_parameters.total_mass*9.80665/rho/0.5/C_L_max/wing_planform.wing_area)

delta_n_gust_cruise=(K_g*V_ge*V_C*delta_alpha*rho*wing_planform.wing_area)/(2*aircraft_parameters.total_mass*9.80665)

delta_n_gust_dive=(K_g*V_ge*V_dive*delta_alpha*rho*wing_planform.wing_area)/(2*aircraft_parameters.total_mass*9.80665)

