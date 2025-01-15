
import numpy as np

# Given density and volume of honey
density_honey = 1.420  # g/cm³
volume_honey = 237     # cm³

# Calculate weight using the formula: weight = density * volume
weight_honey = np.multiply(density_honey, volume_honey)

print(weight_honey)
