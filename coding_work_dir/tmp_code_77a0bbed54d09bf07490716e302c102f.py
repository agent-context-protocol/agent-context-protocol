
import numpy as np
from datetime import datetime

# Define the word counts for each book
word_counts = {
    'Fire and Blood': 262000,
    'Song of Solomon': 92800,
    'The Lost Symbol': 144400,
    '2001: A Space Odyssey': 60482,
    'American Gods': 183222,
    'Out of the Silent Planet': 64116,
    'The Andromeda Strain': 72000,
    'Brave New World': 64000,
    'Silence': 75161,
    'The Shining': 162726
}

# Define the start and end dates for each book
date_ranges = {
    'Fire and Blood': ('2022-01-01', '2022-02-14'),
    'Song of Solomon': ('2022-02-15', '2022-04-04'),
    'The Lost Symbol': ('2022-04-05', '2022-06-10'),
    '2001: A Space Odyssey': ('2022-06-11', '2022-07-04'),
    'American Gods': ('2022-07-05', '2022-08-24'),
    'Out of the Silent Planet': ('2022-08-25', '2022-09-30'),
    'The Andromeda Strain': ('2022-10-01', '2022-10-31'),
    'Brave New World': ('2022-11-01', '2022-11-20'),
    'Silence': ('2022-11-21', '2022-12-24'),
    'The Shining': ('2022-12-25', '2022-12-31')
}

# Calculate the reading rate
reading_rates = {}
for book, dates in date_ranges.items():
    start_date = datetime.strptime(dates[0], '%Y-%m-%d')
    end_date = datetime.strptime(dates[1], '%Y-%m-%d')
    days_read = (end_date - start_date).days + 1
    word_count = word_counts[book]
    reading_rate = word_count / days_read
    reading_rates[book] = reading_rate

print(reading_rates)
