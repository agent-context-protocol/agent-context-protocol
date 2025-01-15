
import numpy as np

# Dictionary to store the number of significant outbreaks for each year
outbreaks_data = {
    2011: {'listeria': 0, 'e_coli': 0},
    2012: {'listeria': 0, 'e_coli': 0},
    2013: {'listeria': 0, 'e_coli': 0},
    2014: {'listeria': 0, 'e_coli': 0},
    2015: {'listeria': 2, 'e_coli': 3},  # Assuming significant outbreaks in 2015 as stated
    2016: {'listeria': 0, 'e_coli': 0},
    2017: {'listeria': 0, 'e_coli': 0},
    2018: {'listeria': 0, 'e_coli': 0},
    2019: {'listeria': 0, 'e_coli': 0},
    2020: {'listeria': 0, 'e_coli': 0},
    2021: {'listeria': 0, 'e_coli': 0}
}

# Calculate total outbreaks per year
total_outbreaks_per_year = {year: sum(outbreaks.values()) for year, outbreaks in outbreaks_data.items()}

# Find the year with the maximum number of outbreaks
most_dangerous_year = max(total_outbreaks_per_year, key=total_outbreaks_per_year.get)

print(most_dangerous_year)
