
import numpy as np

vendor_data = {
    "Rainforest Bistro": (32771, 1920),
    "Panorama Outfitters": (23170, 1788),
    "Zack's Cameras and Trail Mix": (33117, 1001),
    "SignPro Custom DeSign": (21246, 1121),
    "Serenity Indoor Fountains": (25234, 6359),
    "Budapest Comics": (12251, 2461),
    "Dottie's Lattes": (34427, 1293),
    "Gumball Utopia": (13271, 3420),
    "Your Uncle's Basement": (11119, 8201),
    "Carnivore Loan Specialists": (31000, 50312),
    "Harry's Steakhouse": (46791, 1327),
    "Two Guys Paper Supplies": (76201, 1120),
    "Dragon Pizza": (10201, 2000),
    "Us Three: The U2 Fan Store": (10201, 1200),
    "Jimmy's Buffett": (10027, 3201),
    "Franz Equipment Rentals": (20201, 2201),
    "Nigel's Board Games": (62012, 2013),
    "Destructor's Den": (79915, 5203),
    "Hook Me Up": (56503, 1940),
    "Slam Dunk": (61239, 5820),
    "Ben's Hungarian-Asian Fusion": (68303, 2011),
    "PleaseBurgers": (20132, 1402),
    "Reagan's Vegan": (20201, 6201),
    "FreshCart Store-to-Table": (83533, 2751),
}

ratios = {vendor: revenue / rent for vendor, (revenue, rent) in vendor_data.items()}
print(ratios)
