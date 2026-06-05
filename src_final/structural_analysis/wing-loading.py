import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import math
from scipy.optimize import root_scalar
from scipy.integrate import cumulative_trapezoid
import parameters
from scipy.interpolate import interp1d
from parameters import *
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))
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
                 wing_tip_choad_m:float,
                 wing_root_chord_m: float,
                ):
        self.wing_leng_m = wing_leng_m
        self.wing_skin_thickness_m = wing_skin_thickness_m
        self.material_1=material_1
        self.material_2 = material_2
        self.number_of_nodes = number_of_nodes
        self.planform = planform
        self.wing_tip_choad_m = wing_tip_choad_m
        self.wing_root_chord_m = wing_root_chord_m


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
            return perimeter_crossection,area
    


    def step_torsion_determination(self,
            c_stations:float,
            y_stations:int,
            reduced_sectional_spanwise_positions: float,
            modified_sectional_lifts_schrenk:float
 ):
        """This code computes the torsion at each instant on the wing and it accounts for the 
            part of the beam that is also inside of the fuselage
        """
        self.lift_cont_forces = interp1d (reduced_sectional_spanwise_positions,modified_sectional_lifts_schrenk)
        c_stations_cop = c_stations[-np.size(reduced_sectional_spanwise_positions):]
        
        torsion_per_node_single = self.lift_cont_forces(reduced_sectional_spanwise_positions) * (c_stations_cop / 4.0)
        torsion_per_node_tot = np.cumsum(torsion_per_node_single[::-1])[::-1]

        self.tosrion_node_tot = interp1d(reduced_sectional_spanwise_positions,torsion_per_node_tot)
        
        torsion_each_node = self.tosrion_node_tot(reduced_sectional_spanwise_positions)
        torsion_each_node = np.concatenate(( np.full(np.size(c_stations) - np.size(torsion_each_node), torsion_each_node[0]),torsion_each_node))
        
<<<<<<< HEAD

=======
        #print(torsion_each_node, np.size(torsion_each_node))
>>>>>>> e1b2db3a731d2ce3d8bb9f065e4d3acb2cb60a73

        #print(self.lift_cont_forces(reduced_sectional_spanwise_positions))
        #plt.plot(y_stations,torsion_each_node)
        #plt.plot(reduced_sectional_spanwise_positions,modified_sectional_lifts_schrenk)
        #plt.show()
        return torsion_each_node

    def step_rotation_of_wing(self,
                              G1:float,
                              G2:float,
                              thicknes_to_chord:float,
                              skin_thickness:float,
                              chords:np.ndarray,
                              torsion:np.ndarray,
                              y_poz:np.ndarray
                              ):
        #fitst we compute the rotation of the outer shell
        """Get the torsion from pervious funtion"""
        #torsion = self.step_torsion_determination(c_stations, nr_sections,reduced_sectional_spanwise_positions,modified_sectional_lifts_schrenk)
        perimeter , area  = self.perimeter_area_of_section(chords,thicknes_to_chord)
        rotation_rate_shell = torsion * perimeter/(4 * area**2 * G1 * skin_thickness)
        rotation = cumulative_trapezoid(rotation_rate_shell,y_poz,initial = 0)
        rotation = np.squeeze(rotation)
        rotation_deg = np.degrees(rotation)
        #print(rotation)
        plt.plot(y_poz,rotation_deg)
        #plt.plot(y_poz,rotation_rate_shell)
        plt.show()
        return rotation
    


    
    def step_vertical_defletion():
    #still need to understand the stuff of this I will ask more from teo

        return deflection



    def step_shear_stress(self,
                          reduced_sectional_spanwise_positions: float,
                          nr_sections: int,
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
        cross_section_areas_cop = np.pi * 0.5 * c_stations_cop * 0.5 * y_stations_cop

        # Step 3: Get the skin thickness
        thickness_skin = self.wing_skin_thickness_m

        # Step 4: Get the torsion
        torsion_stations = self.step_torsion_determination(c_stations, nr_sections,reduced_sectional_spanwise_positions,modified_sectional_lifts_schrenk)
        torsion_stations_cop = torsion_stations[-np.size(reduced_sectional_spanwise_positions):]
        
        # Step 5: Calculate the shear stress
        shear_wall_cop = torsion_stations_cop/(2*thickness_skin*cross_section_areas_cop)

        # Step 6: Interpolate the shear
        self.shear_node_tot = interp1d(reduced_sectional_spanwise_positions,shear_wall_cop)
    
        shear_each_node = self.shear_node_tot(reduced_sectional_spanwise_positions)
        shear_each_node = np.concatenate(( np.full(np.size(c_stations) - np.size(shear_each_node), shear_each_node[0]), shear_each_node))
        
        # Step 7 (optional): print values for debug
        if debug:
            print(f'Number of stations [-]: {len(c_stations)}')
            print(f'Thickness-to-chord [-]: {self.planform.thickness_to_chord}')
            print(f'Skin thickness [m]: {thickness_skin}')
            print(f'Chord lengths [m]: {c_stations}')
            print(f'Spanwise positions [m]: {y_stations}')
            print(f'Torsion [N/m]: {torsion_stations_cop}')
            print(f'Cross-section Areas [m2]: {cross_section_areas_cop}')
            print(f'Shear stress [Pa]: {shear_each_node}')

        # Step 8 (optional): Plot
        if plot:
            fig = plt.figure()
            plt.plot(y_stations, shear_each_node)
            plt.xlabel("Spanwise Position [m]")
            plt.ylabel("Shear Stress [Pa]")
            plt.title("Shear Stress Distribution")
            fig.savefig('shear_stress_distribution.png')
            plt.show()
            
        return shear_each_node

    def step_shear_forces(self,
                          reduced_sectional_spanwise_positions:float,
                          modified_sectional_lifts_schrenk: float,
                          debug: bool,
                          plot: bool):
    #lift and segment where it is applied
    # dV/dx = -w(x) --> distributed lift
    # V(x) = int^x_0(-w(x)dx)
        
        # Step 1: Find the distributed load (lift) on the wing and the spanwise positions of each section
        self.lift_cont_forces = interp1d (reduced_sectional_spanwise_positions,modified_sectional_lifts_schrenk)
        _, _, y_stations, _ = self.planform.sectional_properties(number_of_sections=self.number_of_nodes)
        y_stations_cop = y_stations[-np.size(reduced_sectional_spanwise_positions):]

        # Step 2: Integrate to get the shear force
        lift_cont_forces_cop = self.lift_cont_forces(y_stations_cop)
        self.shear_cont_forces = cumulative_trapezoid(lift_cont_forces_cop,y_stations_cop, initial=0)

        # Step 3: Interpolate the shear
        self.shear_node_tot = interp1d(reduced_sectional_spanwise_positions,self.shear_cont_forces)
    
        shear_each_node = self.shear_node_tot(reduced_sectional_spanwise_positions)
        shear_each_node = shear_each_node[-1] - shear_each_node
        shear_each_node = np.concatenate(( np.full(np.size(c_stations) - np.size(shear_each_node), shear_each_node[0]), shear_each_node))
        
        # Step 3 (optional): print intermediate values for debug
        if debug:
            print(f'Number of sections: {nr_sections}')
            print(f'Spanwise positions [m]: {y_stations}')
            print(f'Distributed lift [N]: {lift_cont_forces_cop}')
            print(f'Shear force [N]: {shear_each_node}')             

        # Step 4 (optional): plot
        if plot:
            fig = plt.figure()
            plt.plot(y_stations, shear_each_node)
            plt.xlabel('Spanwise Position [m]')
            plt.ylabel("Shear Force [N]")
            plt.title("Shear Force Distribution")
            fig.savefig('shear_force_distribution.png')
            plt.show()
        
        return shear_each_node

    def step_moment():
    #distance from root and lift
    # dM/dx = V(x)
    # M(x) = int^x_0(V(x)dx)

        return moments

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
                 wing_tip_choad_m=0.2,
                 wing_root_chord_m=0.1,
                 )

        # Quick sanity-run of torsion computation
        nr_sections =100
        span_poz, lift_span = planform.estimate_conservative_lift_distribution(diameter_fuselage=0.31,
                                                     positive_manoeuvring_limit_load_factor=6.0,
                                                     initial_total_aircraft_mass=50.0,
                                                     number_of_stations=100)
        c_stations = planform.sectional_properties(number_of_sections=100)[0]
<<<<<<< HEAD
        y_station_chord = planform.sectional_properties(number_of_sections=100)[2]
        
        torsion = wing_model.step_torsion_determination(c_stations, y_station_chord, span_poz, lift_span)
        rotation = wing_model.step_rotation_of_wing(material_1.shear_modulus , material_2.shear_modulus,planform.thickness_to_chord,wing_model.wing_skin_thickness_m,c_stations,torsion,y_station_chord)
        shear = wing_model.step_shear_stress(reduced_sectional_spanwise_positions=span_poz, nr_sections=nr_sections, modified_sectional_lifts_schrenk=lift_span, debug = True, plot = True)
=======
        #print(c_stations)
        #torsion = wing_model.step_torsion_determination(c_stations,nr_sections,span_poz,lift_span)
        #print(torsion)
        shear = wing_model.step_shear_stress(reduced_sectional_spanwise_positions=span_poz, nr_sections=nr_sections,
                                             modified_sectional_lifts_schrenk=lift_span, debug = True, plot = True)
        shear_force = wing_model.step_shear_forces(reduced_sectional_spanwise_positions=span_poz,
                                                   modified_sectional_lifts_schrenk=lift_span,debug = False, plot = True)
>>>>>>> e1b2db3a731d2ce3d8bb9f065e4d3acb2cb60a73
