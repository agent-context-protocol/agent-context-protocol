
import numpy as np

# Tropicos ID
tropicos_id = '100370510'

# Extract the first 9 digits
first_nine_digits = tropicos_id[:9]

# Calculate weighted sum
weights = np.arange(1, 10)
digits = np.array([int(d) for d in first_nine_digits])
weighted_sum = np.sum(weights * digits)

# Compute modulus
modulus = weighted_sum % 11

# Determine check digit
check_digit = 'X' if modulus == 10 else modulus

print(check_digit)
