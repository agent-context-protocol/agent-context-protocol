
import numpy as np

# Given densities in g/cm³ and volume in cm³
density_honey = 1.420  # g/cm³
density_mayo = 0.910  # g/cm³
volume_gallon = 3785.41  # cm³

# Calculate masses using mass = density * volume
mass_honey = density_honey * volume_gallon
mass_mayo = density_mayo * volume_gallon

# Volume of a cup in cm³
cup_volume = 236.588  # cm³

# Calculate cups to be removed
cups_removed = 0
while mass_honey >= mass_mayo:
    mass_honey -= density_honey * cup_volume
    cups_removed += 1

print(cups_removed)
