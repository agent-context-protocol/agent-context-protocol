
import numpy as np

def valid_checksum(weight_matrix, column_indices, target_checksum):
    for row in weight_matrix:
        checksum = np.sum(row[column_indices])
        if checksum != target_checksum:
            return False
    return True

def find_combinations(weight_matrix, target_checksum):
    num_rows, num_cols = weight_matrix.shape
    valid_combinations = []

    for weight in range(num_rows):
        for num_columns in range(1, num_cols + 1):
            column_combinations = np.array(np.meshgrid(*[np.arange(num_cols) for _ in range(num_columns)])).T.reshape(-1, num_columns)
            for col_indices in column_combinations:
                if valid_checksum(weight_matrix, col_indices, target_checksum):
                    valid_combinations.append((weight, col_indices))

    return valid_combinations

weight_matrix = np.array([[3, 5, 7, 10],
                          [2, 4, 6, 8],
                          [1, 9, 11, 13]])

target_checksum = 15

combinations = find_combinations(weight_matrix, target_checksum)

print(combinations)
