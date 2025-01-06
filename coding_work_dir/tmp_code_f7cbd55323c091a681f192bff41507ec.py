
import numpy as np

number_of_bottles = 130
refund_value_per_bottle = 0.05  # in dollars

total_refund_amount = np.multiply(number_of_bottles, refund_value_per_bottle)
print(total_refund_amount)
