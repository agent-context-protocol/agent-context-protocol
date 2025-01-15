
import numpy as np

# Word counts for each book
word_counts = {
    "Fire and Blood": 201161,
    "Song of Solomon": 90145.5,
    "The Lost Symbol": 155442,
    "2001: A Space Odyssey": 64175,
    "American Gods": 188623
}

# Reading durations for each book
reading_durations = {
    "Fire and Blood": 44,
    "Song of Solomon": 48,
    "The Lost Symbol": 66,
    "2001: A Space Odyssey": 23,
    "American Gods": 50,
    "Out of the Silent Planet": 36,
    "The Andromeda Strain": 30,
    "Brave New World": 19,
    "Silence": 33,
    "The Shining": 6
}

# Calculate reading rates (words per day)
reading_rates = {}
for book in word_counts:
    if book in reading_durations:
        reading_rates[book] = word_counts[book] / reading_durations[book]

print(reading_rates)
