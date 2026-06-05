import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed


class EmpennageFinder():
    def __init__(self, fixed:Fixed):
        self.fixed = fixed

  
    @staticmethod
    def _x_ac(self, main_wing:Planform, x_LE:float, tolerance:float=1e-4):
        return (x_LE + main_wing.x_MAC + main_wing.MAC / 4) / main_wing.MAC
    

    def _x_cg(self, planforms:list[Planform]):
        x_cgs = np.array(len(planforms) + 1)
        ms = np.array(len(planforms) + 1)

        for i, planform in enumerate(planforms):
            if (planform.mass_cache is None) or (planform.x_cg_cache is None):
                #TODO implement structural analysis
                raise NotImplementedError("Planform Structural Analysis not implementedyet")
            else:
                x_cgs[i] = planform.x_cg_cache
                ms[i] = planform.mass_cache

        x_cgs[-1] = self.fixed.x_cg_min # as we are sizing for controllability
        ms[-1] = self.fixed.mass #conservative, as it assumes maximum mass at foremost C.G.

        return (np.sum(x_cgs * ms) / ms.sum()) / planforms[0].MAC


    def find_planforms(self, main_wing:Planform, initial:float=.1, maxiter:int=50) -> list[Planform]:
        '''Return the tail and/or canard planforms for a provided main wing'''
        raise NotImplementedError