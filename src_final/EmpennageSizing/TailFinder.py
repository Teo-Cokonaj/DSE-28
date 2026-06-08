import sys
import os
from numba import njit
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed
from EmpennageSizing.EmpennageFinder import EmpennageFinder

class TailFinder(EmpennageFinder):
    def __init__(self, fixed, AR_h:float=3., taper_h:float=1., taper_v:float=1., SM=0.05, Sv_S=.15):
        super().__init__(fixed)
        self.AR_h = AR_h
        self.taper_h = taper_h
        self.taper_v = taper_v
        self.SM = SM
        self.Sv_S = Sv_S


    def find_planforms(self, main_wing:Planform, initial:float=.1, maxiter:int=50, tolerance:float=1e-4) -> list[Planform]:
        x_ac_mac = self._x_ac(main_wing, self.fixed.x_LE_wing)
        ac_term = x_ac_mac  - main_wing.cm_quarter_chord / main_wing.positive_C_L_max
        Sh_S = initial
        
        for i in range(maxiter):
            horizontal_tail, vertical_tail = self._t_tail(main_wing, Sh_S)
            x_LE_vertical_tail = self.fixed.x_LE_tail - vertical_tail.span / 2 * np.tan(vertical_tail.sweep_LE_rad)
            
            l_h_mac = self._x_ac(horizontal_tail, self.fixed.x_LE_tail) - x_ac_mac
            CL_h = horizontal_tail.positive_C_L_max

            x_cg_mac_min = self._x_cg([main_wing, horizontal_tail, vertical_tail], [self.fixed.x_LE_tail, self.fixed.x_LE_tail, x_LE_vertical_tail])
            Sh_S_new_ctrl = abs((x_cg_mac_min - ac_term) / (CL_h * l_h_mac / main_wing.positive_C_L_max))

            #if main_wing.sweep_quarter_rad > 0:
            downwash = self.downwash_gradient(main_wing, l_h_mac * main_wing.MAC, vertical_tail)
            x_cg_mac_max = self._x_cg([main_wing, horizontal_tail, vertical_tail], [self.fixed.x_LE_tail, self.fixed.x_LE_tail, x_LE_vertical_tail], False)
            Sh_S_new_stab = (x_cg_mac_max - x_ac_mac - self.SM) / ((1-downwash) * horizontal_tail.CL_alpha * l_h_mac / main_wing.CL_alpha)
            #else:
                #Sh_S_new_stab = 0
            
            Sh_S_new = max(Sh_S_new_ctrl, Sh_S_new_stab)
            assert Sh_S_new > 0

            diff = abs(Sh_S_new - Sh_S) / Sh_S_new
            if  diff < tolerance:
                Sh_S = (Sh_S + Sh_S_new) / 2
                break
            Sh_S = Sh_S_new

            if i == maxiter - 1:
                Warning(f"For planform of AR:{main_wing.aspect_ratio}, and sweep: {np.rad2deg(main_wing.sweep_quarter_rad)} deg, the tail sizing converged within {diff}, above tolerance: {tolerance}.")

        horizontal_tail, vertical_tail = self._t_tail(main_wing, Sh_S)
        return [horizontal_tail, vertical_tail]


    def _t_tail(self, main_wing:Planform, Sh_S:float)->tuple[Planform, Planform]:
        horizontal_tail = Planform(
                aspect_ratio=self.AR_h, 
                span=np.sqrt(Sh_S * main_wing.wing_area * self.AR_h),
                taper=self.taper_h,
                sweep_quarter_deg=abs(np.rad2deg(main_wing.sweep_quarter_rad)),
                thickness_to_chord=0.12,
                cm_quarter_chord=0.,
                wetted_surface_ratio=1.05,
                interference_factor=1.04,
                clmax=.35 * self.AR_h**(1/3) / .9 / np.cos(main_wing.sweep_quarter_rad),
                flap=False
            )
        horizontal_tail.x_cg_cache = horizontal_tail.x_MAC + horizontal_tail.MAC / 3 #TODO: rough assumption revise
        horizontal_tail.mass_cache = 0.5 #TODO actually conduct the structural analysishere

        vertical_surface = 2 * self.Sv_S * main_wing.wing_area #NOTE: 2 as rudder is only 1 sided
        vertical_span = 2 * vertical_surface / (1 + 1/self.taper_v) / horizontal_tail.c_tip #NOTE: to fit the horizontal tail
        vertical_tail = Planform(
            aspect_ratio=vertical_span**2 / vertical_surface, 
            span=horizontal_tail.span,
            taper=self.taper_v,
            sweep_quarter_deg=abs(np.rad2deg(main_wing.sweep_quarter_rad)),
            thickness_to_chord=0.12,
            cm_quarter_chord=0.,
            wetted_surface_ratio=1.05 / 2, #NOTE: to account for half the drag
            interference_factor=1.04,
            clmax=0.,
            flap=False
        )
        vertical_tail.x_cg_cache = vertical_tail.x_MAC + vertical_tail.MAC / 3 #TODO: rough assumption revise
        vertical_tail.mass_cache = 0.3 #TODO actually conduct the structural analysishere

        return horizontal_tail, vertical_tail
    

    @staticmethod
    def downwash_gradient(
    main_wing:Planform,
    l_h:float,
    vertical_tail:Planform
    ):
        """
        Compute wing downwash gradient dε/dα using the Slingerland correlation.

        Parameters
        ----------
        r : float
            Dimensionless horizontal tail distance parameter.
        m_tv : float
            Dimensionless vertical tail position parameter.
        CLa_w : float
            Wing lift-curve slope [1/rad].
        A : float
            Wing aspect ratio.
        sweep_quarter_chord_rad : float, optional
            Wing quarter-chord sweep angle [rad].
            Default = 0 (unswept wing).

        Returns
        -------
        float
            Downwash gradient dε/dα.
        """

        lam = main_wing.sweep_quarter_rad
        r = 2 * l_h / main_wing.span
        m_tv = vertical_tail.span / main_wing.span

        # Sweep correction factors
        K_eps = (
            (0.1124 + 0.1265 * lam + 0.1766 * lam**2) / r**2
            + 0.1024 / r
            + 2.0
        )

        K_eps_0 = (
            0.1124 / r**2
            + 0.1024 / r
            + 2.0
        )

        term1 = (
            r / (r**2 + m_tv**2)
            * 0.4876 / np.sqrt(r**2 + 0.6319 + m_tv**2)
        )

        term2 = (
            1.0
            + (
                r**2
                / (r**2 + 0.7915 + 5.0734 * m_tv**2)
            )
        )**0.3113

        term3 = (
            1.0
            - np.sqrt(
                m_tv**2 / (1.0 + m_tv**2)
            )
        )

        downwash = (
            (K_eps / K_eps_0)
            * (term1 + term2 * term3)
            * (main_wing.CL_alpha / (np.pi * main_wing.aspect_ratio))
        )

        return downwash