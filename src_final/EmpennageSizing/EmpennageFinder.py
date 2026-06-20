import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed

from structural_analysis.iterative_planform_sizing import Material


class EmpennageFinder():
    def __init__(self, fixed, thicknesses, material, core_density, safety_factor, number_of_sections=30):
        self.fixed = fixed
        self.thicknesses = thicknesses
        self.material = material
        self.core_density = core_density
        self.safety_factor = safety_factor
        self.number_of_sections = number_of_sections

  
    def _x_ac(self, planform:Planform, x_LE:float, MAC:float, number_of_sections:int=20):
        local_ac = planform.aerodynamic_center(number_of_sections=number_of_sections)
        return (x_LE + local_ac - self.fixed.x_LE_wing) / MAC
    

    def _x_cg(self, planforms:list[Planform], x_LEs:list[float], fore:bool=True) -> float:
        #NOTE: can be called only after masses are assigned to planforms
        x_cgs = np.zeros(len(planforms) + 1)
        ms = np.zeros(len(planforms) + 1)

        for i, planform in enumerate(planforms):
            x_cgs[i] = planform.x_cg_cache + x_LEs[i]
            ms[i] = planform.mass_cache

        x_cgs[-1] = self.fixed.x_cg_min if fore else self.fixed.x_cg_max
        ms[-1] = self.fixed.mass #conservative, as it assumes maximum mass at foremost C.G.

        return (np.sum(x_cgs * ms) / ms.sum() - self.fixed.x_LE_wing) / planforms[0].MAC


    def find_planforms(self, main_wing:Planform, material:Material, thicknesses_allowable:list[float], fuselage_diameter:float, initial:float=.1, maxiter:int=50) -> list[Planform]:
        '''Return the tail and/or canard planforms for a provided main wing'''
        raise NotImplementedError