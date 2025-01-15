
import numpy as np

# Define variables
miles = 2721.2
bottles_per_100_miles = 5

# Calculate total bottles
total_bottles = np.ceil(miles / 100) * bottles_per_100_miles

# Print the result
print(total_bottles)
