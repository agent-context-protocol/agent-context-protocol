
import numpy as np

def calculate_checksum(number, weight, col1, col2):
    checksum = 0
    use_weight = False
    for index, digit in enumerate(number):
        if index < 3 or index >= len(number) - 1:
            checksum += int(digit)
        else:
            if index == col1:
                digit = number[col2]
            elif index == col2:
                digit = number[col1]
            checksum += (int(digit) * (weight if use_weight else 1))
            use_weight = not use_weight
    return checksum

def find_valid_combinations(numbers):
    numbers_array = np.array([list(num) for num in numbers])
    num_cols = numbers_array.shape[1]
    valid_combinations = []

    for weight in range(1, 10):
        for col1 in range(3, num_cols - 1):
            for col2 in range(col1 + 1, num_cols - 1):
                all_valid = True
                for number in numbers_array:
                    checksum = calculate_checksum(number, weight, col1, col2)
                    if checksum % 11 != 0:
                        all_valid = False
                        break
                if all_valid:
                    valid_combinations.append((weight, col1))

    return valid_combinations

numbers = [
    "1234567890",
    "2345678901",
    "3456789012",
    # Add more numbers as needed
]

valid_combinations = find_valid_combinations(numbers)
print(valid_combinations)
