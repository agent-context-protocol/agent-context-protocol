
import numpy as np
from datetime import datetime

# Suppose the spreadsheet data is loaded as follows, with each book's period as a tuple (start_date, end_date)
book_dates = [
    ("2023-01-01", "2023-01-10"),
    ("2023-02-05", "2023-02-20"),
    ("2023-03-12", "2023-03-15"),
    ("2023-04-01", "2023-04-30"),
    ("2023-05-10", "2023-05-15"),
    ("2023-06-01", "2023-06-18"),
    ("2023-07-04", "2023-07-20"),
    ("2023-08-15", "2023-08-25"),
    ("2023-09-03", "2023-09-12"),
    ("2023-10-21", "2023-10-30")
]

def calculate_days(book_dates):
    days_between = []
    for start_date, end_date in book_dates:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        delta = end - start
        days_between.append(delta.days)
    return days_between

days_between = calculate_days(book_dates)
print(days_between)
