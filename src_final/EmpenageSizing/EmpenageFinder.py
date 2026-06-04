import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed
from abc import ABC, abstractmethod

# ---------------------------------------------------------------------------
# Statistical assumptions
# ---------------------------------------------------------------------------
A_H     = 5.0    # horizontal tail aspect ratio
TAPER_H = 0.40
SWEEP_H = 20.0   # quarter-chord sweep [deg]
T_C_H   = 0.12

A_C     = 3.0    # canard aspect ratio
TAPER_C = 0.4
SWEEP_C = 15.0   # quarter-chord sweep [deg]
T_C_C   = 0.12

SM_STABLE   = 0.05   # static margin for stable design   (NP = CG + 5% MAC)
SM_UNSTABLE = 0.01   # boundary for just-unstable design (NP = CG)

V_C = 0.10   # canard volume coefficient — used in 3-surface to pin canard size

# Statistical empenage weight model
RHO_SURF_H = 14.0   # kg/m²  — horizontal tail surface density (aluminium structure)
RHO_SURF_C = 12.0   # kg/m²  — canard surface density (lighter: thinner, smaller)
X_CG_FRAC  = 0.5   # structural CG at 40 % MAC from LE (statistical)

N = 50       # spanwise sections for aerodynamic centre integration

# Return type alias: (tail: Planform | None, canard: Planform | None)
EmpenageResult = tuple


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _sweep_half(sweep_quarter_rad: float, c_root: float, span: float, taper: float) -> float:
    """Quarter-chord sweep → half-chord sweep [rad]."""
    return np.arctan(np.tan(sweep_quarter_rad) - c_root / span * 0.25 * (1 - taper))


def _CL_alpha(planform: Planform) -> float:
    """3-D lift-curve slope via Helmbold–DATCOM [1/rad]."""
    a0  = planform.airfoil_lift_slope
    AR  = planform.aspect_ratio
    kap = a0 / (2 * np.pi)
    Lam = _sweep_half(planform.sweep_quarter_rad, planform.c_root, planform.span, planform.taper)
    return a0 * AR / (2 + np.sqrt(4 + (AR / kap) ** 2 * (1 + np.tan(Lam) ** 2)))


def _downwash(CL_alpha_w: float, AR_w: float) -> float:
    """Simplified downwash gradient dε/dα."""
    return 2 * CL_alpha_w / (np.pi * AR_w)


# def _is_set(x) -> bool:
#     #TODO: remove
#     """True when x is a real (non-None, non-NaN) position."""
#     return x is not None and not np.isnan(float(x))


def _make_planform(S: float, AR: float, taper: float, sweep_deg: float, t_c: float) -> Planform:
    """Build a symmetric Planform from area + statistical geometry."""
    return Planform(
        aspect_ratio         = AR,
        span                 = np.sqrt(S * AR),
        sweep_quarter_deg    = sweep_deg,
        taper                = taper,
        thickness_to_chord   = t_c,
        cm_quarter_chord     = 0.0,
        wetted_surface_ratio = 1.05,
        interference_factor  = 1.05,
        clmax                = -.35*AR**(1/3), #CL_h from ADSEE
        flap                 = False,
        airfoil_lift_slope   = 2 * np.pi,
        cl0                  = 0.0,
    )


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class EmpenageFinder(ABC):
    """
    Abstract base for empenage sizing.

    The scissor-plot criterion is used throughout:
        x_np = x_AC_w + (CL_surf_eff / CL_w) * (S_surf/S_w) * l_surf

    stable=True  → SM = SM_STABLE  (5%): S_surf/S_w sized for x_np = x_cg + 0.05*MAC
    stable=False → SM = SM_UNSTABLE (0%): S_surf/S_w sized for x_np = x_cg  (just-unstable boundary)

    Aerodynamic centres of tail and canard are estimated statistically as
        x_AC_surf = x_LE_surf + surf.aerodynamic_center(N)   (≈ x_LE + 0.25*MAC_surf)

    Routing (via find_empenage):
        x_LE_tail set, x_LE_canard NaN → TailFinder
        x_LE_canard set, x_LE_tail NaN → CanardFinder
        both set                        → ThreeSurfaceFinder

    Returns: (tail: Planform | None, canard: Planform | None)
    """

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    @staticmethod
    def find_empenage(planform: Planform, fixed: Fixed, planform_type:str, stable: bool) -> EmpenageResult:
        #TODO: change to match the string planform types used elsewhere

        if planform_type=="three_surface":
            finder = ThreeSurfaceFinder()
        elif planform_type=="canard":
            finder = CanardFinder()
        elif planform_type=="tail":
            finder = TailFinder()
        else:
            raise NotImplementedError("This planform type not implemented yet")

        return finder.size_empenage(planform, fixed, stable)

    @abstractmethod
    def size_empenage(self, planform: Planform, fixed: Fixed, stable: bool) -> EmpenageResult:
        pass

    # ------------------------------------------------------------------
    # Shared aerodynamic utilities
    # ------------------------------------------------------------------

    def _wing_aero(self, planform: Planform, fixed: Fixed):
        """Return (x_AC_wing [absolute], CL_alpha_wing)."""
        return fixed.x_LE_wing + planform.aerodynamic_center(N), _CL_alpha(planform)

    @staticmethod
    def diagnose(planform: Planform, fixed: Fixed) -> None:
        """Print key geometry and stability values to help debug sizing issues."""
        x_AC_w = fixed.x_LE_wing + planform.aerodynamic_center(N)
        CL_w   = _CL_alpha(planform)
        deps   = _downwash(CL_w, planform.aspect_ratio)
        print(f"--- Empennage sizing diagnostics ---")
        print(f"  Wing:   S={planform.wing_area:.4f} m²  MAC={planform.MAC:.4f} m  "
              f"AR={planform.aspect_ratio:.1f}  CL_alpha={CL_w:.3f} /rad")
        print(f"  Wing AC: x_AC_w = {x_AC_w:.4f} m  (x_LE_wing={fixed.x_LE_wing:.3f} + {x_AC_w-fixed.x_LE_wing:.4f})")
        print(f"  CG (excl. empenage): x_cg = {fixed.x_cg_max:.4f} m  mass = {fixed.mass:.2f} kg")
        print(f"  Downwash: deps/dalpha = {deps:.4f}")
        if _is_set(getattr(fixed, 'x_LE_tail', None)):
            l_h = fixed.x_LE_tail - x_AC_w
            print(f"  Tail LE: {fixed.x_LE_tail:.3f} m  →  approx arm l_h ≈ {l_h:.3f} m")
            for SM_label, SM in [("stable (5%)", SM_STABLE), ("neutral (0%)", SM_UNSTABLE)]:
                x_np_req = fixed.x_cg_max + SM * planform.MAC
                print(f"  Required NP [{SM_label}]: {x_np_req:.4f} m  "
                      f"({'OK' if x_AC_w < x_np_req < fixed.x_LE_tail else 'PROBLEM'})")
        if _is_set(getattr(fixed, 'x_LE_canard', None)):
            l_c = x_AC_w - fixed.x_LE_canard
            print(f"  Canard LE: {fixed.x_LE_canard:.3f} m  →  approx arm l_c ≈ {l_c:.3f} m")
            for SM_label, SM in [("stable (5%)", SM_STABLE), ("neutral (0%)", SM_UNSTABLE)]:
                x_np_req = fixed.x_cg_max + SM * planform.MAC
                print(f"  Required NP [{SM_label}]: {x_np_req:.4f} m  "
                      f"({'OK' if fixed.x_LE_canard < x_np_req < x_AC_w else 'PROBLEM — NP must be between canard and wing AC'})")
        print(f"------------------------------------")

    def _cg_updated(self, fixed: Fixed,
                    m_tail: float = 0.0, x_cg_tail: float = 0.0,
                    m_canard: float = 0.0, x_cg_canard: float = 0.0) -> float:
        #TODO: Add main wing
        """
        Aircraft CG updated to include empenage surface masses.

        fixed.mass / fixed.x_cg_max represent the aircraft WITHOUT the empenage
        surfaces being sized here (fuselage, wing, engines, payload, etc.).
        Surface masses are estimated as RHO_SURF * S, structural CG at X_CG_FRAC * MAC.
        """
        m_total = fixed.mass + m_tail + m_canard
        return (fixed.mass * fixed.x_cg_max
                + m_tail   * x_cg_tail
                + m_canard * x_cg_canard) / m_total

    # ------------------------------------------------------------------
    # Scissor-plot solvers — shared by all subclasses
    # ------------------------------------------------------------------

    def _solve_tail_ratio(self, SM: float,
                          planform: Planform, fixed: Fixed) -> tuple:
        """
        Solve for S_h/S_w from the scissor-plot stability criterion.

        Stability equation (downwash corrected):
            x_np = x_AC_w + (CL_h_eff / CL_w) * (S_h/S_w) * l_h

        Rearranged:
            S_h/S_w = (x_np_req - x_AC_w) / ((CL_h_eff / CL_w) * l_h)

        l_h = x_AC_h - x_AC_w, where x_AC_h = x_LE_tail + tail.aerodynamic_center(N)
        is a statistical estimate (≈ x_LE_tail + 0.25*MAC_h).
        Iterated because MAC_h depends on S_h.

        Returns:
            (S_h/S_w, tail_Planform)
        """
        x_AC_w, CL_w = self._wing_aero(planform, fixed)
        deps          = _downwash(CL_w, planform.aspect_ratio)

        ratio = 0.10    # initial S_h/S_w guess
        for _ in range(20):
            tail       = _make_planform(ratio * planform.wing_area, A_H, TAPER_H, SWEEP_H, T_C_H)
            x_AC_h     = fixed.x_LE_tail + tail.aerodynamic_center(N)
            CL_h       = _CL_alpha(tail) * (1 - deps) #TODO replace with the actual Cl_h

            # Update CG with current tail mass estimate, then set required NP
            m_tail     = RHO_SURF_H * tail.wing_area
            x_cg_tail  = fixed.x_LE_tail + X_CG_FRAC * tail.MAC
            x_np_req   = self._cg_updated(fixed, m_tail=m_tail, x_cg_tail=x_cg_tail) + SM * planform.MAC

            l_h = x_AC_h - x_AC_w
            if l_h <= 0:
                raise ValueError(
                    f"Tail AC ({x_AC_h:.2f} m) not aft of wing AC ({x_AC_w:.2f} m)."
                )
            if x_np_req > x_AC_h:
                raise ValueError(
                    f"Required NP ({x_np_req:.3f} m) is aft of tail AC ({x_AC_h:.3f} m). "
                    f"No finite tail area can achieve this — move the tail further aft "
                    f"or move the CG forward (currently x_cg_updated={x_np_req - SM * planform.MAC:.3f} m)."
                )

            if x_np_req <= x_AC_w:
                raise ValueError(
                    f"Required NP ({x_np_req:.3f} m) is forward of or at the wing AC "
                    f"({x_AC_w:.3f} m). The wing alone already exceeds the required static "
                    f"margin — no aft tail is needed for stability. "
                    f"CG position: {x_np_req - SM * planform.MAC:.3f} m."
                )

            ratio_new = (x_np_req - x_AC_w) / ((CL_h / CL_w) * l_h)

            if abs(ratio_new - ratio) < 1e-6:
                ratio = ratio_new
                break
            ratio = ratio_new

        return ratio, _make_planform(ratio * planform.wing_area, A_H, TAPER_H, SWEEP_H, T_C_H)

    def _solve_canard_ratio(self, SM: float,
                            planform: Planform, fixed: Fixed) -> tuple:
        """
        Solve for S_c/S_w from the scissor-plot stability criterion.

        Stability equation:
            x_np = x_AC_w + (CL_c / CL_w) * (S_c/S_w) * (x_AC_c - x_AC_w)

        (x_AC_c - x_AC_w) < 0  → larger canard shifts NP forward → less stable.
        Rearranged (both factors in numerator/denominator are positive):
            S_c/S_w = CL_w*(x_AC_w - x_np_req) / (CL_c*(x_np_req - x_AC_c))

        x_AC_c = x_LE_canard + canard.aerodynamic_center(N)  (≈ x_LE + 0.25*MAC_c).
        Iterated because MAC_c depends on S_c. Damped to prevent divergence.

        Returns:
            (S_c/S_w, canard_Planform)
        """
        x_AC_w, CL_w = self._wing_aero(planform, fixed)

        ratio = 0.05    # initial S_c/S_w guess
        for _ in range(30):
            canard     = _make_planform(ratio * planform.wing_area, A_C, TAPER_C, SWEEP_C, T_C_C)
            x_AC_c     = fixed.x_LE_canard + canard.aerodynamic_center(N)
            CL_c       = _CL_alpha(canard)

            # Update CG with current canard mass estimate, then set required NP
            m_canard    = RHO_SURF_C * canard.wing_area
            x_cg_canard = fixed.x_LE_canard + X_CG_FRAC * canard.MAC
            x_np_req    = self._cg_updated(fixed, m_canard=m_canard, x_cg_canard=x_cg_canard) + SM * planform.MAC

            if x_np_req >= x_AC_w:
                raise ValueError(
                    f"Required NP ({x_np_req:.2f} m) must be forward of wing AC ({x_AC_w:.2f} m). "
                    "For a canard config the CG must be forward of the wing AC."
                )

            if x_AC_c >= x_np_req:
                raise ValueError(
                    f"Canard AC ({x_AC_c:.2f} m) reached required NP ({x_np_req:.2f} m). "
                    "Check CG and canard LE position."
                )

            ratio_new = CL_w * (x_AC_w - x_np_req) / (CL_c * (x_np_req - x_AC_c))

            if abs(ratio_new - ratio) < 1e-6:
                ratio = ratio_new
                break
            ratio = 0.5 * ratio + 0.5 * ratio_new   # damp

        return ratio, _make_planform(ratio * planform.wing_area, A_C, TAPER_C, SWEEP_C, T_C_C)

    def _solve_tail_ratio_3surface(self, SM: float,
                                   ratio_c: float,
                                   x_AC_c: float, CL_alpha_c: float,
                                   m_canard: float, x_cg_canard: float,
                                   planform: Planform, fixed: Fixed) -> tuple:
        """
        Solve for S_h/S_w in a 3-surface aircraft, with a fixed canard ratio.

        3-surface NP equation:
            x_np = x_AC_w + (1/CL_w) * [
                CL_c * (S_c/S_w) * (x_AC_c - x_AC_w)
              + CL_h_eff * (S_h/S_w) * (x_AC_h - x_AC_w)
            ]

        Solved for S_h/S_w:
            S_h/S_w = [CL_w*(x_np_req - x_AC_w) - CL_c*ratio_c*(x_AC_c - x_AC_w)]
                      / [CL_h_eff * (x_AC_h - x_AC_w)]

        The canard term (x_AC_c - x_AC_w) < 0 → subtracting it adds to the numerator,
        so the canard requires a LARGER tail than in a tail-only design.

        Returns:
            (S_h/S_w, tail_Planform)
        """
        x_AC_w, CL_w = self._wing_aero(planform, fixed)
        deps          = _downwash(CL_w, planform.aspect_ratio)

        ratio_h = 0.10
        for _ in range(20):
            tail      = _make_planform(ratio_h * planform.wing_area, A_H, TAPER_H, SWEEP_H, T_C_H)
            x_AC_h    = fixed.x_LE_tail + tail.aerodynamic_center(N)
            CL_h      = _CL_alpha(tail) * (1 - deps)

            # Update CG with both canard and current tail mass, then set required NP
            m_tail    = RHO_SURF_H * tail.wing_area
            x_cg_tail = fixed.x_LE_tail + X_CG_FRAC * tail.MAC
            x_np_req  = self._cg_updated(fixed,
                                         m_tail=m_tail,     x_cg_tail=x_cg_tail,
                                         m_canard=m_canard, x_cg_canard=x_cg_canard
                                         ) + SM * planform.MAC

            l_h = x_AC_h - x_AC_w
            if l_h <= 0:
                raise ValueError(
                    f"Tail AC ({x_AC_h:.2f} m) not aft of wing AC ({x_AC_w:.2f} m)."
                )
            if x_np_req > x_AC_h:
                raise ValueError(
                    f"Required NP ({x_np_req:.3f} m) is aft of tail AC ({x_AC_h:.3f} m). "
                    f"No finite tail area can achieve this — move the tail further aft "
                    f"or move the CG forward (currently x_cg_updated={x_np_req - SM * planform.MAC:.3f} m)."
                )

            numerator   = (CL_w * (x_np_req - x_AC_w)
                           - CL_alpha_c * ratio_c * (x_AC_c - x_AC_w))
            if numerator < 0:
                raise ValueError(
                    f"3-surface: canard + wing already exceeds required SM — "
                    f"no aft tail needed. NP from canard+wing is already aft of "
                    f"x_np_req ({x_np_req:.3f} m). Reduce canard area or move CG aft."
                )
            ratio_h_new = numerator / (CL_h * l_h)

            if abs(ratio_h_new - ratio_h) < 1e-6:
                ratio_h = ratio_h_new
                break
            ratio_h = ratio_h_new

        return ratio_h, _make_planform(ratio_h * planform.wing_area, A_H, TAPER_H, SWEEP_H, T_C_H)


# ---------------------------------------------------------------------------
# Tail-only
# ---------------------------------------------------------------------------

class TailFinder(EmpenageFinder):
    """
    Aft horizontal tail only (no canard).

    stable=True  → tail sized for SM = 5%  (minimum stable tail area)
    stable=False → tail sized for SM = 0%  (minimum area for neutral stability;
                                             any smaller = just unstable)
    """

    def size_empenage(self, planform: Planform, fixed: Fixed, stable: bool) -> EmpenageResult:
        SM = SM_STABLE if stable else SM_UNSTABLE
        ratio, tail = self._solve_tail_ratio(SM, planform, fixed)
        return (tail, None)


# ---------------------------------------------------------------------------
# Canard-only
# ---------------------------------------------------------------------------

class CanardFinder(EmpenageFinder):
    """
    Forward canard only (no aft tail).

    stable=True  → canard sized for SM = 5%  (maximum stable canard area)
    stable=False → canard sized for SM = 0%  (maximum area at neutral stability;
                                               any larger = just unstable)
    """

    def size_empenage(self, planform: Planform, fixed: Fixed, stable: bool) -> EmpenageResult:
        SM = SM_STABLE if stable else SM_UNSTABLE
        ratio, canard = self._solve_canard_ratio(SM, planform, fixed)
        return (None, canard)


# ---------------------------------------------------------------------------
# Three-surface (tail + canard simultaneously)
# ---------------------------------------------------------------------------

class ThreeSurfaceFinder(EmpenageFinder):
    """
    Canard + wing + aft tail (three-surface aircraft).

    Canard area is fixed first using the volume coefficient V_C:
        S_c/S_w = V_C * MAC_w / l_c          (l_c = x_AC_w - x_LE_canard)

    Then the tail ratio S_h/S_w is solved from the 3-surface NP equation
    for the requested static margin:
        stable=True  → SM = 5%
        stable=False → SM = 0%  (just-unstable boundary)

    The canard shifts the NP forward, so the required tail is LARGER than in
    a tail-only design for the same CG and stability target.
    """

    def size_empenage(self, planform: Planform, fixed: Fixed, stable: bool) -> EmpenageResult:
        SM = SM_STABLE if stable else SM_UNSTABLE
        return self._size(SM, planform, fixed)

    def _size(self, SM: float, planform: Planform, fixed: Fixed) -> EmpenageResult:
        x_AC_w, CL_w = self._wing_aero(planform, fixed)

        # 1. Pin canard by volume coefficient
        l_c        = x_AC_w - fixed.x_LE_canard
        ratio_c    = V_C * planform.MAC / l_c                   # S_c/S_w
        canard     = _make_planform(ratio_c * planform.wing_area, A_C, TAPER_C, SWEEP_C, T_C_C)
        x_AC_c     = fixed.x_LE_canard + canard.aerodynamic_center(N)
        CL_c       = _CL_alpha(canard)
        m_canard    = RHO_SURF_C * canard.wing_area
        x_cg_canard = fixed.x_LE_canard + X_CG_FRAC * canard.MAC

        # 2. Solve tail ratio from 3-surface NP equation (canard mass/CG passed in)
        _, tail = self._solve_tail_ratio_3surface(
            SM, ratio_c, x_AC_c, CL_c, m_canard, x_cg_canard, planform, fixed
        )

        return (tail, canard)
