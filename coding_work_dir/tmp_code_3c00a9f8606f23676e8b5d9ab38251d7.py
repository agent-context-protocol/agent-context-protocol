
import numpy as np

# Configuration of wheels: (leading, driving, trailing)
configurations = {
    '0-4-0': (0, 4, 0),
    '4-4-0': (4, 4, 0),
    '2-6-0': (2, 6, 0),
    '2-8-0': (2, 8, 0),
    '2-6-4': (2, 6, 4),
    '2-8-4': (2, 8, 4)
}

# Calculate total number of wheels for each configuration
total_wheels_per_configuration = [sum(wheel_set) for wheel_set in configurations.values()]

# Sum all the wheels in all configurations
total_wheels = np.sum(total_wheels_per_configuration)

print(total_wheels)
