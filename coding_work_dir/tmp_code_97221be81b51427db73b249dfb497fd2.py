
import numpy as np

data = {
    "Hotels": [
        {"name": "Neptune's Palace", "rating": 5},
        {"name": "Admiral Sturgeon", "rating": 5},
        {"name": "Currents", "rating": 4},
        {"name": "The Laughing Gull", "rating": 3},
        {"name": "Loach Towers", "rating": 2}
    ],
    "Motels": [
        {"name": "Sea Escape Inn", "rating": 5},
        {"name": "Wash Inn", "rating": 3},
        {"name": "Boulevard Motel", "rating": 2},
        {"name": "Good Motel", "rating": 1},
        {"name": "Sea Larva Motel", "rating": 0}
    ],
    "Rental Houses": [
        {"name": "Cape Super", "rating": 4},
        {"name": "Bleek Island", "rating": 3},
        {"name": "Pinedrift Avenue", "rating": 4},
        {"name": "Ocean and Main", "rating": 5},
        {"name": "4th Street Cottage", "rating": 5},
        {"name": "Shelley's Place", "rating": 4},
        {"name": "Creakwood Creek", "rating": 3},
        {"name": "Headrush Beach", "rating": 3},
        {"name": "Shiplap Cabin", "rating": 3},
        {"name": "Haddonfield House", "rating": 1}
    ],
    "Campgrounds": [
        {"name": "The Glampground", "rating": 4},
        {"name": "Gull Crest", "rating": 5},
        {"name": "Barnacle Isle", "rating": 3},
        {"name": "Cozy Wood", "rating": 4},
        {"name": "Gravel Lot Campground", "rating": 1}
    ]
}

average_ratings = {}

for category, accommodations in data.items():
    ratings = [place["rating"] for place in accommodations]
    average_ratings[category] = np.mean(ratings)

print(average_ratings)
