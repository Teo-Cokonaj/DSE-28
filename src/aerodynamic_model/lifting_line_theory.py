import aerosandbox as asb
import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import os
import sys
from typing import Dict
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from global_parameters import CONSTANTS, Assumptions
from objects.aircraft_parameters import AircraftParameters
from objects.lifting_surface_planform import LiftingSurfacePlanform
from airfoil.SymmetricAirfoil import SymmetricAirfoil

class LiftingLineTheory():
    def __init__(self,
                 aircraft_parameters: AircraftParameters,
                 wing_planform: LiftingSurfacePlanform,
                 horizontal_stabilizer_planform: LiftingSurfacePlanform,
                 vertical_stabilizer_planform: LiftingSurfacePlanform,
                 canard_planform: LiftingSurfacePlanform,
                 ):
        
        self.aircraft_parameters=aircraft_parameters
        self.wing_planform = wing_planform
        self.horizontal_stabilizer_planform=horizontal_stabilizer_planform
        self.vertical_stabilizer_planform=vertical_stabilizer_planform
        self.canard_planform=canard_planform

        self.wing_number_of_sections = 100
        self.horizontal_stabilizer_number_of_sections = 5
        self.canard_number_of_sections = 5
        self.vertical_stabilizer_number_of_sections = 5

    def initialize_airfoils(self):
        symmetric_airfoil = SymmetricAirfoil()
        self.wing_airfoil = symmetric_airfoil
        self.horizontal_stabilizer_airfoil = symmetric_airfoil
        self.vertical_stabilizer_airfoil=symmetric_airfoil
        self.canard_airfoil = symmetric_airfoil
        self.wing_airfoils=np.array([self.wing_airfoil]*self.wing_number_of_sections)
        self.horizontal_stabilizer_airfoils=np.array([self.horizontal_stabilizer_airfoil]*\
                                                     self.horizontal_stabilizer_number_of_sections)
        self.vertical_stabilizer_airfoils=np.array([self.vertical_stabilizer_airfoil]*\
                                                   self.vertical_stabilizer_number_of_sections)
        self.canard_airfoils=np.array([self.canard_airfoil]*self.canard_number_of_sections)

    def calculate_LE_x_positions(self,
                                 number_of_sections: int,
                                 planform: LiftingSurfacePlanform):
        return np.linspace(0.0,planform.half_span*np.tan(planform.sweep_LE_rad),number_of_sections)

    def calculate_section_y_positions(self,
                                      number_of_sections: int,
                                      planform: LiftingSurfacePlanform):
        return np.linspace(0.0,planform.half_span,number_of_sections)

    def make_horizontal_lifting_surface(self,
        planform: LiftingSurfacePlanform,
        number_of_sections: int,
        twists: np.ndarray,
        airfoils: np.ndarray
    ) -> asb.Wing:

        xsecs = []

        section_LE_x_positions=self.calculate_LE_x_positions(number_of_sections,planform)
        section_y_positions=self.calculate_section_y_positions(number_of_sections,planform)

        chords = np.linspace(planform.c_root,planform.c_tip,number_of_sections)
        for i in range(number_of_sections):
            xsecs.append(
                asb.WingXSec(
                    xyz_le=np.array([section_LE_x_positions[i], section_y_positions[i], 0.0]),
                    chord=chords[i],
                    twist=twists[i],
                    airfoil=airfoils[i],
                )
            )

        return asb.Wing(
            symmetric=True,
            xsecs=xsecs,
        )

    def make_vertical_lifting_surface(self,
        planform: LiftingSurfacePlanform,
        number_of_sections: int,
        twists: np.ndarray,
        airfoils: np.ndarray,
    ) -> asb.Wing:

        xsecs = []

        section_LE_x_positions=self.calculate_LE_x_positions(number_of_sections,planform)
        section_y_positions = self.calculate_section_y_positions(number_of_sections,planform)

        chords=np.linspace(planform.c_root,planform.c_tip,number_of_sections)
        for i in range(number_of_sections):
            xsecs.append(
                asb.WingXSec(
                    xyz_le=np.array([section_LE_x_positions[i], 0.0, section_y_positions[i]]),
                    chord=chords[i],
                    twist=twists[i],
                    airfoil=airfoils[i],
                )
            )

        return asb.Wing(
            symmetric=False,
            xsecs=xsecs,
        )
    
    def make_full_airplane_model(self,
                                 main_wing: bool = True,
                                 canard: bool = False,
                                 horizontal_stabilizer: bool = False,
                                 vertical_stabilizer: bool = False):
        wings=[]
        if main_wing:
            wings.append(self.make_horizontal_lifting_surface(self.wing_planform,
                                                           self.wing_number_of_sections,
                                                           twists=np.linspace(0.0,
                                                                              self.wing_planform.tip_twist,
                                                                              self.wing_number_of_sections),
                                              airfoils=self.wing_airfoils))

        if canard:
            wings.append(self.make_horizontal_lifting_surface(self.canard_planform,
                                            self.canard_number_of_sections,
                                            twists=np.linspace(0.0,
                                                                self.canard_planform.tip_twist,
                                                                self.canard_number_of_sections),
                                            airfoils=self.canard_airfoils).translate(
                                                [-self.aircraft_parameters.canard_distance_in_front_of_wing,0.0,0.0]
                                                ))

        if horizontal_stabilizer:
            wings.append(self.make_horizontal_lifting_surface(self.horizontal_stabilizer_planform,
                                                          self.horizontal_stabilizer_number_of_sections,
                                                          twists=np.linspace(0.0,
                                                                             self.horizontal_stabilizer_planform.tip_twist,
                                                                             self.horizontal_stabilizer_number_of_sections),
                                                          airfoils=self.horizontal_stabilizer_airfoils
                                            ).translate([self.aircraft_parameters.horizontal_stabilizer_distance_from_wing,0.0,0.0])
        )

        if vertical_stabilizer:
            wings.append(self.make_vertical_lifting_surface(self.vertical_stabilizer_planform,
                                                          self.vertical_stabilizer_number_of_sections,
                                                          twists=np.linspace(0.0,0.0,self.vertical_stabilizer_number_of_sections),
                                                          airfoils=self.vertical_stabilizer_airfoils
                                            ).translate([self.aircraft_parameters.vertical_stabilizer_distance_from_wing,0.0,0.0])  
        )

        self.airplane = asb.Airplane(
            name="HUGO",
            xyz_ref=[0.0, 0.0, 0.0], #reference point
            wings=wings,
        )
    
        
    def run_llt_trim_analysis(self,
                         velocity: float,
                         altitude_m: float,
                         ):

        opti = asb.Opti()
        alpha_deg = opti.variable(init_guess=5.0)

        self.op_point = asb.OperatingPoint(
            atmosphere=asb.Atmosphere(altitude_m),
            velocity=velocity,
            alpha=alpha_deg,
        )

        analysis = asb.LiftingLine(
            airplane=self.airplane,
            op_point=self.op_point,
        )

        results = analysis.run()

        opti.subject_to(-results["F_w"][2] == self.aircraft_parameters.total_mass * CONSTANTS.G0)
        # opti.subject_to(results["m_b"][1] == 0)  # Pitching moment = 0

        sol = opti.solve()
        trimmed_alpha_deg = sol(alpha_deg)
        print('Trimmed alpha_deg: ',trimmed_alpha_deg)
        print('Cruise speed: ',cruise_speed)

        self.op_point = asb.OperatingPoint(
            atmosphere=asb.Atmosphere(altitude_m),  # Fixed: include atmosphere
            velocity=velocity,
            alpha=trimmed_alpha_deg,
        )

        analysis = asb.LiftingLine(
            airplane=self.airplane,
            op_point=self.op_point,
        )

        results = analysis.run()

        return analysis, results
        

    def run_llt_arbitrary_analysis(self,
                            altitude_m: float,
                            velocity: float,
                            angle_of_attack_deg: float,
                        ):

            self.op_point = asb.OperatingPoint(
                atmosphere=asb.Atmosphere(altitude_m),
                velocity=velocity,
                alpha=angle_of_attack_deg,
                beta=0,
                p=0,
                q=0,
                r=0,
            )

            analysis = asb.LiftingLine(
                airplane=self.airplane,
                op_point=self.op_point,
            )

            results = analysis.run()

            return analysis, results
    
    def extract_L2_Di_ratio(self,
                            results: Dict) -> float:
        
        lift_force=results['L']#[0]
        drag_force=results['D']

        return lift_force**2/drag_force
    
    def run_llt_alpha_sweep(self,
                        velocity: float,
                        altitude_m: float,
                        alpha_range: np.ndarray = np.arange(0, 5, 2),
                        ):
        CL_list = []

        for alpha in alpha_range:
            op_point = asb.OperatingPoint(
                atmosphere=asb.Atmosphere(altitude_m),
                velocity=velocity,
                alpha=float(alpha),  # explicit scalar cast to be safe
            )

            analysis = asb.LiftingLine(
                airplane=self.airplane,
                op_point=op_point,
            )

            results = analysis.run()

            CL_list.append(results["CL"])

        CL = np.array(CL_list)

        # Fit lift curve slope over linear region only
        lift_curve_slope_per_rad = np.polyfit(np.deg2rad(alpha_range), CL, 1)[0]

        #Kuchemann
        sweep_quarter_rad=self.wing_planform.sweep_quarter_rad
        AR=self.wing_planform.aspect_ratio
        reference_lift_curve_slope_per_rad= 2*np.pi*np.cos(sweep_quarter_rad)/(np.sqrt(1+(2*np.pi*np.cos(sweep_quarter_rad)/np.pi/AR)**2)+2*np.pi*np.cos(sweep_quarter_rad)/np.pi/AR)

        return {
            "alpha": alpha_range,
            "CL": CL,
            "lift_curve_slope_per_rad": lift_curve_slope_per_rad,
            "reference_lift_curve_slope_per_rad":reference_lift_curve_slope_per_rad
        }
        
    
if __name__ == "__main__":

    assumptions=Assumptions()
    air_density = assumptions.AIR_DENSITY_CRUISE_ALTITUDE
    cruise_speed=assumptions.MC*np.sqrt(CONSTANTS.GAMMA_AIR*CONSTANTS.GAS_CONSTANT_AIR*\
                                                 assumptions.TEMPERATURE_CRUISE_ALTITUDE)
    
    aircraft_parameters=AircraftParameters(total_mass=50.0,
                                           horizontal_stabilizer_distance_from_wing=3.0,
                                           vertical_stabilizer_distance_from_wing=3.0,
                                           canard_distance_in_front_of_wing=0.5)
    
    wing_planform=LiftingSurfacePlanform(aspect_ratio=25.0,
                                span=2.0,
                                sweep_quarter_deg=45.0,
                                taper=1.0,
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
    
    lifting_line_theory=LiftingLineTheory(aircraft_parameters,
                                          wing_planform,
                                          horizontal_stabilizer_planform,
                                          vertical_stabilizer_planform,
                                          canard_planform,
                                          )
    
    lifting_line_theory.initialize_airfoils()
    lifting_line_theory.make_full_airplane_model(main_wing=True,
                                                      canard=True,
                                                      horizontal_stabilizer=True,
                                                      vertical_stabilizer=True)
    #lifting_line_theory.airplane.draw_three_view()

    velocity = assumptions.MC*np.sqrt(CONSTANTS.GAMMA_AIR*CONSTANTS.GAS_CONSTANT_AIR*assumptions.TEMPERATURE_CRUISE_ALTITUDE)
    alpha_sweep_results=lifting_line_theory.run_llt_alpha_sweep(velocity=velocity,
                                                                altitude_m=assumptions.ALTITUDE_CRUISE)
    print('Numerical C_L_alpha: ',alpha_sweep_results['lift_curve_slope_per_rad'] )
    print('Analytic C_L_alpha: ',alpha_sweep_results['reference_lift_curve_slope_per_rad'] )

    # _,trim_results =lifting_line_theory.run_llt_trim_analysis(velocity=velocity,
    #                                                           altitude_m=assumptions.ALTITUDE_CRUISE)
    
    # _, arbitrary_results = lifting_line_theory.run_llt_arbitrary_analysis(velocity=238.77,
    #                                                                      altitude_m=assumptions.ALTITUDE_CRUISE,
    #                      angle_of_attack_deg=1.64,
    #                    )

    # required_ratio=lifting_line_theory.extract_L2_Di_ratio(trim_results)
    # reference_ratio=lifting_line_theory.extract_L2_Di_ratio(arbitrary_results)

    # print('Required ratio: ',required_ratio)
    # print('Reference ratio: ',reference_ratio)



