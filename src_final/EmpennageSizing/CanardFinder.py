import numpy as np
from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed
from EmpennageSizing.EmpennageFinder import EmpennageFinder

class CanardFinder(EmpennageFinder):
    def __init__(self, fixed, AR_c:float=3., taper_c:float=.7, taper_v:float=.9, SM=0.05):
        super().__init__(fixed)
        self.AR_c = AR_c
        self.taper_c = taper_c
        self.taper_v = taper_v
        self.SM = SM


    def find_planforms(self, main_wing:Planform, initial:float=.1, maxiter:int=50, tolerance:float=1e-4) -> list[Planform]:
        x_ac_mac = self._x_ac(main_wing, self.fixed.x_LE_wing)
        ac_term = x_ac_mac  - main_wing.cm_quarter_chord / main_wing.positive_C_L_max
        Sh_S = initial
        
        for i in range(maxiter):
            canard, vertical_tail = self._canard_rudder(main_wing, Sh_S)
            x_LE_vertical_tail = self.fixed.x_LE_tail - vertical_tail.span / 2 * np.tan(vertical_tail.sweep_LE_rad)
            
            l_c_mac = x_ac_mac - self._x_ac(canard, self.fixed.x_LE_canard)
            CL_c = canard.positive_C_L_max

            x_cg_mac_min = self._x_cg([main_wing, canard, vertical_tail], [self.fixed.x_LE_tail, self.fixed.x_LE_tail, x_LE_vertical_tail])
            Sh_S_new = (x_cg_mac_min - ac_term) / (CL_c * l_c_mac / main_wing.positive_C_L_max)

            diff = abs(Sh_S_new - Sh_S) / Sh_S_new
            if  diff < tolerance:
                Sh_S = (Sh_S + Sh_S_new) / 2
                break
            Sh_S = Sh_S_new

            if i == maxiter - 1:
                Warning(f"For planform of AR:{main_wing.aspect_ratio}, and sweep: {np.rad2deg(main_wing.sweep_quarter_rad)} deg, the tail sizing converged within {diff}, above tolerance: {tolerance}.")

        canard, vertical_tail = self._canard_rudder(main_wing, Sh_S)
        return [canard, vertical_tail]


    def _canard_rudder(self, main_wing:Planform, Sh_S:float)->tuple[Planform, Planform]:
        canard = Planform(
                aspect_ratio=self.AR_c, 
                span=np.sqrt(Sh_S * main_wing.wing_area * self.AR_c),
                taper=self.taper_c,
                sweep_quarter_deg=np.rad2deg(main_wing.sweep_quarter_rad),
                thickness_to_chord=0.12,
                cm_quarter_chord=0.,
                wetted_surface_ratio=1.05,
                interference_factor=1.04,
                clmax=.35 * self.AR_c**(1/3) / .9 / np.cos(main_wing.sweep_quarter_rad),
                flap=False
            )
        canard.x_cg_cache = canard.x_MAC + canard.MAC / 3 #TODO: rough assumption revise
        canard.mass_cache = 0.5 #TODO actually conduct the structural analysishere

        AR_v = 2 * canard.span / (1 + 1/self.taper_v) / canard.c_root #NOTE: to fit the horizontal tail
        vertical_tail = Planform(
            aspect_ratio=AR_v, 
            span=canard.span,
            taper=self.taper_v,
            sweep_quarter_deg=np.rad2deg(main_wing.sweep_quarter_rad),
            thickness_to_chord=0.12,
            cm_quarter_chord=0.,
            wetted_surface_ratio=1.05 / 2, #NOTE: to account for half the drag
            interference_factor=1.04,
            clmax=0.,
            flap=False
        )
        vertical_tail.x_cg_cache = vertical_tail.x_MAC + vertical_tail.MAC / 3 #TODO: rough assumption revise
        vertical_tail.mass_cache = 0.3 #TODO actually conduct the structural analysishere

        return canard, vertical_tail