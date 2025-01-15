
import numpy as np

reading_durations = [
    {'title': 'Fire and Blood', 'duration': 44},
    {'title': 'Song of Solomon', 'duration': 48},
    {'title': 'The Lost Symbol', 'duration': 66},
    {'title': '2001: A Space Odyssey', 'duration': 23},
    {'title': 'American Gods', 'duration': 50},
    {'title': 'Out of the Silent Planet', 'duration': 36},
    {'title': 'The Andromeda Strain', 'duration': 30},
    {'title': 'Brave New World', 'duration': 19},
    {'title': 'Silence', 'duration': 33},
    {'title': 'The Shining', 'duration': 6}
]

word_counts = [
    {'title': 'Fire and Blood', 'word_count': 249322},
    {'title': 'Song of Solomon', 'word_count': 84250},
    {'title': 'The Lost Symbol', 'word_count': 159352},
    {'title': '2001: A Space Odyssey', 'word_count': 64175},
    {'title': 'American Gods', 'word_count': 188623},
    {'title': 'Out of the Silent Planet', 'word_count': 57000},
    {'title': 'The Andromeda Strain', 'word_count': 66103},
    {'title': 'Brave New World', 'word_count': 63766},
    {'title': 'Silence', 'word_count': 71901},
    {'title': 'The Shining', 'word_count': 160863}
]

reading_rates = []

for word_count_data in word_counts:
    title = word_count_data['title']
    word_count = word_count_data['word_count']
    
    duration_data = next(d for d in reading_durations if d['title'] == title)
    duration = duration_data['duration']
    
    reading_rate = word_count / duration
    reading_rates.append({'title': title, 'reading_rate': reading_rate})

slowest_book = min(reading_rates, key=lambda x: x['reading_rate'])

print(slowest_book['title'])
