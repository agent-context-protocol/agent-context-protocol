
import numpy as np
from datetime import datetime

# Define book details: (word range or exact word count, start date, end date)
books = [
    ((176500, 249322), "2022-01-01", "2022-02-14"),
    ((84250, 96041), "2022-02-15", "2022-04-04"),
    (159352, "2022-04-05", "2022-06-10"),
    (64175, "2022-06-11", "2022-07-04"),
    ((168000, 202591), "2022-07-05", "2022-08-24"),
    (57383, "2022-08-25", "2022-09-30"),
    (67526, "2022-10-01", "2022-10-31"),
    (63766, "2022-11-01", "2022-11-20"),
    (71901, "2022-11-21", "2022-12-24"),
    (149046, "2022-12-25", "2022-12-31")
]

def calculate_days(start_date, end_date):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    return (end - start).days + 1

def get_average_word_count(word_count):
    if isinstance(word_count, tuple):
        return np.mean(word_count)
    return word_count

reading_speeds = []

for words, start_date, end_date in books:
    total_words = get_average_word_count(words)
    days = calculate_days(start_date, end_date)
    speed = total_words / days
    reading_speeds.append(speed)

print(reading_speeds)
