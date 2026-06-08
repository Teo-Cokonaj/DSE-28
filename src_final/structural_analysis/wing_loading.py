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
                 wing_leng_m:float,
                 wing_skin_thickness_m:float,
                 number_of_nodes: int,
                 material_1:Material,
                 material_2:Material,
                 planform:Planform,
                ):
        self.wing_leng_m = wing_leng_m
        self.wing_skin_thickness_m = wing_skin_thickness_m
        self.material_1=material_1
        self.material_2 = material_2
        self.number_of_nodes = number_of_nodes
        self.planform = planform



    def perimeter_area_of_section(self,
                        c_station:np.ndarray,
                        thickness_to_chord: float
                                  ):
            #Calculating the major and minor axes for each section\
            a=c_station/2
            b=a*thickness_to_chord
            #using Ramanujan's Second Approximation
            h = (a-b)**2/(a+b)**2
            perimeter_crossection = np.pi * (a + b ) * [1 + (3*h**2)/(10 + (4-3*h**2)**(1/2))]
            area = np.pi*a*b
            perimeter_crossection = np.squeeze(perimeter_crossection)
            return perimeter_crossection,area
    

    def area_moment_inertia(self,
                        c_satations:np.ndarray,
                        thicchness_to_chord:float
                            ):
            a = c_satations/2
            b = a* thicchness_to_chord
            area_momement_x = np.pi * a *b**3 /4
            area_momement_y = np.pi * b*a**3 /4
            
            return np.squeeze(area_momement_x),np.squeeze(area_momement_y)
    


    def step_torsion_determination(self,
            c_stations:float,
            y_stations:np.asarray,
            reduced_sectional_spanwise_positions: float,
            modified_sectional_lifts_schrenk:float,
            plot: bool,
 ):
        self.lift_cont_forces = interp1d (reduced_sectional_spanwise_positions,modified_sectional_lifts_schrenk)
        c_stations_cop = c_stations[-np.size(reduced_sectional_spanwise_positions):]
        
        torsion_per_node_single = self.lift_cont_forces(reduced_sectional_spanwise_positions) * (c_stations_cop / 4.0)
        torsion_per_node_tot = np.cumsum(torsion_per_node_single[::-1])[::-1]

        self.tosrion_node_tot = interp1d(reduced_sectional_spanwise_positions,torsion_per_node_tot)
        
        torsion_each_node = self.tosrion_node_tot(reduced_sectional_spanwise_positions)
        torsion_each_node = np.concatenate(( np.full(np.size(c_stations) - np.size(torsion_each_node), torsion_each_node[0]),torsion_each_node))
        if plot:
            plt.figure()
            plt.plot(y_stations, torsion_each_node)
            plt.xlabel("Spanwise position y [m]")
            plt.ylabel("Torsion")
            plt.title("Torsion Along Half Span")
            plt.grid(True)
            plt.show()

        return torsion_each_node

    def step_rotation_of_wing(self,
                              G1:float,
                              thicknes_to_chord:float,
                              skin_thickness:float,
                              chords:np.ndarray,
                              torsion:np.ndarray,
                              y_poz:np.ndarray,
                              plot: bool,
                              ):
        #fitst we compute the rotation of the outer shell
        """Get the torsion from pervious funtion"""
        
        perimeter , area  = self.perimeter_area_of_section(chords,thicknes_to_chord)
        rotation_rate_shell = torsion * perimeter/(4 * area**2 * G1 * skin_thickness)
        rotation = cumulative_trapezoid(rotation_rate_shell,y_poz,initial = 0)
        rotation = np.squeeze(rotation)
        rotation_deg = np.degrees(rotation)
        if plot:
            plt.figure()
            plt.plot(y_poz, rotation)
            plt.xlabel("Spanwise position y [m]")
            plt.ylabel("Rotation θ [rad]")
            plt.title("Rotation along span")
            plt.grid(True)
            plt.show()   
        
        return rotation, rotation_deg
    


    
    def step_vertical_defletion(self,
                        y_poz:np.ndarray,
                        E:float,
                        chord_stations:np.ndarray,
                        thickness_to_chord:float,
                        plot: bool,
                                ):
        y_poz = np.asarray(y_poz,dtype=float)
       # chord_length = np.asarray(chord_length,dtype=float)


        Ix,Iy = self.area_moment_inertia(chord_stations, thickness_to_chord)
        #M = self.step_moment()
        M = self.step_moment(plot=False,debug=False)
        

        v_boundary_root = 0
        theta_boundary_root = 0
        EI = E * Ix
        curvature = -M/EI
        theta = theta_boundary_root + cumulative_trapezoid(curvature,y_poz,initial=0.0)
        displacement  = v_boundary_root + cumulative_trapezoid(theta,y_poz,initial=0.0)
        if plot:
            plt.figure()
            plt.plot(y_poz, theta)
            plt.xlabel("Spanwise position y [m]")
            plt.ylabel("Rotation θ [rad]")
            plt.title("Wing Slope Along Span")
            plt.grid(True)
            plt.show()

            
            plt.figure()
            plt.plot(y_poz, displacement)
            plt.xlabel("Spanwise position y [m]")
            plt.ylabel("Vertical displacement v [m]")
            plt.title("Wing Vertical Deflection Along Span")
            plt.grid(True)
            plt.show()
        #we consider that the end constrains are both 0 and fixed
        #still need to understand the stuff of this I will ask more from teo

        return theta, displacement


    def step_crushing_pressure(self,
                         chord_stations:np.asarray,
                         E: float,
                         thichness_to_chord:float,
                         y_poz:float
                               ):
        M = self.step_moment(False,False)
        Ix = self.area_moment_inertia(chord_stations,thichness_to_chord)[0]
        crushing_pressure  = self.wing_skin_thickness_m * c_stations * M**2/(2* E * Ix)
        return crushing_pressure


    def step_shear_stress(self,
                          reduced_sectional_spanwise_positions: float,
                          modified_sectional_lifts_schrenk:float,
                          debug: bool,
                          plot: bool):
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
        torsion_stations = self.step_torsion_determination(c_stations,y_stations,reduced_sectional_spanwise_positions,modified_sectional_lifts_schrenk,plot = False)
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
        
        # Step 7 (optional): print values for debug
        if debug:
            print(f'Number of stations [-]: {len(c_stations)}')
            print(f'Thickness-to-chord [-]: {self.planform.thickness_to_chord}')
            print(f'Skin thickness [m]: {thickness_skin}')
            print(f'Chord lengths [m]: {c_stations}')
            print(f'Spanwise positions [m]: {y_stations}')
            print(f'Torsion [N/m]: {torsion_stations_cop}')
            print(f'Cross-section Areas [m2]: {cross_section_areas_cop}')
            print(f'Shear stress [Pa]: {self.shear_stress_each_node}')

        # Step 8 (optional): Plot
        if plot:
            fig = plt.figure()
            plt.plot(y_stations, self.shear_stress_each_node/1e6)
            plt.xlabel("Spanwise Position [m]")
            plt.ylabel("Shear Stress [MPa]")
            plt.title("Shear Stress Distribution")
            fig.savefig('shear_stress_distribution.png')
            plt.show()

        return self.shear_stress_each_node
            

    def step_shear_forces(self,
                          reduced_sectional_spanwise_positions:float,
                          modified_sectional_lifts_schrenk: float,
                          debug: bool,
                          plot: bool):
        
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
        internal_bending_moments_cop = np.concatenate([[0], cumulative_trapezoid(self.internal_shear_forces_cop[::-1], self.y_stations_cop[::-1])])[::-1]
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
            fig.savefig('bending_moment_distribution.png')
            plt.show()
        return self.internal_bending_moments

        return self.internal_bending_moments


if __name__=='__main__':
        material_1 = Material(density=1600,
                            elastic_modulus=70e9,
                            shear_modulus=5e9,
                            poisson_ratio=0.3,
                            yield_strength=600e6,
                            fracture_strength=600e6
                            )
        material_2  = Material(density=75,
                            elastic_modulus=1.5e6,
                            shear_modulus=1.3e6,
                            poisson_ratio=0.3,
                            yield_strength=600e6,
                            fracture_strength=600e6
                            )
        
        planform=Planform(
            aspect_ratio=20.0,
            span=10.0,
            sweep_quarter_deg=0.0,
            taper=0.5,
            thickness_to_chord=0.12,
            cm_quarter_chord=1.0,
            wetted_surface_ratio=1.0,
            interference_factor=1.0,
            clmax=1.5,
            flap=False,
        )

        wing_model= WingModel(
                 wing_leng_m=10,
                 wing_skin_thickness_m =0.01,
                 number_of_nodes=100,
                 material_1 = material_1,
                 material_2 = material_2,
                 planform = planform,
                 )

        # Quick sanity-run of torsion computation
        nr_sections =100
        span_poz, lift_span = planform.estimate_conservative_lift_distribution(diameter_fuselage=0.31,
                                                     positive_manoeuvring_limit_load_factor=6.0,
                                                     initial_total_aircraft_mass=50.0,
                                                     number_of_stations=wing_model.number_of_nodes)
        c_stations = planform.sectional_properties(number_of_sections=wing_model.number_of_nodes)[0]

        y_station_chord = planform.sectional_properties(number_of_sections=wing_model.number_of_nodes)[2]
        
        torsion = wing_model.step_torsion_determination(c_stations, y_station_chord, span_poz, lift_span,True)
        
        wing_model.step_shear_forces(reduced_sectional_spanwise_positions=span_poz,
                                                  modified_sectional_lifts_schrenk=lift_span,debug = False, plot = False)
        wing_model.step_moment(debug = False, plot = False)
        rotation = wing_model.step_rotation_of_wing(material_1.shear_modulus ,planform.thickness_to_chord,wing_model.wing_skin_thickness_m,c_stations,torsion,y_station_chord,True)
        deflection  = wing_model.step_vertical_defletion(y_station_chord,material_1.elastic_modulus,c_stations,planform.thickness_to_chord,True)

        c_stations = planform.sectional_properties(number_of_sections=100)[0]
        
        
        shear = wing_model.step_shear_stress(reduced_sectional_spanwise_positions=span_poz, modified_sectional_lifts_schrenk=lift_span, debug = True, plot = True)
        p_crush = wing_model.step_crushing_pressure(c_stations,material_1.elastic_modulus,planform.thickness_to_chord,y_station_chord)
        
        

"""DEPRICATED """

"""

#rotation = wing_model.step_rotation_of_wing(material_1.shear_modulus , material_2.shear_modulus,planform.thickness_to_chord,wing_model.wing_skin_thickness_m,c_stations,torsion,y_station_chord)
        

        #print(c_stations)
        #torsion = wing_model.step_torsion_determination(c_stations,nr_sections,span_poz,lift_span)
        #print(torsion)
        #wing_model.step_shear_stress(reduced_sectional_spanwise_positions=span_poz, nr_sections=nr_sections,
        #                                    modified_sectional_lifts_schrenk=lift_span, debug = False, plot = False)
        #print("The lengh of the chords are", c_stations)
        #perimeter = wing_model.perimeter_of_section(c_stations,planform.thickness_to_chord)
        #print("The tosrions at each section are", torsion)
"""
