
import numpy as np

books_data = {
    'Fire and Blood': {'word_count': 176500, 'days_taken': 44},
    'Song of Solomon': {'word_count': 96041, 'days_taken': 48},
    'The Lost Symbol': {'word_count': 151532, 'days_taken': 66},
    '2001: A Space Odyssey': {'word_count': 56119, 'days_taken': 23},
    'American Gods': {'word_count': 185295.5, 'days_taken': 50},
    'Out of the Silent Planet': {'word_count': 57383, 'days_taken': 36},
    'The Andromeda Strain': {'word_count': 66103, 'days_taken': 30},
    'Brave New World': {'word_count': 63766, 'days_taken': 19},
    'Silence': {'word_count': 71901, 'days_taken': 33},
    'The Shining': {'word_count': 160341, 'days_taken': 6}
}

reading_rates = {}
for book, data in books_data.items():
    reading_rates[book] = data['word_count'] / data['days_taken']

for book, rate in reading_rates.items():
    print(f"{book}: {rate:.2f} words per day")
