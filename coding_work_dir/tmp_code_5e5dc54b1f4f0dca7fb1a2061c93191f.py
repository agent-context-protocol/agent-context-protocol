
import numpy as np

# Sample data: words count per book and its respective reading durations in days
word_counts = np.array([10000, 15000, 8000, 25000, 12000, 18000])
reading_durations = np.array([10, 15, 9, 20, 12, 18])

# Calculate the reading rate (words per day) for each book
reading_rates = word_counts / reading_durations

# Identify the book with the slowest reading rate (minimum rate)
slowest_rate_index = np.argmin(reading_rates)
slowest_reading_rate = reading_rates[slowest_rate_index]

print(slowest_reading_rate)
