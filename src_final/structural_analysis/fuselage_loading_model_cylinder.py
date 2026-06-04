import aerosandbox.numpy as np
import matplotlib.pyplot as plt
import math
from scipy.integrate import cumulative_trapezoid
# import win32com.client
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))
from src_final.structural_analysis.Material import Material
from src_final.global_parameters import CONSTANTS

class FuselageModel:
    def __init__(self,
                 fuselage_length_m: float,
                 fuselage_diameter_m: float,
                 minimum_fuselage_thickness_mm: float,
                 material: Material,
                 main_wing_position_m: float,
                 main_wing_mass_kg: float,
                 horizontal_tail_position_m: float,
                 horizontal_tail_mass_kg: float,
                 landing_gear_position_m: float,
                 landing_gear_mass_kg: float,
                 number_of_nodes: int,
                 canard_position_m: float,
                 canard_mass_kg: float,
                 canard_lift_fraction: float = None,             
                 ):
        
        self.fuselage_length_m=fuselage_length_m
        self.fuselage_diameter_m=fuselage_diameter_m
        self.minimum_thickness_mm=minimum_fuselage_thickness_mm
        self.material=material
        self.main_wing_position_m=main_wing_position_m
        self.horizontal_tail_position_m=horizontal_tail_position_m
        self.number_of_nodes=number_of_nodes
        self.landing_gear_position_m=landing_gear_position_m
        self.canard_position_m=canard_position_m
        self.canard_lift_fraction=canard_lift_fraction
        self.main_wing_mass_kg=main_wing_mass_kg
        self.horizontal_tail_mass_kg=horizontal_tail_mass_kg
        self.landing_gear_mass_kg=landing_gear_mass_kg
        self.canard_mass_kg=canard_mass_kg
        

    def create_nodes(self):
        self.nodes = np.linspace(0, self.fuselage_length_m, self.number_of_nodes)
        self.node_spacing = self.nodes[1]-self.nodes[0]
        self.masses=np.zeros_like(self.nodes)


    def assign_structural_mass(self):
        #thin-walled assumption
        self.total_fuselage_structural_mass=(self.fuselage_diameter_m*np.pi*(self.minimum_thickness_mm/1000))*self.fuselage_length_m*self.material.density
        fuselage_mass_per_node=self.total_fuselage_structural_mass/self.number_of_nodes
        self.masses+=fuselage_mass_per_node
        self.masses[np.argmin(np.abs(self.nodes-self.main_wing_position_m))]+=self.main_wing_mass_kg
        self.masses[np.argmin(np.abs(self.nodes-self.canard_position_m))]+=self.canard_mass_kg
        self.masses[np.argmin(np.abs(self.nodes-self.landing_gear_position_m))]+=self.landing_gear_mass_kg
        self.masses[np.argmin(np.abs(self.nodes-self.horizontal_tail_position_m))]+=self.horizontal_tail_mass_kg


    def assign_nonstructural_mass(self,
                      component_mass: float,
                      component_cg_position_along_fuselage: float,
                      component_length_m: float):
        component_front_position_along_fuselage=component_cg_position_along_fuselage-component_length_m/2
        component_aft_position_along_fuselage=component_front_position_along_fuselage+component_length_m
        front_node_idx=np.argmin(np.abs(self.nodes-component_front_position_along_fuselage))
        aft_node_idx = np.argmin(np.abs(self.nodes-component_aft_position_along_fuselage))
        mass_per_node=component_mass/(aft_node_idx-front_node_idx+1) #uniform weight assumption
        self.masses[front_node_idx:aft_node_idx]+=mass_per_node


    def calculate_loads_flight(self):
        self.total_aircraft_mass=np.sum(self.masses)
        print('Total aircraft mass: ',self.total_aircraft_mass)
        self.L_canard=self.canard_lift_fraction*self.total_aircraft_mass*CONSTANTS.G0
        print('Canard lift: ',self.L_canard)
        
        # Set up the matrices for A * x = B
        A = np.array([
            [1.0, 1.0],                                  
            [self.main_wing_position_m, self.horizontal_tail_position_m]              
        ])

        B = np.array([
            [(1-self.canard_lift_fraction)*self.total_aircraft_mass*CONSTANTS.G0],                                # Force constants
            [np.sum(self.nodes*self.masses*CONSTANTS.G0) - self.canard_lift_fraction*self.total_aircraft_mass*CONSTANTS.G0*self.canard_position_m]       # Moment constants
        ])

        solution = np.linalg.solve(A, B)
        self.L_main_wing=solution[0][0]
        self.L_horizontal_tail=solution[1][0]
        
        #loads due to weight
        self.loads = -(self.masses*CONSTANTS.G0).copy() #positive load upwards

        # Apply point loads to the load vector
        locs = [self.canard_position_m, self.main_wing_position_m, self.horizontal_tail_position_m]
        vals = [self.L_canard, self.L_main_wing, self.L_horizontal_tail]
        for loc, val in zip(locs, vals):
            self.loads[np.argmin(np.abs(self.nodes-loc))] += val

        self.internal_shear_forces = np.cumsum(self.loads) #positive downwards

        self.internal_bending_moments = cumulative_trapezoid(y=self.internal_shear_forces,
                                                             x=self.nodes,
                                                             initial=0)


    def compute_sectional_properties(self,
                                     t_skin_mm: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
        r_o = self.fuselage_diameter_m/2
        r_i = r_o - t_skin_mm/1000
        y_bar = (4/(3*math.pi))*(r_o**2 + r_o*r_i + r_i**2)/(r_o+r_i)
        area = (math.pi/2)*(r_o**2 - r_i**2)
        Q = y_bar * area
        I_xx =np.pi/4*(r_o**4 - r_i**4)

        return Q, I_xx
    
    
    def calculate_buckling_stress(self,
                                  t_skin: np.ndarray,
                                  ) -> np.ndarray:
        '''Calculate buckling stress of thin-walled cylinders'''

        phi=1/16*np.sqrt(self.fuselage_diameter_m/2/t_skin)
        gamma=1.0-0.901*(1-np.exp(-phi))
        sigma_cr=gamma*(self.material.elastic_modulus*t_skin)/(math.sqrt(3*(1-self.material.poisson_ratio**2))*self.fuselage_diameter_m/2)

        return sigma_cr
    

    def thickness_utils(self,
                        thicknesses_m: np.ndarray) -> tuple[np.ndarray,np.ndarray]:

        Q, I = self.compute_sectional_properties(t_skin_mm=thicknesses_m*1000)
        tau_shear = self.internal_shear_forces * Q / (I * thicknesses_m)
        sigma_bending = self.internal_bending_moments*self.fuselage_diameter_m/(2*I)
        sigma_buckling = self.calculate_buckling_stress(thicknesses_m)

        maximum_allowed_normal_stress = np.minimum(self.material.yield_strength, sigma_buckling)
        maximum_allowed_shear_stress = 0.5*self.material.yield_strength #Tresca
        bending_util = sigma_bending / maximum_allowed_normal_stress
        shear_util = tau_shear / maximum_allowed_shear_stress

        #print('Bending util: ',bending_util)
        #print('Shear util: ',shear_util)

        return bending_util, shear_util


    def evaluate_thickness(self,
                           maximum_allowed_thickness_mm: float,
                           thickness_step_mm: float):
        self.thicknesses_m = np.ones_like(self.nodes)*self.minimum_thickness_mm/1000
        print('self.thicknesses_m: ',self.thicknesses_m)
        
        bending_util, shear_util = self.thickness_utils(self.thicknesses_m)
        while len(self.thicknesses_m[(bending_util>1.0)|(shear_util>1.0)])>0:
            self.thicknesses_m[(bending_util>1.0)|(shear_util>1.0)] +=thickness_step_mm/1000
            assert len(self.thicknesses_m[self.thicknesses_m>(maximum_allowed_thickness_mm/1000)])==0, "Maximum thickness exceeded!"
            bending_util, shear_util = self.thickness_utils(self.thicknesses_m)


    def plot_external_loads(self):
        plt.figure(figsize=(10, 4))
        plt.plot(self.nodes, self.loads)
        plt.title('Combined external loads on fuselage')
        plt.xlabel('Position along Fuselage (m)')
        plt.ylabel('Load (N)')
        plt.grid()
        plt.legend()
        plt.show()


    def plot_shear_and_moment_diagrams(self):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        ax1.plot(self.nodes, self.internal_shear_forces, label='Shear Force (N)', color='blue')
        ax1.set_title('Shear Force Diagram')
        ax1.set_xlabel('Position along Fuselage (m)')
        ax1.set_ylabel('Shear Force (N)')
        ax1.grid()
        ax1.legend()
        
        ax2.plot(self.nodes, self.internal_bending_moments, label='Bending Moment (Nm)', color='red')
        ax2.set_title('Bending Moment Diagram')
        ax2.set_xlabel('Position along Fuselage (m)')
        ax2.set_ylabel('Bending Moment (Nm)')
        ax2.grid()
        ax2.legend()
        
        #plt.suptitle('suptitle')
        plt.tight_layout()
        plt.show()


    def plot_required_thickness(self):
        plt.figure(figsize=(10, 4))
        plt.plot(self.nodes, self.thicknesses_m*1000)
        plt.xlabel("Position along fuselage [m]")
        plt.ylabel("Required skin thickness [mm]")
        #plt.title('title')
        plt.grid()
        plt.show()


# def plot_3d_fuselage(x_array, thicknesses, R_outer):
#     import trimesh
#     import numpy as np
#     np.infty = np.inf  # Inject the missing attribute back into NumPy
#     import pyrender
    
#     # --- VISUAL SCALING KNOBS ---
#     # Adjust these to make the variations pop in your viewer
#     THICKNESS_MULTIPLIER = 10.0  # Blows up the thickness (e.g., 2mm becomes 100mm)
#     LENGTH_COMPRESSION = 0.3    # Squashes the length to 30% of actual size
#     # ----------------------------

#     num_angles = 50
#     num_stations = len(x_array)
    
#     vertices = []
#     faces = []
#     face_colors = []

#     color_outer = [200, 200, 200, 255]  
#     color_inner = [160, 160, 160, 255]  
#     color_cut = [255, 69, 0, 255]       

#     # 1. Generate Vertices with Scaling applied
#     for x_val, t in zip(x_array, thicknesses):
#         theta = np.linspace(0, np.pi, num_angles)  
        
#         # Apply exaggeration to the thickness value
#         exaggerated_t = t * THICKNESS_MULTIPLIER
        
#         # Apply compression to the longitudinal distance
#         scaled_x = x_val * LENGTH_COMPRESSION
        
#         # Outer arc vertices
#         for th in theta:
#             vertices.append([scaled_x, R_outer * np.cos(th), R_outer * np.sin(th)])
#         # Inner arc vertices
#         for th in theta:
#             vertices.append([scaled_x, (R_outer - exaggerated_t) * np.cos(th), (R_outer - exaggerated_t) * np.sin(th)])

#     vertices = np.array(vertices)
#     verts_per_station = 2 * num_angles  

#     # 2. Generate Faces (Stitching logic remains unchanged)
#     for i in range(num_stations - 1):
#         st1 = i * verts_per_station       
#         st2 = (i + 1) * verts_per_station 
        
#         for j in range(num_angles - 1):
#             o1, o2 = st1 + j, st1 + j + 1
#             o3, o4 = st2 + j, st2 + j + 1
#             faces.append([o1, o2, o4])
#             faces.append([o1, o4, o3])
#             face_colors.append(color_outer)
#             face_colors.append(color_outer)
            
#             i1, i2 = st1 + num_angles + j, st1 + num_angles + j + 1
#             i3, i4 = st2 + num_angles + j, st2 + num_angles + j + 1
#             faces.append([i1, i4, i2]) 
#             faces.append([i1, i3, i4])
#             face_colors.append(color_inner)
#             face_colors.append(color_inner)

#         # Side Cut-Out Flat Edges
#         faces.append([st1, st2, st2 + num_angles])
#         faces.append([st1, st2 + num_angles, st1 + num_angles])
#         face_colors.append(color_cut)
#         face_colors.append(color_cut)
        
#         to1 = st1 + num_angles - 1
#         to2 = st2 + num_angles - 1
#         ti1 = st1 + (2 * num_angles) - 1
#         ti2 = st2 + (2 * num_angles) - 1
        
#         faces.append([to1, ti2, to2])
#         faces.append([to1, ti1, ti2])
#         face_colors.append(color_cut)
#         face_colors.append(color_cut)

#     # 3. Flat End Caps
#     for start_idx in [0, (num_stations - 1) * verts_per_station]:
#         for j in range(num_angles - 1):
#             o1, o2 = start_idx + j, start_idx + j + 1
#             i1, i2 = start_idx + num_angles + j, start_idx + num_angles + j + 1
#             if start_idx == 0:
#                 faces.append([o1, i2, o2])
#                 faces.append([o1, i1, i2])
#             else: 
#                 faces.append([o1, o2, i2])
#                 faces.append([o1, i2, i1])
#             face_colors.append(color_cut)
#             face_colors.append(color_cut)

#     faces = np.array(faces)
#     face_colors = np.array(face_colors)
    
#     mesh = trimesh.Trimesh(vertices=vertices, faces=faces, face_colors=face_colors)


#     # Convert the trimesh geometry to a pyrender mesh
#     pr_mesh = pyrender.Mesh.from_trimesh(mesh, smooth=False)

#     # Create a scene and add the mesh
#     scene = pyrender.Scene(ambient_light=[0.3, 0.3, 0.3])
#     scene.add(pr_mesh)

#     # Launch the high-fidelity interactive viewer
#     # use_raymond_lighting adds a professional 3-point light setup automatically
#     pyrender.Viewer(scene, use_raymond_lighting=True, viewport_size=(1920, 1080))
#     return

if __name__=='__main__':
        material = Material(density=1600,
                            elastic_modulus=70e9,
                            shear_modulus=5e9,
                            poisson_ratio=0.3,
                            yield_strength=600e6,
                            fracture_strength=600e6
                            )
        
        fuselage_model= FuselageModel(
                 fuselage_length_m=3.0,
                 fuselage_diameter_m= 0.3,
                 minimum_fuselage_thickness_mm=1e-6,
                 material=material,
                 main_wing_position_m=1.0,
                 main_wing_mass_kg=10.0,
                 horizontal_tail_position_m=3.0,
                 horizontal_tail_mass_kg=3.0,
                 landing_gear_position_m=1.5,
                 landing_gear_mass_kg=3.0,
                 number_of_nodes=10,
                 canard_position_m=0.2,
                 canard_mass_kg=1.0,
                 canard_lift_fraction=0.2,             
                 )
        
        fuselage_model.create_nodes()
        fuselage_model.assign_structural_mass()
        #fuselage_model.assign_nonstructural_mass()
        fuselage_model.calculate_loads_flight()
        fuselage_model.plot_external_loads()
        fuselage_model.plot_shear_and_moment_diagrams()
        fuselage_model.evaluate_thickness(maximum_allowed_thickness_mm=1.0,
                                          thickness_step_mm=0.1)        
        fuselage_model.plot_required_thickness()