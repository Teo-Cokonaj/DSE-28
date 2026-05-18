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

from aerodynamic_model.lifting_line_inviscid import LiftingLineInviscid

class LiftingLineTheory():
    def __init__(self,
                 aircraft_parameters: AircraftParameters,
                 wing_planform: LiftingSurfacePlanform,
                 horizontal_stabilizer_planform: LiftingSurfacePlanform,
                 vertical_stabilizer_planform: LiftingSurfacePlanform,
                 canard_planform: LiftingSurfacePlanform = None,
                 wing_number_of_sections:int = 100,
                 horizontal_stabilizer_number_of_sections:int = 5,
                 canard_number_of_sections:int = 5,
                 vertical_stabilizer_number_of_sections:int = 5
                 ):
        
        self.aircraft_parameters=aircraft_parameters
        self.wing_planform = wing_planform
        self.horizontal_stabilizer_planform=horizontal_stabilizer_planform
        self.vertical_stabilizer_planform=vertical_stabilizer_planform
        self.canard_planform=canard_planform

        self.wing_number_of_sections = wing_number_of_sections
        self.horizontal_stabilizer_number_of_sections = horizontal_stabilizer_number_of_sections
        self.canard_number_of_sections = canard_number_of_sections
        self.vertical_stabilizer_number_of_sections = vertical_stabilizer_number_of_sections

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
                                                [-self.aircraft_parameters.canard_distance_in_front_of_wing,0.0,
                                                 self.aircraft_parameters.z_canard]
                                                ))

        if horizontal_stabilizer:
            wings.append(self.make_horizontal_lifting_surface(self.horizontal_stabilizer_planform,
                                                          self.horizontal_stabilizer_number_of_sections,
                                                          twists=np.linspace(0.0,
                                                                             self.horizontal_stabilizer_planform.tip_twist,
                                                                             self.horizontal_stabilizer_number_of_sections),
                                                          airfoils=self.horizontal_stabilizer_airfoils
                                            ).translate([self.aircraft_parameters.horizontal_stabilizer_distance_from_wing,0.0,
                                                         self.aircraft_parameters.z_horizontal_stabilizer])
        )

        if vertical_stabilizer:
            wings.append(self.make_vertical_lifting_surface(self.vertical_stabilizer_planform,
                                                          self.vertical_stabilizer_number_of_sections,
                                                          twists=np.linspace(0.0,0.0,self.vertical_stabilizer_number_of_sections),
                                                          airfoils=self.vertical_stabilizer_airfoils
                                            ).translate([self.aircraft_parameters.vertical_stabilizer_distance_from_wing,0.0,
                                                         self.aircraft_parameters.z_vertical_stabiliser_root])  
        )

        self.airplane = asb.Airplane(
            name="HUGO",
            xyz_ref=[0.0, 0.0, 0.0], #reference point
            wings=wings,
        )
    

    def find_aoa_for_force_equilibrium(self,
                         velocity: float,
                         altitude_m: float,
                         alpha_range=np.array([0., 5.]) #NOTE: must start with zero
                         ) -> float:
        if not np.isclose(alpha_range[0], 0.):
            raise ValueError("The range of angle of attacks must start with zero!")

        CL_sweep_results = self.run_llt_alpha_sweep(
            velocity=velocity,
            altitude_m=altitude_m,
            alpha_range_deg=alpha_range
        )
        CL_alpha = CL_sweep_results["lift_curve_slope_per_rad"]
        CL_alpha_equals_0 = CL_sweep_results["CL"][0]

        dynamic_pressure = .5 * velocity**2 * asb.Atmosphere(altitude_m).density()
        CL_target = self.aircraft_parameters.total_mass * CONSTANTS.G0 / dynamic_pressure / self.wing_planform.wing_area
        
        return np.rad2deg((CL_target - CL_alpha_equals_0) / CL_alpha)
        

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

            def linear_spacing(start,end,number_of_stations):
                return np.linspace(0,1,number_of_stations)

            self.analysis = LiftingLineInviscid(
                airplane=self.airplane,
                op_point=self.op_point,
                spanwise_spacing_function=linear_spacing,
            )

            results = self.analysis.run()

            return self.analysis, results
    
    def plot_lift_distribution(self):

        y = self.analysis.vortex_centers[:, 1]

        n = len(y)
        mid = len(y) // 2
        mask = np.ones(n, dtype=bool)
        mask[mid:] = False

        y=y[mask]        
        gamma = self.analysis.vortex_strengths
        gamma=(gamma[:,0])[mask]
        chord = self.analysis.chords[mask]
        area = self.analysis.areas[mask]

        V = self.analysis.op_point.velocity
        rho = self.analysis.op_point.atmosphere.density()

        lift_per_span = (rho * V * gamma) # Kutta-Joukowski lift per unit span
        dy = area / chord # Approximate panel span width
        panel_lift = lift_per_span * dy # Lift carried by each panel
        
        distributions = {
            "spanwise_stations": y,  #m
            "panel_lift": panel_lift,  #N
        }

        plt.plot(y,panel_lift)
        plt.show()

        return distributions
    
    
    def extract_L2_Di_ratio(self,
                            results: Dict) -> float:
        
        lift_coefficient=results['CL']#[0]
        drag_coefficient=results['CD']

        return lift_coefficient**2/drag_coefficient
    
    def run_llt_alpha_sweep(self,
                        velocity: float,
                        altitude_m: float,
                        alpha_range_deg: np.ndarray = np.arange(0, 5, 2),
                        ):
        Cm_list = []
        CL_list = []
        alpha_rad_list = []

        for alpha in alpha_range_deg:
            self.op_point = asb.OperatingPoint(
                atmosphere=asb.Atmosphere(altitude_m),
                velocity=velocity,
                alpha=float(alpha),  # explicit scalar cast to be safe
            )

            self.analysis = LiftingLineInviscid(
                airplane=self.airplane,
                op_point=self.op_point,
            )

            results = self.analysis.run()

            CL_list.append(results["CL"])
            Cm_list.append(results["Cm"])
            alpha_rad_list.append(np.radians(float(alpha)))

        CL = np.array(CL_list)
        Cm = np.array(Cm_list)
        alpha_rad = np.array(alpha_rad_list)

        dCm_dalpha = np.polyfit(alpha_rad, Cm, 1)[0]
        dCL_dalpha = np.polyfit(alpha_rad, CL, 1)[0]
        dCm_dCL    = np.polyfit(CL, Cm, 1)[0]

        x_ref = 0.0 #origin at [0,0,0]
        x_ac = x_ref - self.airplane.c_ref * dCm_dCL

        Cmac = np.polyfit(CL, Cm, 1)[1]  # intercept at CL=0

        #Kuchemann
        sweep_quarter_rad=self.wing_planform.sweep_quarter_rad
        AR=self.wing_planform.aspect_ratio
        reference_lift_curve_slope_per_rad= 2*np.pi*np.cos(sweep_quarter_rad)/(np.sqrt(1+(2*np.pi*np.cos(sweep_quarter_rad)/np.pi/AR)**2)+2*np.pi*np.cos(sweep_quarter_rad)/np.pi/AR)

        return {
            "alpha": alpha_range_deg,
            "x_ac": x_ac,
            "CL": CL,
            "Cmac": Cmac,
            "lift_curve_slope_per_rad": dCL_dalpha,
            "reference_lift_curve_slope_per_rad": reference_lift_curve_slope_per_rad,
            "dCm_dalpha": dCm_dalpha,
        }            
        