
import numpy as np

# Define the two sections with items
dried_dehydrated_section = ['Apples (Dehydrated)', 'Peaches (Dehydrated)', 'Grapefruit Juice (Dehydrated)']
frozen_chilled_section = ['Orange Juice (Frozen)', 'Apple Juice (Frozen)']

# Define the superseded standards
superseded_standards = ['Apples (Dehydrated)', 'Grapefruit Juice (Dehydrated)', 'Orange Juice (Dehydrated)']

# Count total standards
total_standards = len(dried_dehydrated_section) + len(frozen_chilled_section)

# Count superseded standards present in the sections
count_superseded = sum(item in superseded_standards for item in dried_dehydrated_section)

# Calculate percentage of superseded standards
percentage_superseded = (count_superseded / total_standards) * 100

print(percentage_superseded)
