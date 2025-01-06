
import numpy as np

value1 = 8000000
value2 = 6840000

difference = np.abs(value1 - value2)
difference_in_tens_of_thousands = difference / 10000

print(difference_in_tens_of_thousands)
