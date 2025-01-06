
import numpy as np

value1 = 8
value2 = 4.75

percentage = (value1 / value2) * 100
rounded_percentage = np.rint(percentage).astype(int)

print(rounded_percentage)
