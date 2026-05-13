import sys
import os
import aerosandbox.numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from global_parameters import CONSTANTS
from objects.lifting_surface_planform import LiftingSurfacePlanform

class TailVolume:
    def __init__(self, 
                 wing_planform: LiftingSurfacePlanform,
                 required_cg_excursion_MAC: float,
                 ac_position_mac: float,
                 Cmac: float,
                 C_L_H: float,
                 C_L_A_minus_H: float,
                 C_L_alpha_H: float,
                 wing_downwash_gradient: float,
                 C_L_alpha_A_minus_H: float,
                 V_H_over_V_2: float=1.0,

                 ):
        self.wing_planform=wing_planform
        self.required_cg_excursion_MAC=required_cg_excursion_MAC
        self.ac_position_mac=ac_position_mac
        self.Cmac=Cmac
        self.C_L_H=C_L_H
        self.C_L_A_minus_H=C_L_A_minus_H
        self.C_L_alpha_H=C_L_alpha_H
        self.wing_downwash_gradient=wing_downwash_gradient
        self.C_L_alpha_A_minus_H=C_L_alpha_A_minus_H
        self.V_H_over_V_2=V_H_over_V_2

    def find_required_tail_volume(self):
        first_upper=self.required_cg_excursion_MAC-self.Cmac/self.C_L_A_minus_H
        first_lower = self.C_L_alpha_H/self.C_L_alpha_A_minus_H*(1-self.wing_downwash_gradient)-self.C_L_H/self.C_L_A_minus_H
        self.required_tail_volume=first_upper/first_lower*self.wing_planform.wing_area*self.wing_planform.MAC/self.V_H_over_V_2
        return self.required_tail_volume
       
    def find_required_cg_position_MAC(self):
        self.required_CG_position_MAC = self.ac_position_mac+self.C_L_alpha_H/self.C_L_alpha_A_minus_H*\
            (1-self.wing_downwash_gradient)*self.required_tail_volume/\
                (self.wing_planform.wing_area*self.wing_planform.MAC)*self.V_H_over_V_2
        return self.required_CG_position_MAC