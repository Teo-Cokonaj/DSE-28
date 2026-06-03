import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed
from abc import ABC, abstractmethod

# --- Statistical empenage assumptions ---
A_H     = 4.5       # horizontal tail aspect ratio
TAPER_H = 0.40      # horizontal tail taper
SWEEP_H = 25.0      # horizontal tail quarter-chord sweep [deg]
T_C_H   = 0.12      # horizontal tail thickness-to-chord

A_C     = 3.0       # canard aspect ratio
TAPER_C = 0.35      # canard taper
SWEEP_C = 15.0      # canard quarter-chord sweep [deg]
T_C_C   = 0.10      # canard thickness-to-chord

SM   = 0.05         # required static margin [fraction of MAC]
V_H  = 0.35         # horizontal tail volume coefficient (unstable sizing)
V_C  = 0.10         # canard volume coefficient (3-surface / unstable sizing)

N = 50              # spanwise sections for AC integration

# Return type: (tail_planform | None, canard_planform | None)
EmpenageResult = tuple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sweep_half(sweep_quarter_rad: float, c_root: float, span: float, taper: float) -> float:
    """Quarter-chord sweep → half-chord sweep [rad]."""
    return np.arctan(np.tan(sweep_quarter_rad) - c_root / span * 0.25 * (1 - taper))


def _CL_alpha(planform: Planform) -> float:
    """3D lift-curve slope via Helmbold–DATCOM formula [1/rad]."""
    a0   = planform.airfoil_lift_slope
    AR   = planform.aspect_ratio
    kap  = a0 / (2 * np.pi)
    Lam  = _sweep_half(planform.sweep_quarter_rad, planform.c_root, planform.span, planform.taper)
    return a0 * AR / (2 + np.sqrt(4 + (AR / kap) ** 2 * (1 + np.tan(Lam) ** 2)))


def _downwash(CL_alpha_w: float, AR_w: float) -> float:
    """Simplified downwash gradient dε/dα."""
    return 2 * CL_alpha_w / (np.pi * AR_w)


def _is_set(x) -> bool:
    """True if x is a real (non-None, non-NaN) position."""
    return x is not None and not np.isnan(x)


def _make_planform(S: float, AR: float, taper: float, sweep_deg: float, t_c: float) -> Planform:
    """Construct a symmetric Planform from area and statistical geometry."""
    b = np.sqrt(S * AR)
    return Planform(
        aspect_ratio             = AR,
        span                     = b,
        sweep_quarter_deg        = sweep_deg,
        taper                    = taper,
        thickness_to_chord       = t_c,
        cm_quarter_chord         = 0.0,
        wetted_surface_ratio     = 2.0,
        interference_factor      = 1.05,
        clmax                    = 1.2,
        flap                     = False,
        airfoil_lift_slope       = 2 * np.pi,
        cl0                      = 0.0,
    )


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class EmpenageFinder(ABC):
    """Base class for empenage sizing."""

    @staticmethod
    def find_empenage(planform: Planform, fixed: Fixed, stable: bool) -> EmpenageResult:
        """
        Size the empenage and return (tail, canard) Planforms.

        Routes to the appropriate finder based on which LE positions are set
        (non-NaN) in Fixed:
            x_LE_tail only          → TailFinder
            x_LE_canard only        → CanardFinder
            both set                → ThreeSurfaceFinder

        Args:
            planform: Wing planform (geometry + aerodynamic properties).
            fixed:    Fixed CAD geometry (CG, LE positions, etc.).
            stable:   True  → scissor-plot sizing for required SM.
                      False → volume-coefficient sizing (FBW / unstable).

        Returns:
            (tail: Planform | None, canard: Planform | None)
        """
        has_tail   = _is_set(getattr(fixed, 'x_LE_tail',   None))
        has_canard = _is_set(getattr(fixed, 'x_LE_canard', None))

        if has_tail and has_canard:
            finder = ThreeSurfaceFinder()
        elif has_canard:
            finder = CanardFinder()
        else:
            finder = TailFinder()

        return finder.size_empenage(planform, fixed, stable)

    @abstractmethod
    def size_empenage(self, planform: Planform, fixed: Fixed, stable: bool) -> EmpenageResult:
        pass

    def _wing_aero(self, planform: Planform, fixed: Fixed) -> tuple:
        """Return (x_AC_wing [abs], CL_alpha_wing)."""
        x_AC_w     = fixed.x_LE_wing + planform.aerodynamic_center(N)
        CL_alpha_w = _CL_alpha(planform)
        return x_AC_w, CL_alpha_w


# ---------------------------------------------------------------------------
# Tail-only sizing
# ---------------------------------------------------------------------------

class TailFinder(EmpenageFinder):
    """Conventional aft horizontal tail sizing."""

    def size_empenage(self, planform: Planform, fixed: Fixed, stable: bool) -> EmpenageResult:
        tail = self._find_stable(planform, fixed) if stable else self._find_unstable(planform, fixed)
        return (tail, None)

    def _find_stable(self, planform: Planform, fixed: Fixed) -> Planform:
        """
        Scissor-plot sizing: find minimum S_h so that x_np >= x_cg + SM * MAC_w.

        Neutral-point equation (with downwash):
            x_np = x_AC_w + (CL_alpha_h_eff / CL_alpha_w) * (S_h/S_w) * l_h

        Solved iteratively because the tail AC offset depends on S_h (through MAC_h).
        """
        x_AC_w, CL_alpha_w = self._wing_aero(planform, fixed)
        deps_dalpha          = _downwash(CL_alpha_w, planform.aspect_ratio)
        x_np_req             = fixed.x_cg + SM * planform.MAC

        S_h = 0.15 * planform.wing_area
        for _ in range(15):
            tail       = _make_planform(S_h, A_H, TAPER_H, SWEEP_H, T_C_H)
            x_AC_h     = fixed.x_LE_tail + tail.aerodynamic_center(N)
            CL_alpha_h = _CL_alpha(tail) * (1 - deps_dalpha)

            l_h = x_AC_h - x_AC_w
            if l_h <= 0:
                raise ValueError(
                    f"Tail AC ({x_AC_h:.2f} m) is not aft of wing AC ({x_AC_w:.2f} m)."
                )

            S_h_new = (x_np_req - x_AC_w) / ((CL_alpha_h / CL_alpha_w) * l_h) * planform.wing_area

            if abs(S_h_new - S_h) < 1e-5:
                S_h = S_h_new
                break
            S_h = S_h_new

        return _make_planform(S_h, A_H, TAPER_H, SWEEP_H, T_C_H)

    def _find_unstable(self, planform: Planform, fixed: Fixed) -> Planform:
        """Volume-coefficient sizing:  S_h = V_H * S_w * MAC_w / l_h"""
        x_AC_w, _ = self._wing_aero(planform, fixed)
        l_h        = fixed.x_LE_tail - x_AC_w
        S_h        = V_H * planform.wing_area * planform.MAC / l_h
        return _make_planform(S_h, A_H, TAPER_H, SWEEP_H, T_C_H)


# ---------------------------------------------------------------------------
# Canard-only sizing
# ---------------------------------------------------------------------------

class CanardFinder(EmpenageFinder):
    """Forward canard sizing (no aft tail)."""

    def size_empenage(self, planform: Planform, fixed: Fixed, stable: bool) -> EmpenageResult:
        canard = self._find_stable(planform, fixed) if stable else self._find_unstable(planform, fixed)
        return (None, canard)

    def _find_stable(self, planform: Planform, fixed: Fixed) -> Planform:
        """
        Scissor-plot sizing: find maximum S_c so that x_np >= x_cg + SM * MAC_w.

        For a canard-wing, the canard shifts the NP forward; a larger canard
        makes the aircraft LESS stable. This gives the stability-limited maximum.

        Neutral-point equation:
            x_np = x_AC_w + (CL_alpha_c / CL_alpha_w) * (S_c/S_w) * (x_AC_c - x_AC_w)

        Solved for S_c given x_np = x_cg + SM * MAC_w.
        """
        x_AC_w, CL_alpha_w = self._wing_aero(planform, fixed)
        x_np_req             = fixed.x_cg + SM * planform.MAC

        if x_np_req >= x_AC_w:
            raise ValueError(
                f"Required NP ({x_np_req:.2f} m) must be forward of wing AC ({x_AC_w:.2f} m) "
                "for a canard configuration. Move x_cg forward or adjust wing position."
            )

        S_c = 0.05 * planform.wing_area
        for _ in range(30):
            canard     = _make_planform(S_c, A_C, TAPER_C, SWEEP_C, T_C_C)
            x_AC_c     = fixed.x_LE_canard + canard.aerodynamic_center(N)
            CL_alpha_c = _CL_alpha(canard)

            if x_AC_c >= x_np_req:
                raise ValueError(
                    f"Canard AC ({x_AC_c:.2f} m) has grown past the required NP "
                    f"({x_np_req:.2f} m). Check CG position and canard LE location."
                )

            denom   = CL_alpha_c * (x_np_req - x_AC_c)
            S_c_new = CL_alpha_w * (x_AC_w - x_np_req) / denom * planform.wing_area

            if abs(S_c_new - S_c) < 1e-5:
                S_c = S_c_new
                break
            S_c = 0.5 * S_c + 0.5 * S_c_new    # damp to avoid divergence

        return _make_planform(S_c, A_C, TAPER_C, SWEEP_C, T_C_C)

    def _find_unstable(self, planform: Planform, fixed: Fixed) -> Planform:
        """Volume-coefficient sizing:  S_c = V_C * S_w * MAC_w / l_c"""
        x_AC_w, _ = self._wing_aero(planform, fixed)
        l_c        = x_AC_w - fixed.x_LE_canard
        S_c        = V_C * planform.wing_area * planform.MAC / l_c
        return _make_planform(S_c, A_C, TAPER_C, SWEEP_C, T_C_C)


# ---------------------------------------------------------------------------
# Three-surface sizing (tail + canard simultaneously)
# ---------------------------------------------------------------------------

class ThreeSurfaceFinder(EmpenageFinder):
    """
    Three-surface aircraft: canard + wing + aft tail.

    Stable:   Canard sized by volume coefficient (V_C); tail solved from
              the 3-surface NP stability equation:

                x_np = x_AC_w + (1/CL_alpha_w) * [
                    CL_alpha_c*(S_c/S_w)*(x_AC_c - x_AC_w)
                  + CL_alpha_h_eff*(S_h/S_w)*(x_AC_h - x_AC_w)
                ]

              The canard contribution pulls the NP forward, so more tail
              is required than in a tail-only design.

    Unstable: Both surfaces sized independently by volume coefficients.
    """

    def size_empenage(self, planform: Planform, fixed: Fixed, stable: bool) -> EmpenageResult:
        return self._find_stable(planform, fixed) if stable else self._find_unstable(planform, fixed)

    def _find_stable(self, planform: Planform, fixed: Fixed) -> EmpenageResult:
        x_AC_w, CL_alpha_w = self._wing_aero(planform, fixed)
        deps_dalpha          = _downwash(CL_alpha_w, planform.aspect_ratio)
        x_np_req             = fixed.x_cg + SM * planform.MAC

        # 1. Size canard by volume coefficient (fixed contribution)
        l_c        = x_AC_w - fixed.x_LE_canard
        S_c        = V_C * planform.wing_area * planform.MAC / l_c
        canard     = _make_planform(S_c, A_C, TAPER_C, SWEEP_C, T_C_C)
        x_AC_c     = fixed.x_LE_canard + canard.aerodynamic_center(N)
        CL_alpha_c = _CL_alpha(canard)

        # 2. Solve for tail area (iterative — tail AC depends on S_h)
        #
        # 3-surface NP rearranged for S_h:
        #   S_h = [CL_w*S_w*(x_np - x_AC_w) - CL_c*S_c*(x_AC_c - x_AC_w)]
        #         / [CL_h_eff*(x_AC_h - x_AC_w)]
        #
        # (x_AC_c - x_AC_w) < 0, so the canard term adds to the numerator,
        # requiring more tail than in a tail-only design.
        S_h = 0.15 * planform.wing_area
        for _ in range(15):
            tail       = _make_planform(S_h, A_H, TAPER_H, SWEEP_H, T_C_H)
            x_AC_h     = fixed.x_LE_tail + tail.aerodynamic_center(N)
            CL_alpha_h = _CL_alpha(tail) * (1 - deps_dalpha)

            l_h = x_AC_h - x_AC_w
            if l_h <= 0:
                raise ValueError(
                    f"Tail AC ({x_AC_h:.2f} m) is not aft of wing AC ({x_AC_w:.2f} m)."
                )

            numerator = (
                CL_alpha_w * planform.wing_area * (x_np_req - x_AC_w)
                - CL_alpha_c * S_c * (x_AC_c - x_AC_w)
            )
            S_h_new = numerator / (CL_alpha_h * l_h)

            if abs(S_h_new - S_h) < 1e-5:
                S_h = S_h_new
                break
            S_h = S_h_new

        return (_make_planform(S_h, A_H, TAPER_H, SWEEP_H, T_C_H), canard)

    def _find_unstable(self, planform: Planform, fixed: Fixed) -> EmpenageResult:
        """Both surfaces sized by volume coefficients independently."""
        x_AC_w, _ = self._wing_aero(planform, fixed)

        l_h = fixed.x_LE_tail   - x_AC_w
        l_c = x_AC_w - fixed.x_LE_canard

        S_h = V_H * planform.wing_area * planform.MAC / l_h
        S_c = V_C * planform.wing_area * planform.MAC / l_c

        return (
            _make_planform(S_h, A_H, TAPER_H, SWEEP_H, T_C_H),
            _make_planform(S_c, A_C, TAPER_C, SWEEP_C, T_C_C),
        )
