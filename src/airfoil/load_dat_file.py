import aerosandbox as asb
import aerosandbox.numpy as np
from aerosandbox.geometry.airfoil.airfoil_families import get_coordinates_from_raw_dat

import sys
import os
current_file = os.path.abspath(__file__)
airfoil_folder = os.path.dirname(current_file)
project_root = os.path.dirname(airfoil_folder)
sys.path.append(project_root)

coords = np.loadtxt(f"{airfoil_folder}\\NASA SC(2)-0012 AIRFOIL.dat", skiprows=1)

# Split into upper and lower surfaces assuming 102 points each based on your data)
# The data has (0,0) twice, so we separate them carefully.
upper = coords[:coords.shape[0]//2] # Points 0 to 101
lower = coords[coords.shape[0]//2:] # Points 102 to end
print(upper[0, :], upper[-1, :], lower[0, :], lower[-1, :])

# Format for AeroSandbox: Trailing Edge -> Leading Edge -> Trailing Edge
# 1. Flip upper so it goes from TE (1,0) to LE (0,0)
upper_flipped = upper[::-1]

# 2. Combine with lower (skipping the first point of lower because it's (0,0) and already at the end of upper_flipped)
coords_fixed = np.vstack([upper_flipped, lower[1:]])

airfoil = asb.Airfoil(
    name="NASA SC(2)-0012",
    coordinates=coords_fixed
).normalize().repanel(n_points_per_side=50)

airfoil.generate_polars(
    alphas = np.linspace(-10., 15., 10),
    Res = np.geomspace(1e6, 1e8, 10),
    cache_filename = "src/airfoil/NASA_SC2_0012"
)

# Check if coords are loaded correctly
print(coords_fixed)
print(coords_fixed.shape)

# Check airfoil shape
airfoil.draw()