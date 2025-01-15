
import numpy as np

# Sample data
data = [
    {'Vendor': 'Vendor A', 'Revenue': 150000, 'Rent': 30000, 'Type': 'Retail'},
    {'Vendor': 'Vendor B', 'Revenue': 80000, 'Rent': 20000, 'Type': 'Wholesale'},
    {'Vendor': 'Vendor C', 'Revenue': 50000, 'Rent': 10000, 'Type': 'Service'},
]

# Calculate revenue-to-rent ratio
ratios = [(vendor['Revenue'] / vendor['Rent'], vendor['Type']) for vendor in data]

# Find the vendor with the lowest ratio
lowest_ratio = min(ratios, key=lambda x: x[0])
lowest_ratio_value, lowest_vendor_type = lowest_ratio

# Print the results
print(f"Lowest Revenue-to-Rent Ratio: {lowest_ratio_value}, Vendor Type: {lowest_vendor_type}")
