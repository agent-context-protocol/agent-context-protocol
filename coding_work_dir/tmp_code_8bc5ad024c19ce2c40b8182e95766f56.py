
import numpy as np

# Define the dimensions of Panel 4 (in cm)
length = 30  # cm
width = 40   # cm
height = 10  # cm

# Calculate the volume in cubic centimeters
volume_cm3 = length * width * height

# Convert the volume to milliliters (1 cm3 = 1 mL)
volume_ml = volume_cm3

# Round the volume to the nearest milliliter
rounded_volume_ml = round(volume_ml)

print(rounded_volume_ml)
