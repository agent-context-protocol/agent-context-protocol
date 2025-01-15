
import numpy as np

# Coordinates of ASEAN capital cities (latitude, longitude)
coordinates = {
    'Bandar Seri Begawan': (4.9031, 114.9398),  # Brunei
    'Phnom Penh': (11.5564, 104.9282),          # Cambodia
    'Jakarta': (-6.2088, 106.8456),             # Indonesia
    'Vientiane': (17.9757, 102.6331),           # Laos
    'Kuala Lumpur': (3.1390, 101.6869),         # Malaysia
    'Naypyidaw': (19.7633, 96.0785),            # Myanmar
    'Manila': (14.5995, 120.9842),              # Philippines
    'Singapore': (1.3521, 103.8198),            # Singapore
    'Bangkok': (13.7563, 100.5018),             # Thailand
    'Hanoi': (21.0285, 105.8542)                # Vietnam
}

# Haversine formula to calculate the distance between two points on the Earth's surface
def haversine(coord1, coord2):
    R = 6371  # Earth's radius in km
    lat1, lon1 = np.radians(coord1)
    lat2, lon2 = np.radians(coord2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    distance = R * c
    return distance

# Calculate all distances and find the maximum
max_distance = 0
country_pair = None

for city1, coord1 in coordinates.items():
    for city2, coord2 in coordinates.items():
        if city1 != city2:
            distance = haversine(coord1, coord2)
            if distance > max_distance:
                max_distance = distance
                country_pair = (city1, city2)

# Sort the cities alphabetically and retrieve their corresponding countries
country_pair = tuple(sorted(country_pair))
capital_country_map = {
    'Bandar Seri Begawan': 'Brunei',
    'Phnom Penh': 'Cambodia',
    'Jakarta': 'Indonesia',
    'Vientiane': 'Laos',
    'Kuala Lumpur': 'Malaysia',
    'Naypyidaw': 'Myanmar',
    'Manila': 'Philippines',
    'Singapore': 'Singapore',
    'Bangkok': 'Thailand',
    'Hanoi': 'Vietnam'
}

countries = sorted([capital_country_map[city] for city in country_pair])

print(countries)
