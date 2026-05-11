import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import os
import sys
# current_file = os.path.abspath(__file__)
# project_root = os.path.dirname(os.path.dirname(current_file))
# sys.path.append(project_root)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aerodynamic_model.aircraft_model import make_airplane_model
from global_parameters import CONSTANTS, Assumptions
#import Drag.component_method as dcm
from flight_envelope.flight_envelope import FlightEnvelope
from objects.aircraft_parameters import AircraftParameters
from objects.lifting_surface_planform import LiftingSurfacePlanform


aircraft_parameters=AircraftParameters(total_mass=50.0,
                                           horizontal_stabilizer_distance_from_wing=3.0,
                                           vertical_stabilizer_distance_from_wing=3.0,
                                           canard_distance_in_front_of_wing=0.5)

wing_planform=LiftingSurfacePlanform(aspect_ratio=25.0,
                                span=1.9,
                                sweep_quarter_deg=45.0,
                                taper=0.3,
                                tip_twist_rad=1.0)
    
horizontal_stabilizer_planform=LiftingSurfacePlanform(aspect_ratio=3.0,
                                                                span=0.5,
                                                                sweep_quarter_deg=45.0,
                                                                taper=1.0,
                                                                tip_twist_rad=0.0)
    
vertical_stabilizer_planform=LiftingSurfacePlanform(aspect_ratio=3.0,
                                                                span=0.3,
                                                                sweep_quarter_deg=0.0,
                                                                taper=0.3,
                                                                tip_twist_rad=0.0)
canard_planform=LiftingSurfacePlanform(aspect_ratio=3.0,
                                                                span=0.3,
                                                                sweep_quarter_deg=45.0,
                                                                taper=1.0,
                                                                tip_twist_rad=0.0)

wing_number_of_sections=100
horizontal_stabilizer_number_of_sections=5
vertical_stabilizer_number_of_sections=5
canard_number_of_sections = 5

wing_airfoil = asb.Airfoil('naca9999')
tail_airfoil = asb.Airfoil('naca0012')
canard_airfoil=asb.Airfoil('naca0012')

wing_airfoils=np.array([wing_airfoil]*wing_number_of_sections)
horizontal_stabilizer_airfoils=np.array([tail_airfoil]*horizontal_stabilizer_number_of_sections)
vertical_stabilizer_airfoils=np.array([tail_airfoil]*vertical_stabilizer_number_of_sections)
canard_airfoils=np.array([canard_airfoil]*canard_number_of_sections)


class DesignOption():
    def __init__(self, assumptions: Assumptions=Assumptions(), canard:bool=False):
        self.assumptions = Assumptions()
        self.flight_envelope = FlightEnvelope()
        self.canard = canard
        self.assumptions = assumptions

    def generate_lift_distribution(
        self,
        load_factor: float,
        wing_planform: LiftingSurfacePlanform
    ): #-> asb.LiftingLine:

        weight = aircraft_parameters.total_mass * CONSTANTS.G0
        required_lift = load_factor * weight
        print('Required lift: ',required_lift)
        #Cruise conditions used for the operating point
        rho = self.assumptions.AIR_DENSITY_CRUISE_ALTITUDE
        cruise_speed=self.assumptions.MC*np.sqrt(CONSTANTS.GAMMA_AIR*CONSTANTS.GAS_CONSTANT_AIR*self.assumptions.TEMPERATURE_CRUISE_ALTITUDE)
           
        print('---------------Initial configuration------------------')
        print('Aspect ratio: ', wing_planform.aspect_ratio)
        print('Wing span: ',wing_planform.span)
        print('Wing area: ',wing_planform.wing_area)

        angle_of_attack_deg=15.0 #just an initial condition for the loop
        iteration_counter = 0
        while angle_of_attack_deg > self.assumptions.alpha_stall_deg:

            iteration_counter+=1
            if iteration_counter%10==0:
                print(f'Iteration {iteration_counter}')

            wing_span = wing_planform.span
            wing_span+=0.1

            wing_planform=LiftingSurfacePlanform(aspect_ratio=25.0,
                                span=wing_span,
                                sweep_quarter_deg=45.0,
                                taper=0.3,
                                tip_twist_rad=0.0)

            S = wing_planform.wing_area

            C_L = 2*required_lift/(rho*cruise_speed**2*S)
            angle_of_attack_deg=np.rad2deg(C_L/self.assumptions.C_L_alpha)
            print('Required angle of attack [deg]: ',angle_of_attack_deg)

        print('---------------Configuration before aerosandbox simulation------------------')
        print('Aspect ratio: ', wing_planform.aspect_ratio)
        print('Wing span: ',wing_planform.span)
        print('Wing area: ',wing_planform.wing_area)

        airplane=make_airplane_model(aircraft_parameters,
                                 wing_planform,
                                 horizontal_stabilizer_planform,
                                 vertical_stabilizer_planform,
                                 wing_number_of_sections,
                                 wing_airfoils,
                                 horizontal_stabilizer_number_of_sections,
                                 horizontal_stabilizer_airfoils,
                                 vertical_stabilizer_number_of_sections,
                                 vertical_stabilizer_airfoils,
                                 canard_planform,
                                 canard_number_of_sections,
                                 canard_airfoils)

        op_point = asb.OperatingPoint(
            velocity=cruise_speed,
            alpha=angle_of_attack_deg, 
            beta=0,
            p=0,
            q=0,
            r=0
        )

        analysis = asb.LiftingLine(
            airplane=airplane,
            op_point=op_point,
        )

        results = analysis.run()
        print(results)


        # print(results["CL"])
        # print(results["CD"])

        # spanwise = analysis.get_induced_velocity_at_points()
        # distribution = analysis.run_with_stability_derivatives()

        #return 1

    
    def estimate_CD0(self, aircraft_parameters:AircraftParameters, wing_planfom:WingPlanform):
        pass

if __name__=='__main__':

    wing_planform=LiftingSurfacePlanform(aspect_ratio=25.0,
                                span=2.0,
                                sweep_quarter_deg=45.0,
                                taper=0.3,
                                tip_twist_rad=0.0)

    design_option=DesignOption()
    design_option.generate_lift_distribution(load_factor=6.0,
                                             wing_planform=wing_planform)