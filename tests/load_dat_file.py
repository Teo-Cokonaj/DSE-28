import aerosandbox as asb
import aerosandbox.numpy as np
from aerosandbox.geometry.airfoil.airfoil_families import get_coordinates_from_raw_dat

coords = np.loadtxt(r"C:\Users\Plami\Downloads\NASA SC(2)-0412 AIRFOIL.dat", skiprows=1)

airfoil = asb.Airfoil(
    name="NASA SC(2)-0412",
    coordinates=coords
)

# Check if coords are loaded correctly
print(coords)
print(coords.shape)

# Check airfoil shape
airfoil.draw()