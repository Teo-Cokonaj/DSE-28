import sys
import os
import aerosandbox.numpy as np
from dataclasses import dataclass

# Add the 'src' directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from landing_gear_configurations_class import Configurations_landing_gear_sizing


HUG_CFG_301 = Configurations_landing_gear_sizing(L1 = 0.31131738210748455, L2 = 0.9905553067056326, L3 = 0.6339553962916049, x_cg = 1, diameter_fuselage = 0.315, wing_span = 6)


print(HUG_CFG_301.lg_pos_and_length())
