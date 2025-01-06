
import numpy as np

# Define the constants
Vmax = 0.0429
[S] = 72.3
Km = 0.052

# Calculate the reaction velocity using the Michaelis-Menten equation
v = (Vmax * [S]) / (Km + [S])

# Print the result rounded to four decimal places
print(round(v, 4))
