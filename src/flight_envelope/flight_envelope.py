import numpy as np
import matplotlib.pyplot as plt
import os
import sys

current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_file))
sys.path.append(project_root)
from objects.aircraft_parameters import AircraftParameters
from objects.wing_planform import WingPlanform
from global_parameters import CONSTANTS, Assumptions

class FlightEnvelope:
    def __init__(self,
                 CONSTANTS: CONSTANTS,
                 assumptions: Assumptions,
                 ):

        self.positive_manoeuvring_limit_load_factor=6.0 #CS-23, aerobatic
        self.negative_manoeuvring_limit_load_factor=-0.5*self.positive_manoeuvring_limit_load_factor #CS-23, aerobatic


    def kts_to_mps(self,
                   speed_kts):
        
        return 0.514444444*speed_kts


    def fps_to_mps(self,
                   speed_fps):
        
        return 0.3048*speed_fps


    def V_stall(self,
                aircraft_parameters: AircraftParameters,
                wing_planform: WingPlanform,
                C_L_max: float):
        
        return np.sqrt(2*aircraft_parameters.total_mass*CONSTANTS.G0/CONSTANTS.AIR_DENSITY_SEA_LEVEL/wing_planform.wing_area/abs(C_L_max))
    

    def compute_design_speeds(self,
                              aircraft_parameters: AircraftParameters,
                              wing_planform: WingPlanform,
                              assumptions: Assumptions,
                              ):
    
        self.minimum_cruising_speed=2.4*np.sqrt(aircraft_parameters.total_mass*CONSTANTS.G0/wing_planform.wing_area)
        self.design_cruising_speed=np.sqrt(assumptions.AIR_DENSITY_CRUISE_ALTITUDE/CONSTANTS.AIR_DENSITY_SEA_LEVEL)*assumptions.MC*np.sqrt(CONSTANTS.GAMMA_AIR*CONSTANTS.GAS_CONSTANT_AIR*assumptions.TEMPERATURE_CRUISE_ALTITUDE)
        if self.design_cruising_speed< self.minimum_cruising_speed:
            self.design_cruising_speed=self.minimum_cruising_speed

        self.design_diving_speed=1.25*self.design_cruising_speed*assumptions.MD/assumptions.MC


    def load_factor_upper_manoeuvre_curve(self,
                                          speed:np.ndarray,
                                          wing_planform:WingPlanform,
                                          aircraft_parameters:AircraftParameters,
                                          assumptions: Assumptions):
        
        return 0.5*CONSTANTS.AIR_DENSITY_SEA_LEVEL*speed**2*wing_planform.wing_area*assumptions.positive_C_L_max/(aircraft_parameters.total_mass*CONSTANTS.G0)


    def load_factor_lower_manoeuvre_curve(self,
                                          speed:np.ndarray,
                                          wing_planform:WingPlanform,
                                          aircraft_parameters:AircraftParameters,
                                          assumptions: Assumptions):
        
        return 0.5*CONSTANTS.AIR_DENSITY_SEA_LEVEL*speed**2*wing_planform.wing_area*assumptions.negative_C_L_max/(aircraft_parameters.total_mass*CONSTANTS.G0)


    def delta_load_factor_gust_curve(self,
                                     speed:np.ndarray,
                                     wing_planform:WingPlanform,
                                     aircraft_parameters:AircraftParameters,
                                     assumptions: Assumptions,
                                     condition: str='cruise' or 'dive'):

        mu_g=(2*aircraft_parameters.total_mass)/(assumptions.AIR_DENSITY_CRUISE_ALTITUDE*wing_planform.MAC*assumptions.C_L_alpha*wing_planform.wing_area)
        K_g=(0.88*mu_g)/(5.3+mu_g)

        assert (condition=='cruise' or condition=='dive'), 'Specify a valid condition!'

        if condition=='cruise':
            derived_gust_velocity=50.0
            if assumptions.ALTITUDE_CRUISE>6096.0:
                derived_gust_velocity+=(25.0-50.0)/(15240.0-6096.0)*(assumptions.ALTITUDE_CRUISE-6096.0)
            derived_gust_velocity=self.fps_to_mps(derived_gust_velocity)

        elif condition=='dive':
            derived_gust_velocity=25.0
            if assumptions.ALTITUDE_CRUISE>6096.0:
                derived_gust_velocity+=(12.5-25.0)/(15240.0-6096.0)*(assumptions.ALTITUDE_CRUISE-6096.0)
            derived_gust_velocity=self.fps_to_mps(derived_gust_velocity)
        
        return K_g*CONSTANTS.AIR_DENSITY_SEA_LEVEL*derived_gust_velocity*speed*assumptions.C_L_alpha/(2*aircraft_parameters.total_mass*CONSTANTS.G0/wing_planform.wing_area)

    
    def plot_V_n_diagram(self,
                         aircraft_parameters: AircraftParameters,
                         wing_planform: WingPlanform,
                         assumptions: Assumptions):

        positive_stall_speed=np.sqrt(aircraft_parameters.total_mass*CONSTANTS.G0/(0.5*CONSTANTS.AIR_DENSITY_SEA_LEVEL*wing_planform.wing_area*assumptions.positive_C_L_max))
        negative_stall_speed=np.sqrt(aircraft_parameters.total_mass*CONSTANTS.G0/(0.5*CONSTANTS.AIR_DENSITY_SEA_LEVEL*wing_planform.wing_area*abs(assumptions.negative_C_L_max)))
        stall_speed_at_max_positive_manoeuvre_load=np.sqrt(self.positive_manoeuvring_limit_load_factor*aircraft_parameters.total_mass*CONSTANTS.G0/(0.5*CONSTANTS.AIR_DENSITY_SEA_LEVEL*wing_planform.wing_area*assumptions.positive_C_L_max))
        stall_speed_at_min_negative_manoeuvre_load=np.sqrt(abs(self.negative_manoeuvring_limit_load_factor)*aircraft_parameters.total_mass*CONSTANTS.G0/(0.5*CONSTANTS.AIR_DENSITY_SEA_LEVEL*wing_planform.wing_area*abs(assumptions.negative_C_L_max)))

        # load_factor_manoeuvre_envelope = []
        # speed_manoeuvre_envelope=[]
        _A_curve_load = []
        _A_curve_speed=[]
        _K_curve_load = []
        _K_curve_speed=[]
        A_B_curve_load=[]
        A_B_curve_speed=[]
        K_J_curve_load=[]
        K_J_curve_speed=[]
        B_F_curve_load=[]
        B_F_curve_speed=[]
        J_G_curve_load=[]
        J_G_curve_speed=[]
        G_dive_speed=[]
        G_dive_load=[]
        F_G_curve_load=[]
        F_G_curve_speed=[]

        _A_curve_speed.extend(list(np.linspace(0.0,positive_stall_speed,1000)))
        _A_curve_load.extend(self.load_factor_upper_manoeuvre_curve(np.array(_A_curve_speed),
                                                                             wing_planform,
                                                                             aircraft_parameters,
                                                                             assumptions))

        _K_curve_speed.extend(list(np.linspace(0.0,negative_stall_speed,1000)))
        _K_curve_load.extend(self.load_factor_lower_manoeuvre_curve(np.array(_K_curve_speed),
                                                                             wing_planform,
                                                                             aircraft_parameters,
                                                                             assumptions))

        A_B_curve_speed.extend(list(np.linspace(positive_stall_speed,
                                               stall_speed_at_max_positive_manoeuvre_load,
                                               1000)))
        A_B_curve_load.extend(self.load_factor_upper_manoeuvre_curve(np.array(A_B_curve_speed),
                                                                              wing_planform,
                                                                              aircraft_parameters,
                                                                              assumptions))

        K_J_curve_speed.extend(list(np.linspace(negative_stall_speed,
                                               stall_speed_at_min_negative_manoeuvre_load,
                                               1000)))
        K_J_curve_load.extend(self.load_factor_lower_manoeuvre_curve(np.array(K_J_curve_speed),
                                                                              wing_planform,
                                                                              aircraft_parameters,
                                                                              assumptions))
        
        B_F_curve_speed.extend([stall_speed_at_max_positive_manoeuvre_load,self.design_diving_speed])
        B_F_curve_load.extend([self.positive_manoeuvring_limit_load_factor,self.positive_manoeuvring_limit_load_factor])
        
        J_G_curve_speed.extend([stall_speed_at_min_negative_manoeuvre_load,self.design_cruising_speed])
        J_G_curve_load.extend([self.negative_manoeuvring_limit_load_factor,self.negative_manoeuvring_limit_load_factor])

        G_dive_speed.extend([self.design_cruising_speed, self.design_diving_speed])
        G_dive_load.extend([self.negative_manoeuvring_limit_load_factor,-1.0]) #CS-23.333 b) 3)
        
        F_G_curve_speed.extend([self.design_diving_speed,self.design_diving_speed])
        F_G_curve_load.extend([-1.0, self.positive_manoeuvring_limit_load_factor])
        
        gust_cruise_upper_speed=[]
        gust_cruise_lower_speed=[]
        gust_dive_upper_speed=[]
        gust_dive_lower_speed=[]
        gust_cruise_upper_load_factor=[]
        gust_cruise_lower_load_factor=[]
        gust_dive_upper_load_factor=[]
        gust_dive_lower_load_factor=[]
        gust_CD_speed=[]
        gust_CD_load=[]
        gust_D_dive_speed=[]
        gust_D_dive_load=[]
        gust_IL_speed=[]
        gust_IL_load=[]
        gust_L_dive_speed=[]
        gust_L_dive_load=[]

        gust_cruise_upper_speed.extend(list(np.linspace(0.0, self.design_diving_speed+1, 1000)))
        gust_cruise_lower_speed.extend(list(np.linspace(0.0, self.design_diving_speed+1, 1000)))
        gust_dive_upper_speed.extend(list(np.linspace(0.0, self.design_diving_speed+1, 1000)))
        gust_dive_lower_speed.extend(list(np.linspace(0.0, self.design_diving_speed+1, 1000)))

        gust_cruise_upper_load_factor.extend(list(1+self.delta_load_factor_gust_curve(np.linspace(0.0,self.design_diving_speed+1,1000),
                                                                                wing_planform=wing_planform,
                                                                                aircraft_parameters=aircraft_parameters,
                                                                                assumptions=assumptions,
                                                                                condition='cruise')))

        gust_cruise_lower_load_factor.extend(list(1-self.delta_load_factor_gust_curve(np.linspace(0.0,self.design_diving_speed+1,1000),
                                                                                wing_planform=wing_planform,
                                                                                aircraft_parameters=aircraft_parameters,
                                                                                assumptions=assumptions,
                                                                                condition='cruise')))

        gust_dive_upper_load_factor.extend(list(1+self.delta_load_factor_gust_curve(np.linspace(0.0,self.design_diving_speed+1,1000),
                                                                                wing_planform=wing_planform,
                                                                                aircraft_parameters=aircraft_parameters,
                                                                                assumptions=assumptions,
                                                                                condition='dive')))

        gust_dive_lower_load_factor.extend(list(1-self.delta_load_factor_gust_curve(np.linspace(0.0,self.design_diving_speed+1,1000),
                                                                                wing_planform=wing_planform,
                                                                                aircraft_parameters=aircraft_parameters,
                                                                                assumptions=assumptions,
                                                                                condition='dive')))
        upper_gust_intersection_speed=gust_cruise_upper_speed[np.argmin(np.abs(np.array(gust_cruise_upper_load_factor)-self.positive_manoeuvring_limit_load_factor))]
        lower_gust_intersection_speed=gust_cruise_lower_speed[np.argmin(np.abs(np.array(gust_cruise_lower_load_factor)-self.negative_manoeuvring_limit_load_factor))]
        

        if upper_gust_intersection_speed<self.design_cruising_speed:
            gust_CD_speed.extend([upper_gust_intersection_speed,self.design_cruising_speed])
            gust_CD_load.extend([self.positive_manoeuvring_limit_load_factor,1+self.delta_load_factor_gust_curve(self.design_cruising_speed,
                                                                                wing_planform=wing_planform,
                                                                                aircraft_parameters=aircraft_parameters,
                                                                                assumptions=assumptions,
                                                                                condition='cruise')])
            gust_D_dive_speed.extend([self.design_cruising_speed,self.design_diving_speed])
            gust_D_dive_load.extend([1+self.delta_load_factor_gust_curve(self.design_cruising_speed,
                                                                                wing_planform=wing_planform,
                                                                                aircraft_parameters=aircraft_parameters,
                                                                                assumptions=assumptions,
                                                                                condition='cruise'),
                                     1+self.delta_load_factor_gust_curve(self.design_diving_speed,
                                                                                wing_planform=wing_planform,
                                                                                aircraft_parameters=aircraft_parameters,
                                                                                assumptions=assumptions,
                                                                                condition='dive')])
            
        if lower_gust_intersection_speed<self.design_cruising_speed:
            gust_IL_speed.extend([lower_gust_intersection_speed,self.design_cruising_speed])
            gust_IL_load.extend([self.negative_manoeuvring_limit_load_factor,1-self.delta_load_factor_gust_curve(self.design_cruising_speed,
                                                                                wing_planform=wing_planform,
                                                                                aircraft_parameters=aircraft_parameters,
                                                                                assumptions=assumptions,
                                                                                condition='cruise')])
            gust_L_dive_speed.extend([self.design_cruising_speed,self.design_diving_speed])
            gust_L_dive_load.extend([1-self.delta_load_factor_gust_curve(self.design_cruising_speed,
                                                                                wing_planform=wing_planform,
                                                                                aircraft_parameters=aircraft_parameters,
                                                                                assumptions=assumptions,
                                                                                condition='cruise'),
                                     1-self.delta_load_factor_gust_curve(self.design_diving_speed,
                                                                                wing_planform=wing_planform,
                                                                                aircraft_parameters=aircraft_parameters,
                                                                                assumptions=assumptions,
                                                                                condition='dive')])


        plt.plot([negative_stall_speed]*100,
                 np.linspace(self.negative_manoeuvring_limit_load_factor-0.5,self.positive_manoeuvring_limit_load_factor+0.5,100),
                 'r--',
                 linewidth=1,
                 )
        plt.plot([positive_stall_speed]*100,
                 np.linspace(self.negative_manoeuvring_limit_load_factor-0.5,self.positive_manoeuvring_limit_load_factor+0.5,100),
                 'r--',
                 linewidth=1,
                 )
        plt.plot([self.design_cruising_speed]*100,
                 np.linspace(self.negative_manoeuvring_limit_load_factor-0.5,self.positive_manoeuvring_limit_load_factor+0.5,100),
                 'r--',
                 linewidth=1,
                 )
        plt.plot([self.design_diving_speed]*100,
                 np.linspace(self.negative_manoeuvring_limit_load_factor-0.5,self.positive_manoeuvring_limit_load_factor+0.5,100),
                 'r--',
                 linewidth=1,
                 )

        plt.plot(A_B_curve_speed, A_B_curve_load, 'b-', linewidth=1, label='Manoeuvre loads')
        plt.plot(B_F_curve_speed, B_F_curve_load, 'b-', linewidth=1)
        plt.plot(F_G_curve_speed, F_G_curve_load, 'b-', linewidth=1)
        plt.plot(K_J_curve_speed, K_J_curve_load, 'b-', linewidth=1)
        plt.plot(J_G_curve_speed, J_G_curve_load, 'b-', linewidth=1)
        plt.plot(G_dive_speed, G_dive_load, 'b-', linewidth=1)
        plt.plot(_A_curve_speed,_A_curve_load, 'b--',linewidth=1)
        plt.plot(_K_curve_speed,_K_curve_load, 'b--',linewidth=1)
        plt.plot([positive_stall_speed, positive_stall_speed],[0.0,1.0], 'b-',linewidth=1)
        plt.plot([negative_stall_speed, negative_stall_speed],[0.0,-1.0], 'b-',linewidth=1)

        #Gust loads
        plt.plot(np.linspace(0.0, self.design_diving_speed+1, 1000),
                gust_cruise_upper_load_factor, 'g-.', linewidth=1, label='Gust loads')

        plt.plot(np.linspace(0.0, self.design_diving_speed+1, 1000),
                gust_cruise_lower_load_factor, 'g-.', linewidth=1)

        plt.plot(np.linspace(0.0, self.design_diving_speed+1, 1000),
                gust_dive_upper_load_factor, 'g-.', linewidth=1)

        plt.plot(np.linspace(0.0, self.design_diving_speed+1, 1000),
                gust_dive_lower_load_factor, 'g-.', linewidth=1)
        
        if upper_gust_intersection_speed<self.design_cruising_speed:
            plt.plot(gust_CD_speed, gust_CD_load, 'g-',linewidth=1,label='Gust envelope')
            plt.plot(gust_D_dive_speed, gust_D_dive_load, 'g-',linewidth=1)
        if lower_gust_intersection_speed<self.design_cruising_speed:
            plt.plot(gust_IL_speed, gust_IL_load, 'g-',linewidth=1)
            plt.plot(gust_L_dive_speed, gust_L_dive_load, 'g-',linewidth=1)

        # plt.xticks(np.arange(self.negative_manoeuvring_limit_load_factor-0.5,
        #                      self.positive_manoeuvring_limit_load_factor+0.5,
        #                      20))
        # plt.yticks(np.arange(0.0,self.minimum_design_dive_speed+5.0,100))
        plt.minorticks_on()
        plt.grid(True, which='both')
        plt.legend()
        #plt.title('V-n diagram')
        plt.ylabel('Load factor')
        plt.xlabel('EAS [m/s]')
        plt.show()
        plt.close()

if __name__=='__main__':
    aircraft_parameters=AircraftParameters(
    total_mass=50.0,  
)

    wing_planform=WingPlanform(
        aspect_ratio=25.0,
        span=2.0,
        sweep_quarter_deg=45.0,
        taper=1.0,
)

    constants=CONSTANTS()

    assumptions = Assumptions()
    assumptions.ALTITUDE_CRUISE = 5500.0 # [m] (up for review)
    assumptions.AIR_DENSITY_CRUISE_ALTITUDE = 0.695 # [kg/m^3]
    assumptions.positive_C_L_max=1.6 #CHANGE
    assumptions.negative_C_L_max=-1.0 #CHANGE
    assumptions.C_L_alpha = 3.0 #CHANGE
    assumptions.MC=0.75 #cruise Mach number
    assumptions.MD = 0.80 #ADSEE: in general, MD is 0.05M higher than MC

    flight_envelope=FlightEnvelope(constants,
                                   assumptions)
    flight_envelope.positive_manoeuvring_limit_load_factor=6.0
    flight_envelope.negative_manoeuvring_limit_load_factor=-0.5*flight_envelope.positive_manoeuvring_limit_load_factor
    flight_envelope.compute_design_speeds(aircraft_parameters,
                                          wing_planform,
                                          assumptions)
    flight_envelope.plot_V_n_diagram(aircraft_parameters,
                                     wing_planform,
                                     assumptions)



    
