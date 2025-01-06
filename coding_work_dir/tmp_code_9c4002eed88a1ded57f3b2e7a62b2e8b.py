
import numpy as np

mass_kg = 0.312
density_kg_per_m3 = 1.7348

# Convert mass from kg to grams because 1 kg = 1000 grams
mass_g = mass_kg * 1000

# Density conversion: from kg/m^3 to g/cm^3, as 1 g/cm^3 = 1000 kg/m^3
density_g_per_cm3 = density_kg_per_m3 / 1000

# Calculate volume in cm^3: volume = mass / density
volume_cm3 = mass_g / density_g_per_cm3

# Convert volume from cm^3 to mL as 1 mL = 1 cm^3
volume_mL = volume_cm3

print(volume_mL)
