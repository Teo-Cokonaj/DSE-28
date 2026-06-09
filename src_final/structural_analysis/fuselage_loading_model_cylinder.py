from aerosandbox import Atmosphere
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import math
from scipy.integrate import cumulative_trapezoid, quad
from scipy.interpolate import interp1d
# import win32com.client
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..')))
from src_final.structural_analysis.wing_loading import WingModel
from src_final.structural_analysis.Material import Material
from src_final.global_parameters import CONSTANTS, Assumptions
from src_final.Aircraft.Planform import Planform

class FuselageModel:
    def __init__(self,
                 minimum_fuselage_thickness_mm: float,
                 material: Material,
                 wing_model: WingModel,
                 number_of_nodes: int,
                 canard_lift_fraction: float,  
                 ):
        
        self.minimum_thickness_mm=minimum_fuselage_thickness_mm
        self.material=material
        self.number_of_nodes=number_of_nodes
        self.canard_lift_fraction=canard_lift_fraction
        #self.moment_due_to_wing=wing_model.tosrion_node_tot[0]

        
    def create_nodes(self):
        self.nodes = np.linspace(0, self.fuselage_length_m, self.number_of_nodes)
        self.masses = np.zeros_like(self.nodes)


    def load_components_from_csv(self,
                                 csv_path: str):
        
        df = pd.read_csv(csv_path)

        def get_cg_x(name_prefix: str):
            mask = df["Component Name"].str.startswith(name_prefix)
            if not mask.any():
                raise ValueError(f"CSV must contain a '{name_prefix}' entry.")
            return df[mask].iloc[0]["Assembly CG X (m)"]
        
        def get_mass(name_prefix: str):
            mask = df["Component Name"].str.startswith(name_prefix)
            if not mask.any():
                raise ValueError(f"CSV must contain a '{name_prefix}' entry.")
            return df[mask].iloc[0]["Mass (kg)"]

        # Fuselage length and node initialisation
        main_body_mask = df["Component Name"].str.startswith("Main Body")
        if not main_body_mask.any():
            raise ValueError("CSV must contain a 'Main Body' entry to define fuselage length.")
        main_body = df[main_body_mask].iloc[0]
        self.fuselage_length_m = main_body["Size X (m)"]
        self.create_nodes()

        # Key structural positions
        self.canard_x_m              = get_cg_x("Canard")
        self.main_wing_x_m           = get_cg_x("Main Wing")
        self.horizontal_tail_x_m     = get_cg_x("Horizontal_TailPlane")
        self.vertical_tail_x_m       = get_cg_x("Vertical_Tail")
        self.landing_gear_x_m = get_cg_x("Metal Strut")
        self.baseline_fuselage_mass = get_mass("Main Body")
        

        if abs(self.canard_lift_fraction)>1e-3:
            skip = {"C. Port Cover <1>","C. Port Foam <1>"}
        else:
            skip = {"Canard"}

        for _, row in df.iterrows():
            if row["Component Name"]=="Main Body <1>":
                self.fuselage_diameter_m=row["Size Y (m)"]

            if row["Component Name"]=="Vertical_Tail <3>":
                self.vertical_tail_height_m=row["Size Z (m)"]
                
            name = row["Component Name"]
            if any(name.startswith(prefix) for prefix in skip):
                continue

            self.assign_mass(
                    component_mass=row["Mass (kg)"],
                    component_cg_position_along_fuselage=row["Assembly CG X (m)"],
                    component_length_m=row["Size X (m)"],
                )


    def assign_mass(self,
                    component_mass: float,
                    component_cg_position_along_fuselage: float,
                    component_length_m: float):

        component_front = component_cg_position_along_fuselage - component_length_m / 2
        component_aft   = component_front + component_length_m
        fuselage_end    = self.nodes[-1]

        # Split mass proportionally between interior and overflow
        if component_aft > fuselage_end and component_front<fuselage_end:
            interior_fraction = (fuselage_end - component_front) / (component_aft - component_front)
            overflow_mass     = component_mass * (1.0 - interior_fraction)
            interior_mass     = component_mass * interior_fraction
        elif component_aft>fuselage_end and component_front>fuselage_end:
            interior_mass=0.0
            overflow_mass=component_mass
        else:
            interior_mass = component_mass
            overflow_mass = 0.0

        front_node_idx = np.argmin(np.abs(self.nodes - component_front))
        aft_node_idx   = np.argmin(np.abs(self.nodes - component_aft))

        n_nodes = aft_node_idx - front_node_idx + 1
        self.masses[front_node_idx:aft_node_idx + 1] += interior_mass / n_nodes
        self.masses[-1] += overflow_mass


    def calculate_loads_flight(self,
                               load_factor: float,
                               ):
        self.total_aircraft_mass=np.sum(self.masses)
        self.L_canard=self.canard_lift_fraction*load_factor*self.total_aircraft_mass*CONSTANTS.G0
        
        # Set up the matrices for A * x = B
        A = np.array([
            [1.0, 1.0],                                  
            [self.main_wing_x_m, self.horizontal_tail_x_m]              
        ])

        B = np.array([
            [(1-self.canard_lift_fraction)*load_factor*self.total_aircraft_mass*CONSTANTS.G0],                                # Force constants
            [np.sum(self.nodes*load_factor*self.masses*CONSTANTS.G0) - self.canard_lift_fraction*load_factor*self.total_aircraft_mass*CONSTANTS.G0*self.canard_x_m]       # Moment constants
        ])

        solution = np.linalg.solve(A, B)
        self.L_main_wing=solution[0][0]
        self.L_horizontal_tail=solution[1][0]

        self.loads=np.zeros_like(self.nodes)

        # loads due to wing, canard, tail
        locs = [self.canard_x_m, self.main_wing_x_m, self.horizontal_tail_x_m]
        vals = [self.L_canard, self.L_main_wing, self.L_horizontal_tail]
        for loc, val in zip(locs, vals):
            self.loads[np.argmin(np.abs(self.nodes-loc))] += val
            #print('Loads: ',self.loads)
        #loads due to weight
        self.loads -=self.masses*CONSTANTS.G0*load_factor
        self.empennage_torque=self.calculate_empennage_torque()

        self.calculate_internal_loads()

    
    def calculate_loads_landing(self,
                                landing_deceleration_in_terms_of_g: float):
        self.total_aircraft_mass=np.sum(self.masses)
        self.L_canard=self.canard_lift_fraction*self.total_aircraft_mass*CONSTANTS.G0
        self.force_landing_gear = abs(landing_deceleration_in_terms_of_g)*self.total_aircraft_mass*CONSTANTS.G0
        
        # Set up the matrices for A * x = B
        A = np.array([
            [1.0, 1.0],                                  
            [self.main_wing_x_m, self.horizontal_tail_x_m]              
        ])

        B = np.array([
            [(1-self.canard_lift_fraction)*self.total_aircraft_mass*CONSTANTS.G0],                # Force constants
            [np.sum(self.nodes*self.masses*CONSTANTS.G0) - self.canard_lift_fraction*self.total_aircraft_mass*CONSTANTS.G0*self.canard_x_m]       # Moment constants
        ])

        solution = np.linalg.solve(A, B)
        self.L_main_wing=solution[0][0]
        self.L_horizontal_tail=solution[1][0]

        self.center_of_mass_position=np.sum(self.nodes*self.masses*CONSTANTS.G0)/np.sum(self.masses*CONSTANTS.G0)
        self.MMOI_cg=np.sum(self.masses*(self.nodes-self.center_of_mass_position)**2)

        self.loads=np.zeros_like(self.nodes)
        
        #loads due to wing, canard, tail
        locs = [self.canard_x_m, self.main_wing_x_m, self.horizontal_tail_x_m, self.landing_gear_x_m]
        vals = [self.L_canard, self.L_main_wing, self.L_horizontal_tail, self.force_landing_gear]
        for loc, val in zip(locs, vals):
            self.loads[np.argmin(np.abs(self.nodes-loc))] += val
        #loads due to weight
        self.loads -=self.masses*CONSTANTS.G0

        self.external_moment_sum_about_cg=np.sum((self.nodes-self.center_of_mass_position)*self.loads)
        self.rotational_acceleration = self.external_moment_sum_about_cg/self.MMOI_cg
        self.accelerations=abs(landing_deceleration_in_terms_of_g)*CONSTANTS.G0+self.rotational_acceleration*(self.nodes-self.center_of_mass_position)

        self.loads -=self.masses*self.accelerations

        self.empennage_torque=self.calculate_empennage_torque()

        self.calculate_internal_loads()


    def calculate_empennage_torque(self) -> float:
        
        atmosphere=Atmosphere(altitude=8230.0) #altitude of Mach max
        assumptions=Assumptions()
        airspeed=float(assumptions.mach_max*atmosphere.speed_of_sound())

        dynamic_pressure=float(0.5*atmosphere.density()*airspeed**2)
        C_L_max=0.9*assumptions.VT_clmax #no sweep of VT, conservative
        torque=self.vertical_tail_height_m/2*C_L_max*dynamic_pressure*assumptions.VT_surface_area_m2

        return torque

        
    #def calculate_attachment_stresses(self):
        

    def calculate_internal_loads(self):
        self.internal_shear_forces = np.cumsum(self.loads) #positive downwards
        self.internal_shear_forces = interp1d(self.nodes,
                                              self.internal_shear_forces,
                                    kind='zero',
                                    fill_value='extrapolate')
        
        fine_nodes = np.linspace(self.nodes[0], self.nodes[-1], 100 * len(self.nodes))
        shear_fine = self.internal_shear_forces(fine_nodes)
        self.internal_bending_moments = np.concatenate([[0], cumulative_trapezoid(shear_fine, fine_nodes)])
        self.internal_bending_moments = interp1d(
                                     fine_nodes,
                                     self.internal_bending_moments,
                                     kind='linear')
        self.internal_torques = np.zeros_like(fine_nodes)
        self.internal_torques[np.argmin(np.abs(fine_nodes - self.main_wing_x_m)):-1] += self.empennage_torque

        self.internal_torques = interp1d(
                                     fine_nodes,
                                     self.internal_torques,
                                     kind='linear')
        

    def compute_sectional_properties(self,
                                     t_skin_mm: np.ndarray) -> tuple[np.ndarray,np.ndarray,float]:
        r_o = self.fuselage_diameter_m/2
        r_i = r_o - t_skin_mm/1000
        y_bar = (4/(3*math.pi))*(r_o**2 + r_o*r_i + r_i**2)/(r_o+r_i)
        area = (math.pi/2)*(r_o**2 - r_i**2)
        Q = y_bar * area
        I_xx =np.pi/4*(r_o**4 - r_i**4)
        enclosed_area=(self.fuselage_diameter_m/2)**2*np.pi

        return Q, I_xx, enclosed_area
    
    
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

        Q, I, enclosed_area = self.compute_sectional_properties(t_skin_mm=thicknesses_m*1000)
        tau_shear = np.abs(self.internal_shear_forces(self.nodes) * Q / (I * thicknesses_m))+np.abs(self.internal_torques(self.nodes)/thicknesses_m/2/enclosed_area)
        sigma_bending = np.abs(self.internal_bending_moments(self.nodes)*self.fuselage_diameter_m/(2*I))
        sigma_buckling = np.abs(self.calculate_buckling_stress(thicknesses_m))

        ##print('Sigma bending [Mpa]: ',sigma_bending/1e6)
        ##print('Sigma buckling [Mpa]: ',sigma_buckling/1e6)

        maximum_allowed_normal_stress = np.minimum(0.7*self.material.yield_strength, sigma_buckling)
        ##print('Max allowed normal stress [Mpa]: ',maximum_allowed_normal_stress/1e6)
        maximum_allowed_shear_stress = 0.5*self.material.yield_strength #Tresca
        bending_util = sigma_bending / maximum_allowed_normal_stress
        shear_util = tau_shear / maximum_allowed_shear_stress

        ##print('Bending util: ',bending_util)
        ##print('Shear util: ',shear_util)

        return bending_util, shear_util


    def evaluate_thickness(self,
                           maximum_allowed_thickness_mm: float,
                           thickness_step_mm: float):
        self.thicknesses_m = np.ones_like(self.nodes)*self.minimum_thickness_mm/1000
        ##print('self.thicknesses_m: ',self.thicknesses_m)
        
        bending_util, shear_util = self.thickness_utils(self.thicknesses_m)
        while len(self.thicknesses_m[(bending_util>1.0)|(shear_util>1.0)])>0:
            self.thicknesses_m[(bending_util>1.0)|(shear_util>1.0)] +=thickness_step_mm/1000
            assert len(self.thicknesses_m[self.thicknesses_m>(maximum_allowed_thickness_mm/1000)])==0, "Maximum thickness exceeded!"
            bending_util, shear_util = self.thickness_utils(self.thicknesses_m)


    def plot_mass_distribution(self):
        plt.figure(figsize=(10, 4))
        plt.plot(self.nodes, self.masses)
        plt.title('Masses')
        plt.xlabel('Position along Fuselage (m)')
        plt.ylabel('Mass (kg)')
        plt.grid()
        plt.legend()
        plt.show()


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
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8))
        
        ax1.plot(self.nodes, self.internal_shear_forces(self.nodes), label='Shear Force (N)', color='blue')
        ax1.set_title('Shear Force Diagram')
        ax1.set_xlabel('Position along Fuselage (m)')
        ax1.set_ylabel('Shear Force (N)')
        ax1.grid()
        ax1.legend()
        
        ax2.plot(self.nodes, self.internal_bending_moments(self.nodes), label='Bending Moment (Nm)', color='red')
        ax2.set_title('Bending Moment Diagram')
        ax2.set_xlabel('Position along Fuselage (m)')
        ax2.set_ylabel('Bending Moment (Nm)')
        ax2.grid()
        ax2.legend()

        ax3.plot(self.nodes, self.internal_torques(self.nodes), label='Torque (Nm)', color='green')
        ax3.set_title('Torque Diagram')
        ax3.set_xlabel('Position along Fuselage (m)')
        ax3.set_ylabel('Torque (Nm)')
        ax3.grid()
        ax3.legend()
        
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
#             faces.append([i1, i3, i4])f
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
        
        material = Material(density=1600,
                            elastic_modulus=50e9,
                            shear_modulus=5e9,
                            poisson_ratio=0.3,
                            yield_strength=600e6,
                            fracture_strength=600e6
                            )
        
        fuselage_model= FuselageModel(
                 minimum_fuselage_thickness_mm=0.1,
                 material=material,
                 number_of_nodes=1000,
                 canard_lift_fraction=0.1, 
                 wing_model=wing_model            
                 )
        
        from pathlib import Path
        csv_path = Path(__file__).parent / "onshape_mass_distribution.csv"
        fuselage_model.load_components_from_csv(str(csv_path))
        fuselage_model.plot_mass_distribution()

        fuselage_model.calculate_loads_flight(9.0)
        #print('Internal shear forces (flight): ',fuselage_model.internal_shear_forces(fuselage_model.nodes))
        #print('Internal bending moments (flight): ',fuselage_model.internal_bending_moments(fuselage_model.nodes))        
        bending_util, shear_util = fuselage_model.thickness_utils(np.ones_like(fuselage_model.nodes)*fuselage_model.minimum_thickness_mm/1000)
        #print('Bending util (flight): ',bending_util)
        #print('Shear util (flight): ',shear_util)
        fuselage_model.plot_external_loads()
        fuselage_model.plot_shear_and_moment_diagrams()
        fuselage_model.evaluate_thickness(maximum_allowed_thickness_mm=1.0,
                                          thickness_step_mm=0.01)        
        fuselage_model.plot_required_thickness()

        fuselage_model.calculate_loads_landing(landing_deceleration_in_terms_of_g=4.0)
        ##print('Landing loads: ',fuselage_model.loads)
        #print('Internal shear forces (landing): ', fuselage_model.internal_shear_forces(fuselage_model.nodes))
        #print('Internal bending moments (landing): ',fuselage_model.internal_bending_moments(fuselage_model.nodes))
        bending_util, shear_util = fuselage_model.thickness_utils(np.ones_like(fuselage_model.nodes)*fuselage_model.minimum_thickness_mm/1000)
        #print('Bending util (landing): ',bending_util)
        #print('Shear util (landing): ',shear_util)
        fuselage_model.plot_external_loads()
        fuselage_model.plot_shear_and_moment_diagrams()
        fuselage_model.evaluate_thickness(maximum_allowed_thickness_mm=1.0,
                                          thickness_step_mm=0.01)        
        fuselage_model.plot_required_thickness()