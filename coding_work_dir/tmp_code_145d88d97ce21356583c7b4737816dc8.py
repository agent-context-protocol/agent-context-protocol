
import numpy as np

books = [
    {"title": "The Lightning Thief", "author": "Rick Riordan", "status": "Checked Out"},
    {"title": "The Sea of Monsters", "author": "Rick Riordan", "status": "Available"},
    {"title": "The Titan's Curse", "author": "Rick Riordan", "status": "Checked Out"},
    {"title": "The Battle of the Labyrinth", "author": "Rick Riordan", "status": "Overdue"},
    {"title": "The Last Olympian", "author": "Rick Riordan", "status": "Checked Out"},
    {"title": "The Lost Hero", "author": "Rick Riordan", "status": "Available"},
    {"title": "The Son of Neptune", "author": "Rick Riordan", "status": "Overdue"}
]

statuses_to_count = {"Checked Out", "Overdue"}

count = np.sum(
    [book["status"] in statuses_to_count for book in books if book["author"] == "Rick Riordan"]
)

print(count)
