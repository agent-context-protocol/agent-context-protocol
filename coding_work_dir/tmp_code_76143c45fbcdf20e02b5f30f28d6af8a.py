
import numpy as np

# Points allocation per problem type
multiply_fractions_points = 10
add_subtract_fractions_points = 5
convert_improper_to_mixed_points = 20
convert_mixed_to_improper_points = 15
bonus_points = 5

# Correct problems
correct_problems = [1, 4, 5, 7, 8, 9, 10]

# Calculating total score based on the given problem types
total_score = (
    2 * multiply_fractions_points +     # Two problems of multiplication (1, 7)
    2 * add_subtract_fractions_points + # Two problems of addition/subtraction (5, 9)
    1 * convert_improper_to_mixed_points + # One problem of converting improper to mixed (4)
    2 * convert_mixed_to_improper_points + # Two problems of converting mixed to improper (8, 10)
    bonus_points                         # Bonus points
)

print(total_score)
