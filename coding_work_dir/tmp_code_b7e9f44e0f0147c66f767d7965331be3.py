
import numpy as np

# Number of bottles
num_bottles = 140

# Refund per bottle in cents
refund_per_bottle = 5

# Calculate total refund in cents
total_refund_cents = num_bottles * refund_per_bottle

# Convert total refund to dollars
total_refund_dollars = np.round(total_refund_cents / 100, 2)

print(total_refund_dollars)
