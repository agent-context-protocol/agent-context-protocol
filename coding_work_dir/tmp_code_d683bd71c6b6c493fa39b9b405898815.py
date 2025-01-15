
import numpy as np

entries = {
    "Time-Parking 2: Parallel Universe": 2009,
    "Cereal Killer III: Incomplete Breakfast": 2011,
    "Windshield Bug: The First Ten Seasons": 2016,
    "A Protist's Life": 2018,
    "My Neighbor Is A Shrimp Farmer": 2022,
    "Dogs and Croatia: A Movie About Both These Things": 2023
}

oldest_year = np.min(list(entries.values()))
oldest_titles = [title for title, year in entries.items() if year == oldest_year]

print(oldest_titles[0])
