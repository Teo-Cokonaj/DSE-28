from aerosandbox import Atmosphere
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import math
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
                 canard_model: WingModel,
                 number_of_nodes: int,
                 canard_lift_fraction: float,  
                 ):
        
        self.minimum_thickness_mm=minimum_fuselage_thickness_mm
        self.material=material
        self.number_of_nodes=number_of_nodes
        self.canard_lift_fraction=canard_lift_fraction
        wing_model.planform_data()
        wing_model.force_per_unit(plot=False)
        canard_model.planform_data()
        canard_model.force_per_unit(plot=False)
        self.wing_torque = wing_model.step_torsion_determination(plot=False)[0]
        self.canard_torque = canard_model.step_torsion_determination(plot=False)[0]
        self.LG_length=0.17 #m
        self.fuselage_diameter_m=0.24

        
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

        self.canard_x_m              = get_cg_x("Canard")
        self.main_wing_x_m           = get_cg_x("Main Wing")
        self.horizontal_tail_x_m     = get_cg_x("Horizontal_TailPlane")
        self.vertical_tail_x_m       = get_cg_x("Vertical_Tail")
        self.landing_gear_x_m = get_cg_x("Rear_Strut")
        self.baseline_fuselage_mass = get_mass("Main Body")
        
        if abs(self.canard_lift_fraction)>1e-3:
            skip = {"C. Port Cover <1>","C. Port Foam <1>"}
        else:
            skip = {"Canard"}

        for _, row in df.iterrows():
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
        self.center_of_mass_position=np.sum(self.nodes*self.masses*CONSTANTS.G0)/np.sum(self.masses*CONSTANTS.G0)
        self.horizontal_tail_x_m=self.fuselage_length_m

        A = np.array([
            [1.0, 1.0],                                  
            [self.main_wing_x_m, self.horizontal_tail_x_m]              
        ])

        B = np.array([
            [load_factor*self.total_aircraft_mass*CONSTANTS.G0-self.L_canard],                                # Force constants
            [np.sum(self.nodes*self.masses*CONSTANTS.G0*load_factor)-self.canard_x_m*self.L_canard+self.wing_torque+self.canard_torque]       # Moment constants
        ])

        solution = np.linalg.solve(A, B)
        self.L_main_wing=solution[0][0]
        self.L_horizontal_tail=solution[1][0]

        self.external_loads=np.zeros_like(self.nodes)
        self.external_moments = np.zeros_like(self.nodes)
        self.accelerations = np.ones_like(self.nodes)*(load_factor-1)*CONSTANTS.G0

        # loads due to wing, canard, tail
        locs = [self.canard_x_m, self.main_wing_x_m, self.horizontal_tail_x_m]
        vals = [self.L_canard, self.L_main_wing, self.L_horizontal_tail]
        for loc, val in zip(locs, vals):
            self.external_loads[np.argmin(np.abs(self.nodes-loc))] += val
        
        locs = [self.canard_x_m, self.main_wing_x_m]
        vals = [self.canard_torque, self.wing_torque]
        for loc, val in zip(locs, vals):
            self.external_moments[np.argmin(np.abs(self.nodes-loc))] += val
    
        self.condition='flight'
        self.empennage_torque=self.calculate_empennage_torque()

        self.calculate_internal_loads()

    
    def calculate_loads_landing(self,
                                landing_deceleration_in_terms_of_g: float
                                ):
        self.total_aircraft_mass=np.sum(self.masses)
        self.L_canard=self.canard_lift_fraction*self.total_aircraft_mass*CONSTANTS.G0
        self.force_landing_gear = abs(landing_deceleration_in_terms_of_g)*self.total_aircraft_mass*CONSTANTS.G0
        self.center_of_mass_position=np.sum(self.nodes*self.masses*CONSTANTS.G0)/np.sum(self.masses*CONSTANTS.G0)
        self.MMOI_cg=np.sum(self.masses*(self.nodes-self.center_of_mass_position)**2)
        self.horizontal_tail_x_m=self.fuselage_length_m

        A = np.array([
            [1.0, 1.0],                                  
            [self.main_wing_x_m, self.horizontal_tail_x_m]              
        ])

        B = np.array([
            [self.total_aircraft_mass*CONSTANTS.G0-self.L_canard],                # Force constants
            [np.sum(self.nodes*self.masses*CONSTANTS.G0) -self.canard_x_m*self.L_canard+self.wing_torque+self.canard_torque]       # Moment constants
        ])

        solution = np.linalg.solve(A, B)
        self.L_main_wing=solution[0][0]
        self.L_horizontal_tail=solution[1][0]

        self.external_loads=np.zeros_like(self.nodes)
        self.external_moments = np.zeros_like(self.nodes)
        self.accelerations = np.zeros_like(self.nodes)
        
        #loads due to wing, canard, tail
        locs = [self.canard_x_m, self.main_wing_x_m, self.horizontal_tail_x_m, self.landing_gear_x_m]
        vals = [self.L_canard, self.L_main_wing, self.L_horizontal_tail, self.force_landing_gear]
        for loc, val in zip(locs, vals):
            self.external_loads[np.argmin(np.abs(self.nodes-loc))] += val

        locs = [self.canard_x_m, self.main_wing_x_m,self.landing_gear_x_m]
        vals = [self.canard_torque, self.wing_torque, -0.25*self.force_landing_gear*self.LG_length]
        for loc, val in zip(locs, vals):            
            self.external_moments[np.argmin(np.abs(self.nodes-loc))] += val

        self.external_moment_sum_about_cg=np.sum((self.nodes-self.center_of_mass_position)*self.external_loads-self.external_moments)
        self.rotational_acceleration = self.external_moment_sum_about_cg/self.MMOI_cg
        self.accelerations=abs(landing_deceleration_in_terms_of_g)*CONSTANTS.G0+self.rotational_acceleration*(self.nodes-self.center_of_mass_position)

        self.condition='landing'
        self.empennage_torque=self.calculate_empennage_torque()

        self.calculate_internal_loads()


    def calculate_empennage_torque(self,
                                   ) -> float:
        
        assumptions=Assumptions()
        
        if self.condition=='flight':
            atmosphere=Atmosphere(altitude=8230.0) #altitude of Mach max
            airspeed=float(assumptions.mach_max*atmosphere.speed_of_sound())

        elif self.condition=='landing':
            atmosphere=Atmosphere(0.0)
            airspeed = 50.0

        dynamic_pressure=float(0.5*atmosphere.density()*airspeed**2)
        C_L_max=0.9*assumptions.VT_clmax #no sweep of VT, conservative

        torque=self.vertical_tail_height_m/2*C_L_max*dynamic_pressure*assumptions.VT_surface_area_m2

        return torque
        

    def calculate_internal_loads(self):
        net_forces=self.external_loads-self.masses*(CONSTANTS.G0+self.accelerations)
        self.internal_shear_forces = np.cumsum(net_forces) #positive downwards
        
        cum_M=np.cumsum(self.external_moments)
        cum_F=np.cumsum(net_forces)
        cum_xF=np.cumsum(self.nodes*net_forces)

        self.internal_bending_moments=cum_M+self.nodes*cum_F-cum_xF
        
        self.internal_torques = np.zeros_like(self.nodes)
        self.internal_torques[np.argmin(np.abs(self.nodes - self.main_wing_x_m)):-1] += self.empennage_torque
        

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
        tau_shear = np.abs(self.internal_shear_forces * Q / (I * thicknesses_m))+np.abs(self.internal_torques/thicknesses_m/2/enclosed_area)
        sigma_bending = np.abs(self.internal_bending_moments*self.fuselage_diameter_m/(2*I))
        sigma_buckling = np.abs(self.calculate_buckling_stress(thicknesses_m))

        maximum_allowed_normal_stress = np.minimum(0.7*self.material.yield_strength, sigma_buckling)
        maximum_allowed_shear_stress = 0.5*self.material.yield_strength #Tresca
        bending_util = sigma_bending / maximum_allowed_normal_stress
        shear_util = tau_shear / maximum_allowed_shear_stress

        return bending_util, shear_util


    def evaluate_thickness(self,
                           maximum_allowed_thickness_mm: float,
                           thickness_step_mm: float):
        self.thicknesses_m = np.ones_like(self.nodes)*self.minimum_thickness_mm/1000  
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


    def plot_applied_loads(self):
        plt.figure(figsize=(10, 4))
        plt.plot(self.nodes, self.external_loads)
        plt.title('Applied external loads on fuselage')
        plt.xlabel('Position along Fuselage (m)')
        plt.ylabel('Load (N)')
        plt.grid()
        plt.legend()
        plt.show()


    def plot_applied_moments(self):
        plt.figure(figsize=(10, 4))
        plt.plot(self.nodes, self.external_moments)
        plt.title('Applied external moments on fuselage')
        plt.xlabel('Position along Fuselage (m)')
        plt.ylabel('Moment (Nm)')
        plt.grid()
        plt.legend()
        plt.show()


    def plot_shear_and_moment_diagrams(self):
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8))
        
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

        ax3.plot(self.nodes, self.internal_torques, label='Torque (Nm)', color='green')
        ax3.set_title('Torque Diagram')
        ax3.set_xlabel('Position along Fuselage (m)')
        ax3.set_ylabel('Torque (Nm)')
        ax3.grid()
        ax3.legend()
        
        #plt.suptitle('suptitle')
        plt.tight_layout()
        plt.savefig('internal_loads_'+self.condition+'.png')
        plt.show()
        

    def plot_required_thickness(self):
        plt.figure(figsize=(10, 4))
        plt.plot(self.nodes, self.thicknesses_m*1000)
        plt.xlabel("Position along fuselage [m]")
        plt.ylabel("Required skin thickness [mm]")
        #plt.title('title')
        plt.grid()
        plt.savefig('thickness_'+self.condition+'.png')
        plt.show()
        
        


if __name__=='__main__': 
        material = Material(density=1600,
                            elastic_modulus=50e9,
                            shear_modulus=5e9,
                            poisson_ratio=0.3,
                            yield_strength=600e6,
                            fracture_strength=600e6
                            )
        
        planform_wing=Planform(
            aspect_ratio=27.0,
            span=2.67,
            sweep_quarter_deg=15.0,
            taper=0.5,
            thickness_to_chord=0.12,
            cm_quarter_chord=1.0,
            wetted_surface_ratio=1.0,
            interference_factor=1.0,
            clmax=1.5,
            flap=False,
        )

        planform_canard=Planform(
            aspect_ratio=6.0,
            span=0.6,
            sweep_quarter_deg=10.0,
            taper=0.5,
            thickness_to_chord=0.12,
            cm_quarter_chord=1.0,
            wetted_surface_ratio=1.0,
            interference_factor=1.0,
            clmax=1.5,
            flap=False,
        )

        wing_model_flight= WingModel(
                 wing_skin_thickness_m =0.001,
                 number_of_nodes=100,
                 material_1 = material,
                 planform = planform_wing,
                 load_factor=9.0,
                 local_fuselage_diameter=0.30,
                 load_factor_maneuver=1.0
                 )
        
        canard_model_flight= WingModel(
                 wing_skin_thickness_m =0.001,
                 number_of_nodes=100,
                 material_1 = material,
                 planform = planform_canard,
                 load_factor=9.0,
                 local_fuselage_diameter=0.1,
                 load_factor_maneuver=1.0
                 )
        
        fuselage_model_flight= FuselageModel(
                 minimum_fuselage_thickness_mm=0.1,
                 material=material,
                 number_of_nodes=1000,
                 canard_lift_fraction=0.2, 
                 wing_model=wing_model_flight,
                 canard_model=canard_model_flight            
                 )
        
        wing_model_landing= WingModel(
                 wing_skin_thickness_m =0.001,
                 number_of_nodes=100,
                 material_1 = material,
                 planform = planform_wing,
                 load_factor=4.0,
                 local_fuselage_diameter=0.30,
                 load_factor_maneuver=1.0
                 )
        
        canard_model_landing= WingModel(
                 wing_skin_thickness_m =0.001,
                 number_of_nodes=100,
                 material_1 = material,
                 planform = planform_canard,
                 load_factor=4.0,
                 local_fuselage_diameter=0.1,
                 load_factor_maneuver=1.0
                 )
        
        fuselage_model_landing= FuselageModel(
                 minimum_fuselage_thickness_mm=0.1,
                 material=material,
                 number_of_nodes=1000,
                 canard_lift_fraction=0.2, 
                 wing_model=wing_model_landing,
                 canard_model=canard_model_landing            
                 )
        
        from pathlib import Path
        csv_path = Path(__file__).parent / "onshape_mass_distribution.csv"
        fuselage_model_flight.load_components_from_csv(str(csv_path))
        fuselage_model_flight.plot_mass_distribution()
        fuselage_model_flight.calculate_loads_flight(9.0)
        fuselage_model_flight.plot_applied_loads()
        fuselage_model_flight.plot_applied_moments()
        fuselage_model_flight.plot_shear_and_moment_diagrams()
        fuselage_model_flight.evaluate_thickness(maximum_allowed_thickness_mm=1.0,
                                          thickness_step_mm=0.01)        
        fuselage_model_flight.plot_required_thickness()

        fuselage_model_landing.load_components_from_csv(str(csv_path))
        fuselage_model_landing.plot_mass_distribution()
        fuselage_model_landing.calculate_loads_landing(landing_deceleration_in_terms_of_g=4.0)
        fuselage_model_landing.plot_applied_loads()
        fuselage_model_landing.plot_applied_moments()
        fuselage_model_landing.plot_shear_and_moment_diagrams()
        fuselage_model_landing.evaluate_thickness(maximum_allowed_thickness_mm=1.0,
                                          thickness_step_mm=0.01)        
        fuselage_model_landing.plot_required_thickness()