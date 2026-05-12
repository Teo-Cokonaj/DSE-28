from dataclasses import dataclass, field
import copy
import aerosandbox.numpy as np
import aerosandbox as asb

import sys
import os

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Sizing_Loop.DesignOptionStateFixed import DesignOptionStateFixed
from src.Sizing_Loop.DesignOptionStateIterable import DesignOptionStateIterable
from src.global_parameters import CONSTANTS

@dataclass
class DesignOptionState:
    iterable:DesignOptionStateIterable
    _fixed:DesignOptionStateFixed = field(default_factory=lambda: copy.deepcopy(DesignOptionStateFixed()))

    @property
    def fixed(self) -> DesignOptionStateFixed:
        return self._fixed
    

    #======== Obtaining driven quantities =========
    def CL_A_h(self) -> float:
        return self.fixed.assumptions.positive_C_L_max_airfoil * .9 * np.cos(self.iterable.lifting_surfaces[0].sweep_quarter_rad)
    

    def CL_max(self) -> float:
        return self.CL_A_h() + self.iterable.lifting_surfaces[1].wing_area / self.iterable.lifting_surfaces[0].wing_area * self.CL_h_max()
    

    def wing_loading(self) -> float:
        return CONSTANTS.G0 * self.iterable.aircraft_parameters.total_mass / self.iterable.lifting_surfaces[0].wing_area
    

    def CL_h_max(self) -> float:
        return -.35 * self.iterable.lifting_surfaces[1].aspect_ratio**(1/3)
    

    def mach_go_around(self) -> float:
        assumptions = self.fixed.assumptions
        wing_loading = self.iterable.aircraft_parameters.total_mass / self.iterable.lifting_surfaces[0].wing_area
        CL_max_glide_ratio = np.sqrt(self.iterable.performance_parameters.go_around_parameters.CD0 * self.iterable.performance_parameters.go_around_parameters.inviscid_ratio)
        # determining go around parameters
        omega_turn = np.pi/assumptions.TIME_HALF_CIRCLE
        atmosphere_go_around = asb.Atmosphere(assumptions.ALTITUDE_GO_AROUND)
        rho_go_around_altitude = atmosphere_go_around.density()
        # n**2 - quadratic_b_term*n -1
        quadratic_b_term = omega_turn**2/CONSTANTS.G0**2 * wing_loading * 2/rho_go_around_altitude / CL_max_glide_ratio
        load_factor_go_around = .5*(quadratic_b_term + np.sqrt(quadratic_b_term**2+4))
        airspeed_go_around = np.sqrt(wing_loading * 2/rho_go_around_altitude * load_factor_go_around/CL_max_glide_ratio)

        return airspeed_go_around / atmosphere_go_around.speed_of_sound()