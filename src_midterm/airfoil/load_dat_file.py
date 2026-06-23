import aerosandbox as asb
import aerosandbox.numpy as np
from aerosandbox.geometry.airfoil.airfoil_families import get_coordinates_from_raw_dat

import sys
import os
current_file = os.path.abspath(__file__)
airfoil_folder = os.path.dirname(current_file)
project_root = os.path.dirname(airfoil_folder)
sys.path.append(project_root)

coords = np.loadtxt(os.path.join(airfoil_folder, "NASA SC(2)-0012 AIRFOIL.dat"), skiprows=1)

upper = coords[:coords.shape[0]//2] # Points 0 to 103
lower = coords[coords.shape[0]//2:] # Points 103 to end
print(upper[0, :], upper[-1, :], lower[0, :], lower[-1, :])

# Format for AeroSandbox: Trailing Edge -> Leading Edge -> Trailing Edge
upper_flipped = upper[::-1]

# 2. Combine with lower (skipping the first point of lower because it's (0,0) and already at the end of upper_flipped)
coords_fixed = np.vstack([upper_flipped, lower[1:]])

airfoil = asb.Airfoil(
    name="NASA SC(2)-0012",
    coordinates=coords_fixed
).normalize().repanel(n_points_per_side=50)

# airfoil.generate_polars(
#     alphas = np.linspace(-10., 15., 10),
#     Res = np.geomspace(1e6, 1e8, 10),
#     cache_filename = "src/airfoil/NASA_SC2_0012"
# )

# Check if coords are loaded correctly
print(coords_fixed)
c_root = 0.1937 # m
thickness = 0.0025 # m

mid_t_cr = c_root - thickness
initial_x=coords_fixed[:-1,0]*mid_t_cr
initial_y=coords_fixed[:-1,1]*mid_t_cr
shifted_x=coords_fixed[1:,0]*mid_t_cr
shifted_y=coords_fixed[1:,1]*mid_t_cr

distances = np.sqrt((shifted_x-initial_x)**2+(shifted_y-initial_y)**2)
y_segments = (shifted_y + initial_y)/2


I_xxs = distances * thickness * y_segments**2
Ixx = I_xxs.sum()

a=c_root / 2
b=0.12*a
Ixx_ellipse=np.pi*a*b**3/4 - np.pi*(a-thickness)*(b-thickness)**3/4

# print(coords_fixed.shape)
print('Airfoil AMOI: ',Ixx)
print('Ellipse AMOI: ',Ixx_ellipse)

#Finding tc max
tc_max_location = 0.
tc_max = 0.

max_camber_location = 0.
max_camber = 0.

for i in range(len(upper)):
    tc = upper[i, 1] - lower[i, 1]
    if tc > tc_max:
        tc_max = tc
        tc_max_location = (upper[i, 0] + lower[i, 0]) / 2

    camber = (upper[i, 1] + lower[i, 1]) / 2
    if camber > max_camber:
        max_camber = camber
        max_camber_location = (upper[i, 0] + lower[i, 0]) / 2

print(f"Maximum thickness to chord: {tc_max} @ (x/c)={tc_max_location}")
print(f"Maximum camber: {max_camber} @ (x/c)={max_camber_location}")


# Check airfoil shape
airfoil.draw()