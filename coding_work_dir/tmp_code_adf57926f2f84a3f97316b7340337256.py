
import numpy as np

ratings = {
    'Hotels': [5, 5, 4, 3, 2],
    'Motels': [5, 3, 2, 1, 0],
    'Rental Houses': [4, 3, 4, 5, 5, 4, 3, 3, 3, 1],
    'Campgrounds': [4, 5, 3, 4, 1]
}

average_ratings = {key: np.mean(value) for key, value in ratings.items()}

print(average_ratings)
