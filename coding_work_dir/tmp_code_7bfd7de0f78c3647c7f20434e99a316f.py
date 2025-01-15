
import numpy as np

# Assuming a certain additional cost from Panel 5
additional_cost_panel_5 = 850.75  # example additional cost

# Number of files
number_of_files = 1040

# Divide the additional cost by the number of files
cost_per_file = additional_cost_panel_5 / number_of_files

# Round to nearest cent
cost_per_file_rounded = np.round(cost_per_file, 2)

print(cost_per_file_rounded)
