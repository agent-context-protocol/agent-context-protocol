
import numpy as np

# Sample data representing the status of some Rick Riordan books
# 'Checked Out' or 'Overdue' imply the book is not on the shelf
book_statuses = np.array([
    'Available', 'Checked Out', 'Available', 'Overdue', 'Checked Out',
    'Available', 'Checked Out', 'Checked Out', 'Overdue', 'Available'
])

# Count the number of books with status 'Checked Out' or 'Overdue'
count_not_on_shelves = np.sum((book_statuses == 'Checked Out') | (book_statuses == 'Overdue'))

print(count_not_on_shelves)
