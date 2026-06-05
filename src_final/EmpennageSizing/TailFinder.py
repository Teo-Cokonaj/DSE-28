import sys
import os
from numba import njit
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed
from EmpennageSizing.EmpennageFinder import EmpennageFinder

class TailFinder(EmpennageFinder):
    def __init__(self, fixed, AR_h:float=3., taper_h:float=.7, taper_v:float=.9):
        super().__init__(fixed)
        self.AR_h = AR_h
        self.taper_h = taper_h
        self.taper_v = taper_v


    @njit
    def find_planforms(self, main_wing:Planform, initial:float=.1, maxiter:int=50, tolerance:float=1e-4) -> list[Planform]:
        x_ac_mac = self._x_ac(main_wing, self.fixed.x_LE_wing)
        ac_term = x_ac_mac  - main_wing.cm_quarter_chord / main_wing.positive_C_L_max
        Sh_S = 0.1
        
        for i in range(maxiter):
            horizontal_tail, vertical_tail = self._t_tail(main_wing, Sh_S)
            
            l_h_mac = self._x_ac(horizontal_tail, self.fixed.x_LE_tail) - x_ac_mac
            CL_h = - horizontal_tail.positive_C_L_max
            x_LE_vertical_tail = self.fixed.x_LE_tail - vertical_tail.span / 2 * np.tan(vertical_tail.sweep_LE_rad)
            x_cg_mac = self._x_cg([main_wing, horizontal_tail, vertical_tail])
            Sh_S_new = (x_cg_mac - ac_term) / (CL_h * l_h_mac / main_wing.positive_C_L_max)

            if abs(Sh_S_new - Sh_S) / Sh_S_new < tolerance:
                Sh_S = (Sh_S + Sh_S_new) / 2
                break
            Sh_S = Sh_S_new

        horizontal_tail, vertical_tail = self._t_tail(main_wing, Sh_S)
        return [horizontal_tail, vertical_tail]


    @njit
    def _t_tail(self, main_wing:Planform, Sh_S:float)->tuple[Planform, Planform]:
        horizontal_tail = Planform(
                aspect_ratio=self.AR_h, 
                span=np.sqrt(Sh_S * main_wing.wing_area * self.AR_h),
                taper=self.taper_h,
                sweep_quarter_deg=np.rad2deg(main_wing.sweep_quarter_rad),
                thickness_to_chord=0.12,
                cm_quarter_chord=0.,
                wetted_surface_ratio=1.05,
                interference_factor=1.04,
                clmax=-.35 * self.AR_h**(1/3) / .9 / np.cos(main_wing.sweep_quarter_rad),
                flap=False
            )
        AR_v = 2 * horizontal_tail.span / (1 + 1/self.taper_v) / horizontal_tail.c_root #NOTE: to fit the horizontal tail
        vertical_tail = Planform(
            aspect_ratio=AR_v, 
            span=horizontal_tail.span,
            sweep_quarter_deg=np.rad2deg(main_wing.sweep_quarter_rad),
            thickness_to_chord=0.12,
            cm_quarter_chord=0.,
            wetted_surface_ratio=1.05 / 2, #NOTE: to account for half the drag
            interference_factor=1.04,
            clmax=0.,
            flap=False
        )

        return horizontal_tail, vertical_tail