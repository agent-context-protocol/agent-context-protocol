
import numpy as np

point1 = np.array([90.574, -8.433, 100.549])
point2 = np.array([91.872, -7.99, 100.059])

# Calculate the Euclidean distance
distance_angstroms = np.linalg.norm(point1 - point2)

# Convert the distance from Angstroms to picometers (1 Angstrom = 100 picometers)
distance_picometers = distance_angstroms * 100

# Round to the nearest picometer
rounded_distance = round(distance_picometers)

print(rounded_distance)
