
import numpy as np

filtered_penguins = 291
total_penguins = 39713970

percentage = (filtered_penguins / total_penguins) * 100
rounded_percentage = np.round(percentage, 5)

print(rounded_percentage)
