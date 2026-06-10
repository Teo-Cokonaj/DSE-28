import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import math
from scipy.optimize import root_scalar
from scipy.integrate import cumulative_trapezoid
from scipy.interpolate import interp1d
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))
from scipy.interpolate import interp1d
import src_final.structural_analysis.parameters


from src_final.structural_analysis.Material import Material
from src_final.global_parameters import CONSTANTS
from src_final.Aircraft.Planform import Planform



class WingModel:
    def __init__(self,

                 wing_skin_thickness_m:float,
                 number_of_nodes: int,
                 material_1:Material,
                 planform:Planform,
                 load_factor:float,
                 #rib_number:float,
                ):
        self.wing_leng_m = planform.span
        self.wing_skin_thickness_m = wing_skin_thickness_m
        self.material_1=material_1
        self.number_of_nodes = number_of_nodes
        self.planform = planform
        self.load_factor = load_factor
        #self.rib_number = rib_number

    def planform_data(self, diameter_fuselage:float=0.31
                      ):
        self.span_poz, self.lift_span = self.planform.estimate_conservative_lift_distribution(
            diameter_fuselage=diameter_fuselage,
            positive_manoeuvring_limit_load_factor=self.load_factor,
            initial_total_aircraft_mass=50.0,
            number_of_stations=self.number_of_nodes
        )

        self.chord_stations, _, self.y_stations_chord, self.dy = self.planform.sectional_properties(
            number_of_sections=self.number_of_nodes
        )

        self.y_stations = self.y_stations_chord

        self.span_poz = np.asarray(self.span_poz, dtype=float)
        self.lift_span = np.asarray(self.lift_span, dtype=float)
        self.chord_stations = np.asarray(self.chord_stations, dtype=float)
        print(np.sum(self.lift_span)/9.81)
        return self.span_poz, self.lift_span, self.chord_stations, self.y_stations_chord, self.dy
    

    def perimeter_area_of_section(self):
        a = self.chord_stations
        b = a * self.planform.thickness_to_chord

        h = (a - b)**2 / (a + b)**2

        perimeter_crosssection = np.pi * (a + b) * (
            1 + (3 * h) / (10 + (4 - 3 * h)**0.5)
        )

        area = np.pi * (a * b - (a-self.wing_skin_thickness_m*2)* (b-self.wing_skin_thickness_m*2)) /4

        return np.squeeze(perimeter_crosssection), np.squeeze(area)
    
    def area_moment_inertia(self):
            a = self.chord_stations
            b = a* self.planform.thickness_to_chord
            area_momement_x = np.pi * (a *b**3 - ((a-self.wing_skin_thickness_m*2) * (b-self.wing_skin_thickness_m*2)**3)) /64
            area_momement_y = np.pi * b*a**3 /4
            #print(a,"\n")
            #print(b,"\n")
            return np.squeeze(area_momement_x),np.squeeze(area_momement_y)
    
    # def wing_weight_distribution(self):
    #     perimeter, _ = self.perimeter_area_of_section()

    #     n_lift = np.size(self.span_poz)

    #     perimeter_cop = perimeter[-n_lift:]

    #     if np.size(self.dy) == 1:
    #         dy_cop = np.ones(n_lift) * self.dy
    #     else:
    #         dy_cop = self.dy[-n_lift:]

    #     mass_per_station = (
    #         self.material_1.density
    #         * perimeter_cop
    #         * self.wing_skin_thickness_m
    #         * dy_cop
    #     )

    #     weight_per_station = mass_per_station * 9.81

    #     return weight_per_station
    

    def force_per_unit(self, plot: bool = False):
        perimeter, _ = self.perimeter_area_of_section()

        n_lift = np.size(self.lift_span)

        perimeter_cop = perimeter[-n_lift:]
        y_cop = self.span_poz

        if np.size(self.dy) == 1:
            dy_cop = np.ones(n_lift) * self.dy
        else:
            dy_cop = self.dy[-n_lift:]

        mass = self.material_1.density * perimeter_cop * self.wing_skin_thickness_m * dy_cop
        
        inertial_weight = self.load_factor * mass * 9.81
        

        self.force_distribution = self.lift_span - inertial_weight

        if plot:
            plt.figure()
            plt.plot(y_cop, self.lift_span, color="red", label="lift")
            plt.plot(y_cop, -inertial_weight, color="blue", label="inertial_weight")
            plt.plot(y_cop, self.force_distribution, color="black", label="net force")
            plt.xlabel("Spanwise position y [m]")
            plt.ylabel("Force per station [N]")
            plt.title("Lift, Weight, and Net Force Distribution")
            plt.grid(True)
            plt.legend()
            plt.show()

        return self.force_distribution, self.lift_span, inertial_weight
         



    def step_torsion_determination(self,
            plot: bool,
 ):
        reduced_sectional_spanwise_positions = self.span_poz
        self.force_cont_forces = interp1d (reduced_sectional_spanwise_positions,self.lift_span)
        c_stations_cop = self.chord_stations[-np.size(reduced_sectional_spanwise_positions):]
        
        torsion_per_node_single = self.force_cont_forces(reduced_sectional_spanwise_positions) * (c_stations_cop / 4.0)
        torsion_per_node_tot = np.cumsum(torsion_per_node_single[::-1])[::-1]

        self.torsion_node_tot = interp1d(reduced_sectional_spanwise_positions,torsion_per_node_tot)
        
        torsion_each_node = self.torsion_node_tot(reduced_sectional_spanwise_positions)
        torsion_each_node = np.concatenate(( np.full(np.size(self.chord_stations) - np.size(torsion_each_node), torsion_each_node[0]),torsion_each_node))
        if plot:
            plt.figure()
            plt.plot(self.y_stations, torsion_each_node)
            plt.xlabel("Spanwise position y [m]")
            plt.ylabel("Torsion")
            plt.title("Torsion Along Half Span")
            plt.grid(True)
            plt.show()

        return torsion_each_node

    def step_rotation_of_wing(self,
                              torsion:np.ndarray,
                              plot: bool,
                              ):
        #fitst we compute the rotation of the outer shell
        """Get the torsion from pervious funtion"""
        
        perimeter , area  = self.perimeter_area_of_section()
        rotation_rate_shell = torsion * perimeter/(4 * area**2 * self.material_1.shear_modulus * self.wing_skin_thickness_m)
        rotation = cumulative_trapezoid(rotation_rate_shell,self.y_stations_chord,initial = 0)
        rotation = np.squeeze(rotation)
        rotation_deg = np.degrees(rotation)
        if plot:
            plt.figure()
            plt.plot(self.y_stations_chord, rotation)
            plt.xlabel("Spanwise position y [m]")
            plt.ylabel("Rotation θ [rad]")
            plt.title("Rotation along span")
            plt.grid(True)
            plt.show()   
        
        return rotation, rotation_deg
    


    
    def step_vertical_deflection(self,
                        plot: bool,
                        moments: np.ndarray | None = None,
                                ):

        Ix,Iy = self.area_moment_inertia()
        if moments is None:
            
            M = self.step_moment(plot=False, debug=False)
        else:
            M = np.asarray(moments, dtype=float)
        

        v_boundary_root = 0
        theta_boundary_root = 0
        EI = self.material_1.elastic_modulus * Ix
        curvature = -M/EI
        theta = theta_boundary_root + cumulative_trapezoid(curvature,self.y_stations_chord,initial=0.0)
        displacement  = v_boundary_root + cumulative_trapezoid(theta,self.y_stations_chord,initial=0.0)
        if plot:
            plt.figure()
            plt.plot(self.y_stations_chord, theta)
            plt.xlabel("Spanwise position y [m]")
            plt.ylabel("Rotation θ [rad]")
            plt.title("Wing Slope Along Span")
            plt.grid(True)
            plt.show()

            
            plt.figure()
            plt.plot(self.y_stations_chord, displacement)
            plt.xlabel("Spanwise position y [m]")
            plt.ylabel("Vertical displacement v [m]")
            plt.title("Wing Vertical Deflection Along Span")
            plt.grid(True)
            plt.show()
        #we consider that the end constrains are both 0 and fixed
        #still need to understand the stuff of this I will ask more from teo

        return theta, displacement


#     def step_crushing_pressure(self,
#                          moments: np.ndarray | None = None,
#                                ):
#         if moments is None:
#               M = self.step_moment(False,False)
#         else:
#              M = np.asarray(moments,dtype = float)
        
#         Ix = self.area_moment_inertia()[0]
#         crushing_pressure = (
#         self.wing_skin_thickness_m
#         * self.chord_stations
#         * M**2
#         / (2 * self.material_1.elastic_modulus * Ix)
# )           
#         print(crushing_pressure)
#         return crushing_pressure

    def buckling_model(self):
        C = 4 #from SAD
        #b = planform.span/(2*self.rib_number)
        crit_stress = C * np.pi**2 * self.material_1.elastic_modulus/(12*(1-self.material_1.poisson_ratio)**2)*(self.wing_skin_thickness_m/self.chord_stations)
        return crit_stress


    def step_shear_stress(self,
                          #reduced_sectional_spanwise_positions: float,
                          #modified_sectional_lifts_schrenk:float,
                          debug: bool,
                          plot: bool):
        modified_sectional_lifts_schrenk = self.force_distribution
        reduced_sectional_spanwise_positions = self.span_poz
    #need torque, area and wall thickness --> for a thin-walled section, tau = T/(2tA)
    # area = assume elliptical shape --> chord, thickness at a given location
    # torsion modelled by Alex
    # thickness = wing skin thickness

        # Step 1: copy the chord length and spanwise positions outside the fuselage
        c_stations, _, y_stations, _ = self.planform.sectional_properties(number_of_sections=self.number_of_nodes)
        c_stations_cop = c_stations[-np.size(reduced_sectional_spanwise_positions):]
        y_stations_cop = y_stations[-np.size(reduced_sectional_spanwise_positions):]


        # Step 2: Get the thickness and cross section area at each station
        thickness_stations_cop = c_stations_cop * self.planform.thickness_to_chord
        cross_section_areas_cop = np.pi * 0.5 * c_stations_cop * 0.5 * thickness_stations_cop

        # Step 3: Get the skin thickness
        thickness_skin = self.wing_skin_thickness_m

        # Step 4: Get the torsion
        torsion_stations = self.step_torsion_determination(plot=False)
        torsion_stations_cop = torsion_stations[-np.size(reduced_sectional_spanwise_positions):]
        
        # Step 5: Calculate the shear stress
        shear_wall_cop = torsion_stations_cop/(2*thickness_skin*cross_section_areas_cop)

        # Step 6: Interpolate the shear
        self.shear_node_tot = interp1d(reduced_sectional_spanwise_positions,
                                       shear_wall_cop,
                                       kind = 'zero',
                                       fill_value = 'extrapolate')
    
        self.shear_stress_each_node = self.shear_node_tot(reduced_sectional_spanwise_positions)
        self.shear_stress_each_node = np.concatenate(( np.full(np.size(c_stations) - np.size(self.shear_stress_each_node), self.shear_stress_each_node[0]), self.shear_stress_each_node))
        
       
        if debug:
            print(f'Number of stations [-]: {len(c_stations)}')
            print(f'Thickness-to-chord [-]: {self.planform.thickness_to_chord}')
            print(f'Skin thickness [m]: {thickness_skin}')
            print(f'Chord lengths [m]: {c_stations}')
            print(f'Spanwise positions [m]: {y_stations}')
            print(f'Torsion [N/m]: {torsion_stations_cop}')
            print(f'Cross-section Areas [m2]: {cross_section_areas_cop}')
            print(f'Shear stress [Pa]: {self.shear_stress_each_node}')
            print(f'Are webuckling: {np.max(are_we_buckling)}, {np.min(are_we_buckling)}')

       
        if plot:
            fig = plt.figure()
            plt.plot(y_stations, self.shear_stress_each_node/1e6)
            plt.xlabel("Spanwise Position [m]")
            plt.ylabel("Shear Stress [MPa]")
            plt.title("Shear Stress Distribution")
            fig.savefig('shear_stress_distribution.png')
            plt.show()

        return self.shear_stress_each_node
    

    # def step_normal_stress(self,
    #                       #reduced_sectional_spanwise_positions: float,
    #                       #modified_sectional_lifts_schrenk:float,
    #                       debug: bool,
    #                       plot: bool):
    #     modified_sectional_lifts_schrenk = self.force_distribution
    #     reduced_sectional_spanwise_positions = self.span_poz
    # #need torque, area and wall thickness --> for a thin-walled section, tau = T/(2tA)
    # # area = assume elliptical shape --> chord, thickness at a given location
    # # torsion modelled by Alex
    # # thickness = wing skin thickness

    #     # Step 1: copy the chord length and spanwise positions outside the fuselage
    #     c_stations, _, y_stations, _ = self.planform.sectional_properties(number_of_sections=self.number_of_nodes)
    #     c_stations_cop = c_stations[-np.size(reduced_sectional_spanwise_positions):]
    #     y_stations_cop = y_stations[-np.size(reduced_sectional_spanwise_positions):]

    #     I_xx, I_yy = self.area_moment_inertia()
    #     I_xx_cop = I_xx[-np.size(reduced_sectional_spanwise_positions):]


    #     # Step 2: Get the thickness and cross section area at each station
    #     thickness_stations_cop = c_stations_cop * self.planform.thickness_to_chord
    #     #cross_section_areas_cop = np.pi * 0.5 * c_stations_cop * 0.5 * thickness_stations_cop

    #     # Step 3: Get the skin thickness
    #     thickness_skin = self.wing_skin_thickness_m

    #     # Step 4: Get the bending
    #     moment_stations = self.step_moment(debug, plot)
    #     moment_stations_cop = moment_stations[-np.size(reduced_sectional_spanwise_positions):]
        
    #     # Step 5: Calculate the normal stress
    #     normal_wall_cop = moment_stations_cop * thickness_stations_cop / 2 / I_xx_cop

    #     # Step 6: Interpolate the normal stress
    #     self.normal_node_tot = interp1d(reduced_sectional_spanwise_positions,
    #                                    normal_wall_cop,
    #                                    kind = 'zero',
    #                                    fill_value = 'extrapolate')
    
    #     self.normal_stress_each_node = self.normal_node_tot(reduced_sectional_spanwise_positions)
    #     self.normal_stress_each_node = np.concatenate(( np.full(np.size(c_stations) - np.size(self.normal_stress_each_node), self.normal_stress_each_node[0]), self.normal_stress_each_node))
        
       
    #     if debug:
    #         print(f'Number of stations [-]: {len(c_stations)}')
    #         print(f'Thickness-to-chord [-]: {self.planform.thickness_to_chord}')
    #         print(f'Skin thickness [m]: {thickness_skin}')
    #         print(f'Chord lengths [m]: {c_stations}')
    #         print(f'Spanwise positions [m]: {y_stations}')
    #         print(f'Moment [N/m]: {moment_stations_cop}')
    #         print(f'Cross-section Ixx [m4]: {I_xx_cop}')
    #         print(f'Shear stress [Pa]: {self.normal_stress_each_node}')

       
    #     if plot:
    #         fig = plt.figure()
    #         plt.plot(y_stations, self.normal_stress_each_node/1e6)
    #         plt.xlabel("Spanwise Position [m]")
    #         plt.ylabel("Normal Stress [MPa]")
    #         plt.title("Normal Stress Distribution")
    #         fig.savefig('normal_stress_distribution.png')
    #         plt.show()

    #     return self.normal_stress_each_node
            

    def step_shear_forces(self,
                        #  reduced_sectional_spanwise_positions:float,
                        #  modified_sectional_lifts_schrenk: float,
                          debug: bool,
                          plot: bool):
        reduced_sectional_spanwise_positions = self.span_poz
        modified_sectional_lifts_schrenk = self.force_distribution
        # Step 1: Find the lift acting on the wing and the spanwise positions of each section
        self.lift_cont_forces = interp1d (reduced_sectional_spanwise_positions,modified_sectional_lifts_schrenk)
        _, _, self.y_stations, _ = self.planform.sectional_properties(number_of_sections=self.number_of_nodes)
        self.y_stations_cop = self.y_stations[-np.size(reduced_sectional_spanwise_positions):]
        self.lift_cont_forces_cop = self.lift_cont_forces(self.y_stations_cop)
  

        # Step 2: Use cumsum to sum the shear forces over the wingspan from the interpolated lift, then trim it
        self.internal_shear_forces_cop = np.cumsum(self.lift_cont_forces_cop[::-1])[::-1]

        # Step 3: Interpolate the shear
        self.internal_shear_forces_cop_int = interp1d(self.y_stations_cop,
                                              self.internal_shear_forces_cop,
                                              kind='zero',
                                              fill_value='extrapolate')
        
        self.shear_each_node_cop = self.internal_shear_forces_cop_int(self.y_stations_cop)        
        self.shear_each_node = self.internal_shear_forces_cop_int(self.y_stations)
        self.shear_force_each_node = np.concatenate(( np.full(np.size(self.y_stations) - np.size(self.shear_each_node), self.shear_each_node[0]), self.shear_each_node))
        
        # Step 3 (optional): print intermediate values for debug
        if debug:
            print(f'Number of sections: {self.number_of_nodes}')
            print(f'Spanwise positions [m]: {self.y_stations}')
            print(f'Distributed lift [N]: {self.lift_cont_forces_cop}')
            print(f'Shear force [N]: {self.shear_each_node}')             

        # Step 4 (optional): plot
        if plot:
            fig = plt.figure()
            plt.plot(self.y_stations, self.shear_each_node)
            plt.xlabel('Spanwise Position [m]')
            plt.ylabel("Shear Force [N]")
            plt.title("Shear Force Distribution")
            fig.savefig('shear_force_distribution.png')
            plt.show()
        
        return self.shear_force_each_node

    def step_moment(self,
                    debug: bool,
                    plot: bool):
    # Step 1: Integrate the shear loads
        y_stations_cop_fine = np.linspace(self.y_stations_cop[0], self.y_stations_cop[-1], 1 * len(self.y_stations_cop))
        y_stations_fine =  np.linspace(self.y_stations[0], self.y_stations[-1], 1 * len(self.y_stations))
        internal_shear_forces_cop_fine = self.internal_shear_forces_cop_int(y_stations_cop_fine)
        internal_bending_moments_cop = np.concatenate([[0], cumulative_trapezoid(internal_shear_forces_cop_fine[::-1], y_stations_cop_fine[::-1])])[::-1]
        self.internal_bending_moments_int = interp1d(
                                     self.y_stations_cop,
                                     internal_bending_moments_cop,
                                     kind='zero',
                                     bounds_error=False,
                                     fill_value='extrapolate')
        
        self.internal_bending_moments_cop = self.internal_bending_moments_int(self.y_stations_cop)
        self.internal_bending_moments = self.internal_bending_moments_int(self.y_stations)

        # Step 2 (optional): print intermediate values if debug
        if debug:
            print(f'Number of sections: {len(self.y_stations)}')
            print(f'Spanwise positions [m]: {self.y_stations}')
            print(f'Bending Moments [Nm]: {self.internal_bending_moments}')


        # Step 3 (optional): plot
        if plot:
            fig = plt.figure()
            plt.plot(self.y_stations, self.internal_bending_moments)
            plt.xlabel('Spanwise Position [m]')
            plt.ylabel("Bending Moment [Nm]")
            plt.title("Bending Moment Distribution")
            
            plt.show()
        return self.internal_bending_moments

    def wing_stres_per_com(self):
        buckling_stress = self.buckling_model()
        moments = self.step_moment(False, False)
        Ix,_ = self.area_moment_inertia()
        y_max = self.planform.thickness_to_chord * self.chord_stations
        bending_stress = moments * y_max / Ix

        diff = buckling_stress- bending_stress

        return diff
    
    def bending_stresses(self):
        moments = self.step_moment(False, False)
        Ix,_ = self.area_moment_inertia()
        y_max = self.planform.thickness_to_chord * self.chord_stations
        bending_stress = moments * y_max / Ix

        return bending_stress

    


if __name__=='__main__':
        material_1 = Material(density=1570,
                            elastic_modulus=69e9,
                            shear_modulus=5.58e9,
                            poisson_ratio=0.048,
                            yield_strength=896e6,
                            fracture_strength=600e6
                            )
        
        planform=Planform(
            aspect_ratio=27.0,
            span=2.67,
            sweep_quarter_deg=15,
            taper=0.5,
            thickness_to_chord=0.12,
            cm_quarter_chord=1.0,
            wetted_surface_ratio=1.0,
            interference_factor=1.0,
            clmax=1.5,
            flap=False,
        )

        wing_model= WingModel(
                 wing_skin_thickness_m =0.002,
                 number_of_nodes=100,
                 material_1 = material_1,
                 planform = planform,
                 load_factor = 1,
                 )
        wing_model.planform_data()
        plot_1 = False
        force_distribution, lift, weight = wing_model.force_per_unit(plot=plot_1)

        torque = wing_model.step_torsion_determination(plot=plot_1)

        shear_force = wing_model.step_shear_forces(debug=False, plot=plot_1)

        bending_moment = wing_model.step_moment(debug=False, plot=plot_1)

        twist_rad, twist_deg = wing_model.step_rotation_of_wing(
            torsion=torque,
            plot=plot_1
        )

        slope_rad, deflection_m = wing_model.step_vertical_deflection(
            plot=plot_1,
            moments=bending_moment
        )

        # crushing_pressure = wing_model.step_crushing_pressure(
        #     moments=bending_moment
        # )

        shear_stress = wing_model.step_shear_stress(
            debug=False,
            plot=plot_1
        )

        buckling_stress = wing_model.buckling_model()
        are_we_buckling = wing_model.wing_stres_per_com()
       

        print("\n========== WING STRUCTURAL RESULTS ==========")
        print(f"Root torque:              {torque[0]:.3f} N m")
        print(f"Tip torque:               {torque[-1]:.3f} N m")
        print(f"Root shear force:         {shear_force[0]:.3f} N")
        print(f"Root bending moment:      {bending_moment[0]:.3f} N m")
        print(f"Tip twist:                {twist_deg[-1]:.6f} deg")
        print(f"Tip vertical deflection:  {deflection_m[-1]:.6f} m")
        print(f"Max shear stress:         {np.max(np.abs(shear_stress)) / 1e6:.3f} MPa")
        #print(f"Max crushing pressure:    {np.max(np.abs(crushing_pressure)) / 1e6:.3f} MPa")
        print(f"Max buckling stress is    {np.max(buckling_stress)/1e6 :.3f} MPa")
        print(f"Are we buckling with this? {np.any(  are_we_buckling> 0)}")
        print(np.max(are_we_buckling))
        


        # Quick sanity-run of torsion computation
        # span_poz, lift_span = planform.estimate_conservative_lift_distribution(diameter_fuselage=0.31,
        #                                              positive_manoeuvring_limit_load_factor=6.0,
        #                                              initial_total_aircraft_mass=50.0,
        #                                              number_of_stations=wing_model.number_of_nodes)
        # c_stations = planform.sectional_properties(number_of_sections=wing_model.number_of_nodes)[0]

        # _,_,y_station_chord,dy = planform.sectional_properties(number_of_sections=wing_model.number_of_nodes)
        # force_along_wing = wing_model.force_per_unit(c_stations,wing_model.wing_skin_thickness_m,planform.thickness_to_chord,material_1.density,y_station_chord,dy,lift_span)
        # torsion = wing_model.step_torsion_determination(c_stations, y_station_chord, span_poz, lift_span,plot=True)
        # wing_model.step_shear_forces(reduced_sectional_spanwise_positions=span_poz,
        #                                           modified_sectional_lifts_schrenk=force_along_wing[0],debug = False, plot = False)
        # wing_model.step_moment(debug = False, plot = False)
        # rotation = wing_model.step_rotation_of_wing(material_1.shear_modulus ,planform.thickness_to_chord,wing_model.wing_skin_thickness_m,c_stations,torsion,y_station_chord,True)
        # deflection  = wing_model.step_vertical_defletion(y_station_chord,material_1.elastic_modulus,c_stations,planform.thickness_to_chord,plot=True)

        
        # shear = wing_model.step_shear_stress(reduced_sectional_spanwise_positions=span_poz, modified_sectional_lifts_schrenk=force_along_wing[0], debug = True, plot = True)
        # p_crush = wing_model.step_crushing_pressure(c_stations,material_1.elastic_modulus,planform.thickness_to_chord,y_station_chord)
       
        
