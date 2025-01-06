
import numpy as np

# Input: total number of items listed in the 1959 standards
total_items_1959 = int(input("Enter the total number of items listed in the 1959 standards: "))

# Number of items superseded as of August 2023
items_superseded = total_items_1959  # Since all items have been superseded

# Calculate the percentage of standards superseded
percentage_superseded = (items_superseded / total_items_1959) * 100

print(f"Percentage of standards superseded: {percentage_superseded:.2f}%")
