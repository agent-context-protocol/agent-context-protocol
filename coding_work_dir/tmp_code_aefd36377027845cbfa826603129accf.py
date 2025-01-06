
import numpy as np

original_standards_1959 = ['Processed Raisins', 'Apples', 'Beans', 'Oranges', 'Pears']
superseded_standards = ['Processed Raisins', 'Apples', 'Beans']

# Calculate percentage of superseded standards
percentage_superseded = (len(superseded_standards) / len(original_standards_1959)) * 100
rounded_percentage_superseded = np.round(percentage_superseded)

print(int(rounded_percentage_superseded))
