
import numpy as np

point1 = np.array([90.574, -8.433, 100.549])
point2 = np.array([91.872, -7.99, 100.059])

# Calculate Euclidean distance
distance = np.linalg.norm(point1 - point2)

# Convert from Angstroms to picometers by multiplying by 100 and round to nearest picometer
distance_picometers = round(distance * 100)

print(distance_picometers)
