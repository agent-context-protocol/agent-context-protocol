
import numpy as np

# Given weights in kg
gallon_weight_kg = 5.746481909360706
cup_weight_g = 336.54
cup_weight_kg = cup_weight_g / 1000  # Convert to kg

# Calculate number of cups needed to be removed
cups_to_remove = np.ceil((gallon_weight_kg - gallon_weight_kg) / cup_weight_kg)

# Print the number of cups to remove
print(int(cups_to_remove))
