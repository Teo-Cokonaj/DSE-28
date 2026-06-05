import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import math
from scipy.optimize import root_scalar
from scipy.integrate import cumulative_trapezoid
import parameters
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



    def step_torsion_determination(self):
        c_stations, sectional_areas, y_stations, dy = self.planform.sectional_properties(number_of_sections=self.number_of_nodes)
        reduced_sectional_spanwise_positions, modified_sectional_lifts_schrenk = self.planform.estimate_conservative_lift_distribution(
            diameter_fuselage=0.31,
            positive_manoeuvring_limit_load_factor=6.0,
            initial_total_aircraft_mass=50.0,
            number_of_stations=self.number_of_nodes,
        )

        torsion_per_node_single = modified_sectional_lifts_schrenk * (c_stations / 4.0)
        torsion_per_node_tot = np.cumsum(torsion_per_node_single[::-1])[::-1]

        return torsion_per_node_tot


    def step_vertical_defletion():
    #still need to understand the stuff of this I will ask more from teo
        return deflection

    def step_rotation_of_wing(self):
        

    
        return rotation

    def step_shear_stress(self, debug: bool, plot: bool):
    #need torque, area and wall thickness --> for a thin-walled section, tau = T/(2tA)
    # area = assume elliptical shape --> chord, thickness at a given location
    # torsion modelled by Alex
    # thickness = wing skin thickness

        # Step 1: Find the chord length for each station
        c_stations, _, y_stations, _ = self.planform.sectional_properties(number_of_sections=self.number_of_nodes)

        # Step 2: Initialize cross section area, as well as chord length and spanwise position for section midpoints
        cross_section_area = np.zeros_like(c_stations[1:])
        c_mid_station = np.zeros_like(c_stations[1:])
        y_mid_station = np.zeros_like(c_stations[1:])

        # Step 3: Calculate the cross section area of each section (assume an ellipse)
        for i in range(len(cross_section_area)):
            c_mid_station[i] = 0.5 * (c_stations[i] + c_stations[i + 1])
            y_mid_station[i] = 0.5 * (y_stations[i] + y_stations[i + 1])
            thickness_station = c_mid_station[i] * self.planform.thickness_to_chord

            cross_section_area[i] = np.pi * 0.5*c_mid_station[i] * 0.5*thickness_station
            
        # Step 4: Get the skin thickness
        thickness_skin = self.wing_skin_thickness_m

        # Step 5: Get the torsion
        torsion_stations = None
        
        # Step 6: Calculate the shear stress
        shear_wall = np.zeros_like(cross_section_area)

        for j in range(len(cross_section_area)):
            shear_wall[i] = torsion_stations[i]/(2*thickness_skin*cross_section_area[i])

        # Step 7 (optional): print values for debug
        if debug:
            print(f'Number of stations: {len(c_stations)}')
            print(f'Assumed thickness-to-chord: {self.planform.thickness_to_chord}')
            print(f'Skin thickness: {thickness_skin} m')
            print(f'Chord lengths: {c_mid_station} m')
            print(f'Spanwise positions: {y_mid_station} m')
            print(f'Shear stress: {shear_wall} Pa')

        # Step 8 (optional): Plot
        if plot:
            fig = plt.figure()
            plt.plot(y_mid_station, shear_wall)
            plt.title("Shear Stress Distribution")
            fig.savefig('shear_stress_distribution.png')
            plt.show()
            
        return shear_wall

    def step_shear_forces(self):
    #lift and segment where it is applied
    # dV/dx = -w(x) --> distributed lift
    # V(x) = int^x_0(-w(x)dx)
        
        # Step 1: Find the distributed load (lift) on the wing

        # Step 2: Integrate to get the shear force

        # Step 3: Plot

        return shear_force

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
            span=2.0,
            sweep_quarter_deg=0.0,
            taper=1.0,
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
        torsion = wing_model.step_torsion_determination()
        print("Torsion array shape:", getattr(torsion, 'shape', None))