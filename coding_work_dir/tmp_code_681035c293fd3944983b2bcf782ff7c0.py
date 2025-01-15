
import numpy as np

# Constants
mass_freon12 = 0.312  # kg
density_freon12_trench = 1.486  # kg/L (density of Freon-12 under trench conditions)

# Calculation
volume_freon12 = mass_freon12 / density_freon12_trench  # volume = mass / density

# Print the result
print(volume_freon12)
