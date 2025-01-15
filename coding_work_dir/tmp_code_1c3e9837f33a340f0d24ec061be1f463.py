
import numpy as np

data = [39, 54, 29, 28, 73, 68, 47, 60, 53, 59, 64, 40, 75, 26, 31, 55, 70, 31, 44, 38, 55, 46, 78, 66, 35, 41, 53, 77]

sample_std_dev = np.std(data, ddof=1)
print(sample_std_dev)
