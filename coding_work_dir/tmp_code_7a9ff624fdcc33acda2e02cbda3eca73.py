
import numpy as np

# Constants for Freon-12 (in SI units)
molecular_weight = 120.91  # g/mol
density = 1.486  # g/cm³

# Required volume calculation in cubic centimeters
mass_grams = 1000  # Example mass in grams
volume_cc = mass_grams / density

# Convert cubic centimeters to milliliters (1 cc = 1 mL)
volume_ml = volume_cc

# Round to the nearest milliliter
volume_ml_rounded = np.round(volume_ml)

print(volume_ml_rounded)
