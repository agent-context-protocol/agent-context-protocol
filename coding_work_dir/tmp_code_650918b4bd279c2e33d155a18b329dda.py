
import numpy as np

# Given time in minutes, seconds, and milliseconds
minutes = 1
seconds = 38
milliseconds = 409

# Convert milliseconds to total seconds
total_seconds = seconds + milliseconds / 1000

# Round the seconds to the nearest hundredth
rounded_seconds = np.round(total_seconds, 2)

# Print minutes and rounded seconds
print(f"{minutes}' {rounded_seconds}\"")
