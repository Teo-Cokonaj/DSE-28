import aerosandbox as asb
import aerosandbox.numpy as np
from aerosandbox.geometry.airfoil.airfoil_families import get_coordinates_from_raw_dat

import sys
import os
current_file = os.path.abspath(__file__)
airfoil_folder = os.path.dirname(current_file)
project_root = os.path.dirname(airfoil_folder)
sys.path.append(project_root)

class SymmetricAirfoil(asb.Airfoil):
    def __init__(self, name = "Untitled"):

        coords = np.loadtxt(f"{airfoil_folder}\\NASA SC(2)-0012 AIRFOIL.dat", skiprows=1)

        # Flipping the dat file upper surface and removing the duplicate (0, 0) to match the xfoil conventions.
        upper = coords[:coords.shape[0]//2] 
        lower = coords[coords.shape[0]//2:]
        upper_flipped = upper[::-1]
        coords_fixed = np.vstack([upper_flipped, lower[1:]])

        super().__init__(name, coords_fixed)

        self.repanel(n_points_per_side=50)


if __name__ == "__main__":
    SymmetricAirfoil().draw()