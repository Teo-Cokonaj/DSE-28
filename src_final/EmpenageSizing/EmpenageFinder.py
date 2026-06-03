import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Aircraft.Planform import Planform
from Aircraft.Fixed import Fixed
from abc import ABC, abstractmethod

class EmpenageFinder(ABC):
    """Base class for empenage (tail/canard) sizing."""

    @staticmethod
    def find_empenage(planform: Planform, fixed: Fixed, stable: bool) -> Planform:
        """
        Route to appropriate empenage finder based on configuration.

        Args:
            planform: Aircraft planform with wing geometry
            fixed: Fixed CAD geometry
            stable: True for stable tail (scissor plot), False for unstable

        Returns:
            Planform with configured empenage
        """
        # TODO: Detect tail vs canard type (check fixed or planform attributes)
        is_tail = True  # placeholder detection logic

        if is_tail:
            finder = TailFinder()
        else:
            finder = CanardFinder()

        return finder.size_empenage(planform, fixed, stable)

    @abstractmethod
    def size_empenage(self, planform: Planform, fixed: Fixed, stable: bool) -> Planform:
        """Size the empenage and return updated planform."""
        pass

    def _find_stable(self, planform: Planform, fixed: Fixed) -> Planform:
        """Stable empenage using scissor plot method."""
        # TODO: Implement scissor plot sizing
        # - Calculate required CL_H (statistical or from stability margin)
        # - Calculate A_H (aspect ratio)
        # - Size tail planform geometry
        raise NotImplementedError

    def _find_unstable(self, planform: Planform, fixed: Fixed) -> Planform:
        """Unstable empenage (unconstrained sizing)."""
        # TODO: Implement alternative sizing method
        # - Use statistical values from midterm
        # - Size based on volume coefficients
        raise NotImplementedError


class TailFinder(EmpenageFinder):
    """Conventional horizontal tail sizing."""

    def size_empenage(self, planform: Planform, fixed: Fixed, stable: bool) -> Planform:
        """Size horizontal tail based on stability requirement."""
        if stable:
            return self._find_stable(planform, fixed)
        else:
            return self._find_unstable(planform, fixed)


class CanardFinder(EmpenageFinder):
    """Canard empenage sizing."""

    def size_empenage(self, planform: Planform, fixed: Fixed, stable: bool) -> Planform:
        """Size canard based on stability requirement."""
        if stable:
            return self._find_stable(planform, fixed)
        else:
            return self._find_unstable(planform, fixed)
