
import numpy as np

# Example data: Dictionary with book titles as keys, and (word_count, days_read) as values
books_data = {
    'Book1': (45000, 10),
    'Book2': (60000, 7),
    'Book3': (40000, 5)
}

# Function to calculate reading rate
def calculate_reading_rate(data):
    reading_rates = {}
    for book, (word_count, days_read) in data.items():
        if days_read > 0:  # To avoid division by zero
            reading_rate = word_count / days_read
            reading_rates[book] = reading_rate
        else:
            reading_rates[book] = np.nan  # Use NaN for invalid days_read
    return reading_rates

# Calculate the reading rates
reading_rates = calculate_reading_rate(books_data)

# Print the reading rates
print(reading_rates)
