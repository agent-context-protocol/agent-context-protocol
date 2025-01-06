
import numpy as np

# Latitude and Longitude of Jakarta, Indonesia
jakarta_lat = -6.2088
jakarta_lon = 106.8456

# Latitude and Longitude of Naypyidaw, Myanmar
naypyidaw_lat = 19.7633
naypyidaw_lon = 96.0785

def haversine(lat1, lon1, lat2, lon2):
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert degrees to radians
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0)**2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    # Distance in kilometers
    distance = R * c
    return distance

distance_jakarta_naypyidaw = haversine(jakarta_lat, jakarta_lon, naypyidaw_lat, naypyidaw_lon)
countries = ["Indonesia", "Myanmar"]

# Sort countries alphabetically
countries.sort()

print(countries)
