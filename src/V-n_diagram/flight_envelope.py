import numpy as np
import matplotlib.pyplot as plt
import os
import sys

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_file))
sys.path.append(project_root)
from objects.aircraft_parameters import AircraftParameters
from objects.wing_planform import WingPlanform

positive_C_L_max=1.6 #CHANGE
negative_C_L_max=-0.8 #CHANGE
C_L_alpha = 0.5*2*np.pi #CHANGE
rho_SL=1.225 #sea-level air density
MC=0.75 #cruise Mach number
MD = 0.80 #ADSEE: in general, MD is 0.05M higher than MC
V_H_sea_level= MC*np.sqrt(1.4*287*273.15) #maximum speed in level flight with maximum continuous power #CHANGE
air_density=1.225 #kg/m^3
altitude=0.0 #m

positive_manoeuvring_limit_load_factor=6.0 #CS-23, aerobatic
negative_manoeuvring_limit_load_factor=-0.5*positive_manoeuvring_limit_load_factor #CS-23, aerobatic

aircraft_parameters=AircraftParameters(
    total_mass=50.0,
    fuselage_length=3.0,   
)

wing_planform=WingPlanform(
    aspect_ratio=25.0,
    span=10.0,
    sweep_quarter_deg=45,
    taper=0.4
)


def kts_to_mps(speed_kts):
    return 0.51445*speed_kts


def fps_to_mps(speed_fps):
    return 0.3048*speed_fps


def V_C_min(V_H_sea_level: float,
            aircraft_parameters: AircraftParameters,
            wing_planform: WingPlanform):
    wing_loading = aircraft_parameters.total_mass*9.80665/wing_planform.wing_area
    if wing_loading > 20.0:
        factor = 36 + (28.6-36.0)/(100.0-20.0)*(wing_loading-20.0)
        print('Factor: ',factor)
    factor=36.0
    
    speed = kts_to_mps(factor*np.sqrt(wing_loading))
    if speed>V_H_sea_level:
        speed=V_H_sea_level
    print('V_C_min: ',V_C_min)
    return speed


# def V_D_min(V_H_sea_level: float,
#             aircraft_parameters: AircraftParameters,
#             wing_planform: WingPlanform):
#     speed = 1.25*MD*(VC/MC)
#     factor = 1.55
#     wing_loading = aircraft_parameters.total_mass*9.80665/wing_planform.wing_area
#     if wing_loading > 20.0:
#         factor = 1.55 + (1.35-1.55)/(100.0-20.0)*(wing_loading-20.0)
    
#     speed=min(factor*VCmin,speed) ##Add additional conditions related to VCmin
#     return speed          


def V_stall(aircraft_parameters:AircraftParameters,
            wing_planform: WingPlanform,
            C_L_max: float):
    return np.sqrt(2*aircraft_parameters.total_mass*9.80665/1.225/wing_planform.wing_area/abs(C_L_max))


def V_A_min(stall_speed: float,
            limit_manoeuvring_load_factor: float,
            minimum_design_cruising_speed: float):
    speed=stall_speed*np.sqrt(limit_manoeuvring_load_factor)
    if speed>minimum_design_cruising_speed:
        speed=minimum_design_cruising_speed
    return speed
   

def load_factor_upper_manoeuvre_curve(speed:np.ndarray,
                                      wing_planform:WingPlanform,
                                      aircraft_parameters:AircraftParameters):
    return 0.5*1.225*speed**2*wing_planform.wing_area*positive_C_L_max/(aircraft_parameters.total_mass*9.80665)


def load_factor_lower_manoeuvre_curve(speed:np.ndarray,
                                      wing_planform:WingPlanform,
                                      aircraft_parameters:AircraftParameters):
    return 0.5*1.225*speed**2*wing_planform.wing_area*negative_C_L_max/(aircraft_parameters.total_mass*9.80665)


def delta_load_factor_gust_curve(
                           speed:np.ndarray,
                           air_density: float,
                           altitude: float,
                           lift_curve_slope_per_rad: float,
                           wing_planform:WingPlanform,
                           aircraft_parameters:AircraftParameters,
                           condition: str='cruise' or 'dive',
                           ):
    
    mu_g=(2*aircraft_parameters.total_mass)/(air_density*wing_planform.MAC*C_L_alpha*wing_planform.wing_area)
    K_g=(0.88*mu_g)/(5.3+mu_g)

    assert (condition=='cruise' or condition=='dive'), 'Specify a valid condition!'

    if condition=='cruise':
        derived_gust_velocity=fps_to_mps(50.0)
        if altitude>6096.0:
            derived_gust_velocity+=(25.0-50.0)/(15240.0-6096.0)*(altitude-6096.0)

    elif condition=='dive':
        derived_gust_velocity=fps_to_mps(25.0)
        if altitude>6096.0:
            derived_gust_velocity+=(12.5-25.0)/(15240.0-6096.0)*(altitude-6096.0)
    #print(K_g*rho_SL*derived_gust_velocity*lift_curve_slope_per_rad/(2*aircraft_parameters.total_mass*9.80665/wing_planform.wing_area))
    print('-----')
    print(mu_g)
    print(K_g)
    print(rho_SL)
    print(derived_gust_velocity)
    print(lift_curve_slope_per_rad)
    print(aircraft_parameters.total_mass)
    print(wing_planform.wing_area)
    print('-----')
    
    return K_g*rho_SL*derived_gust_velocity*speed*lift_curve_slope_per_rad/(2*aircraft_parameters.total_mass*9.80665/wing_planform.wing_area)
    
print(f'Cruise speed between {2.4*np.sqrt(aircraft_parameters.total_mass*9.80665/wing_planform.wing_area)} and {V_C_min(V_H_sea_level,
                                         aircraft_parameters,
                                         wing_planform)}')
minimum_design_cruising_speed=min(2.4*np.sqrt(aircraft_parameters.total_mass*9.80665/wing_planform.wing_area),
                                 V_C_min(V_H_sea_level,
                                         aircraft_parameters,
                                         wing_planform))

minimum_design_dive_speed=1.40*minimum_design_cruising_speed

positive_stall_speed=np.sqrt(aircraft_parameters.total_mass*9.80665/(0.5*rho_SL*wing_planform.wing_area*positive_C_L_max))
negative_stall_speed=np.sqrt(aircraft_parameters.total_mass*9.80665/(0.5*rho_SL*wing_planform.wing_area*abs(negative_C_L_max)))
stall_speed_at_max_positive_manoeuvre_load=np.sqrt(positive_manoeuvring_limit_load_factor*aircraft_parameters.total_mass*9.80665/(0.5*rho_SL*wing_planform.wing_area*positive_C_L_max))
stall_speed_at_min_negative_manoeuvre_load=np.sqrt(abs(negative_manoeuvring_limit_load_factor)*aircraft_parameters.total_mass*9.80665/(0.5*rho_SL*wing_planform.wing_area*abs(negative_C_L_max)))

load_factor_manoeuvre_envelope = []
speed_manoeuvre_envelope=[]
A_B_curve_load=[]
A_B_curve_speed=[]
K_J_curve_load=[]
K_J_curve_speed=[]
B_F_curve_load=[]
B_F_curve_speed=[]
J_G_curve_load=[]
J_G_curve_speed=[]
F_G_curve_load=[]
F_G_curve_speed=[]

A_B_curve_load.extend(list(load_factor_upper_manoeuvre_curve(np.arange(positive_stall_speed,
                                                                      stall_speed_at_max_positive_manoeuvre_load,
                                                                      0.1),
                          wing_planform,
                          aircraft_parameters)))
A_B_curve_speed.extend(list(np.arange(positive_stall_speed,
                                        stall_speed_at_max_positive_manoeuvre_load,
                                        0.1)))
K_J_curve_load.extend(list(load_factor_lower_manoeuvre_curve(np.arange(negative_stall_speed,
                                                                      stall_speed_at_min_negative_manoeuvre_load,
                                                                      0.1),
                          wing_planform,
                          aircraft_parameters)))
K_J_curve_speed.extend(list(np.arange(negative_stall_speed,
                                        stall_speed_at_min_negative_manoeuvre_load,
                                        0.1)))


B_F_curve_load.extend([positive_manoeuvring_limit_load_factor]*100)
B_F_curve_speed.extend(list(np.linspace(stall_speed_at_max_positive_manoeuvre_load,minimum_design_dive_speed,100)))
J_G_curve_load.extend([negative_manoeuvring_limit_load_factor]*100)
J_G_curve_speed.extend(list(np.linspace(stall_speed_at_min_negative_manoeuvre_load,minimum_design_dive_speed,100)))
F_G_curve_load.extend(list(np.linspace(negative_manoeuvring_limit_load_factor,
                                       positive_manoeuvring_limit_load_factor,
                                       100)))
F_G_curve_speed.extend([minimum_design_dive_speed]*100)

gust_cruise_upper_load_factor=[]
gust_cruise_lower_load_factor=[]
gust_dive_upper_load_factor=[]
gust_dive_lower_load_factor=[]

gust_cruise_upper_load_factor.extend(list(1+delta_load_factor_gust_curve(np.linspace(0.0,minimum_design_cruising_speed,100),
                                                                         air_density=air_density,
                                                                         altitude=altitude,
                                                                         lift_curve_slope_per_rad=C_L_alpha,
                                                                         wing_planform=wing_planform,
                                                                         aircraft_parameters=aircraft_parameters,
                                                                         condition='cruise')))

gust_cruise_lower_load_factor.extend(list(1-delta_load_factor_gust_curve(np.linspace(0.0,minimum_design_cruising_speed,100),
                                                                         air_density=air_density,
                                                                         altitude=altitude,
                                                                         lift_curve_slope_per_rad=C_L_alpha,
                                                                         wing_planform=wing_planform,
                                                                         aircraft_parameters=aircraft_parameters,
                                                                         condition='cruise')))

gust_dive_upper_load_factor.extend(list(1+delta_load_factor_gust_curve(np.linspace(0.0,minimum_design_dive_speed,100),
                                                                         air_density=air_density,
                                                                         altitude=altitude,
                                                                         lift_curve_slope_per_rad=C_L_alpha,
                                                                         wing_planform=wing_planform,
                                                                         aircraft_parameters=aircraft_parameters,
                                                                         condition='dive')))

gust_dive_lower_load_factor.extend(list(1-delta_load_factor_gust_curve(np.linspace(0.0,minimum_design_dive_speed,100),
                                                                         air_density=air_density,
                                                                         altitude=altitude,
                                                                         lift_curve_slope_per_rad=C_L_alpha,
                                                                         wing_planform=wing_planform,
                                                                         aircraft_parameters=aircraft_parameters,
                                                                         condition='dive')))

# First five: thin blue lines
plt.plot(A_B_curve_speed, A_B_curve_load, 'b-', linewidth=1)
plt.plot(B_F_curve_speed, B_F_curve_load, 'b-', linewidth=1)
plt.plot(F_G_curve_speed, F_G_curve_load, 'b-', linewidth=1)
plt.plot(K_J_curve_speed, K_J_curve_load, 'b-', linewidth=1)
plt.plot(J_G_curve_speed, J_G_curve_load, 'b-', linewidth=1)

# Remaining: thin red lines
plt.plot(np.linspace(0.0, minimum_design_cruising_speed, 100),
         gust_cruise_upper_load_factor, 'r-', linewidth=1)

plt.plot(np.linspace(0.0, minimum_design_cruising_speed, 100),
         gust_cruise_lower_load_factor, 'r-', linewidth=1)

plt.plot(np.linspace(0.0, minimum_design_dive_speed, 100),
         gust_dive_upper_load_factor, 'r-', linewidth=1)

plt.plot(np.linspace(0.0, minimum_design_dive_speed, 100),
         gust_dive_lower_load_factor, 'r-', linewidth=1)

plt.grid()
plt.title('V-n diagram')
plt.ylabel('Load factor')
plt.xlabel('Speed')
plt.show()
plt.close()