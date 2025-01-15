
import numpy as np

number_of_papers = 1002
error_rate = 0.05

incorrect_papers = number_of_papers * error_rate
expected_incorrect_papers = np.ceil(incorrect_papers)

print(int(expected_incorrect_papers))
