
# Metro stations on the Green and Yellow Line which includes Shaw-Howard University and Ronald Reagan Washington National Airport stations.
metro_stations = [
    "Greenbelt", "College Park-U of Md", "Prince George's Plaza", "West Hyattsville", "Fort Totten",
    "Georgia Ave-Petworth", "Columbia Heights", "U Street", "Shaw-Howard U",  # Shaw-Howard University Metro Station
    "Mt Vernon Sq 7th St-Convention Center", "Gallery Pl-Chinatown", "Archives-Navy Memorial-Penn Quarter",
    "L'Enfant Plaza", "Waterfront", "Navy Yard-Ballpark", "Anacostia", "Congress Heights", "Southern Avenue", 
    "Naylor Road", "Suitland", "Branch Avenue",
    "Pentagon", "Pentagon City", "Crystal City", "Ronald Reagan Washington National Airport"
]

# Get the indices of the two metro stations
start_index = metro_stations.index("Shaw-Howard U")
end_index = metro_stations.index("Ronald Reagan Washington National Airport")

# Calculate the number of stations in between
number_of_stations = abs(end_index - start_index) - 1

print(number_of_stations)
