
import numpy as np

# Load the CSV file into a structured numpy array
data = np.genfromtxt('/Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_GAIA_Simple/GAIA/2023/validation/8d46b8d6-b38a-47ff-ac74-cda14cf2d19b.csv', delimiter=',', dtype=None, encoding=None, names=True)

# Count penguins that do not live on Dream Island or have beaks longer than 42mm
count = np.sum((data['Island'] != 'Dream Island') | (data['BeakLength'] > 42))

print(count)
