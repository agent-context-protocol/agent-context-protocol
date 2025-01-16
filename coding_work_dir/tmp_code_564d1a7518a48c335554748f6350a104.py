
import numpy as np

value = 74
total = 41754153
percentage = (value / total) * 100
rounded_percentage = np.floor(percentage * 100) / 100

print(rounded_percentage)
