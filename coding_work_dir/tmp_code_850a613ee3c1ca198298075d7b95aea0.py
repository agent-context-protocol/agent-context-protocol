
import json
from datetime import datetime

data = [
    {"title": "Fire and Blood", "start_date": "2022-01-01", "end_date": "2022-02-14"},
    {"title": "Song of Solomon", "start_date": "2022-02-15", "end_date": "2022-04-04"},
    {"title": "The Lost Symbol", "start_date": "2022-04-05", "end_date": "2022-06-10"},
    {"title": "2001: A Space Odyssey", "start_date": "2022-06-11", "end_date": "2022-07-04"},
    {"title": "American Gods", "start_date": "2022-07-05", "end_date": "2022-08-24"},
    {"title": "Out of the Silent Planet", "start_date": "2022-08-25", "end_date": "2022-09-30"},
    {"title": "The Andromeda Strain", "start_date": "2022-10-01", "end_date": "2022-10-31"},
    {"title": "Brave New World", "start_date": "2022-11-01", "end_date": "2022-11-20"},
    {"title": "Silence", "start_date": "2022-11-21", "end_date": "2022-12-24"},
    {"title": "The Shining", "start_date": "2022-12-25", "end_date": "2022-12-31"}
]

reading_durations = []

for book in data:
    start_date = datetime.strptime(book["start_date"], "%Y-%m-%d")
    end_date = datetime.strptime(book["end_date"], "%Y-%m-%d")
    duration = (end_date - start_date).days
    reading_durations.append({"title": book["title"], "duration": duration})

print(reading_durations)
