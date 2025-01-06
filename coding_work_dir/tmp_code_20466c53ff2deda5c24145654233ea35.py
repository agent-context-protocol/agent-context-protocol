
import numpy as np

def calculate_percentage(total_penguins, qualifying_penguins):
    if total_penguins == 0:
        return 0.0
    percentage = (qualifying_penguins / total_penguins) * 100
    return np.round(percentage, 5)

total_penguins = 1000  # Example total
qualifying_penguins = 250  # Example qualifying
result = calculate_percentage(total_penguins, qualifying_penguins)
print(result)
