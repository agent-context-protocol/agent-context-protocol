
import numpy as np

def calculate_checksum(data):
    n_rows, n_cols = data.shape
    weights = np.arange(1, 10)  # Weights from 1 to 9
    indices = list(range(3, n_cols - 1))  # Valid column indices for transposition
    
    for row in data:
        for col in indices:
            for unknown_weight in weights:
                # Calculate checksums excluding transposed columns
                checksum_original = np.sum(weights * row)
                
                # Transpose adjacent columns
                row[col], row[col + 1] = row[col + 1], row[col]
                
                checksum_transposed = np.sum(weights * row)
                
                # Compare checksums
                if checksum_original != checksum_transposed:
                    print(f"Row: {row}, Unknown weight: {unknown_weight}, Error columns: ({col}, {col + 1})")
                
                # Revert transposition
                row[col], row[col + 1] = row[col + 1], row[col]

# Example data
data = np.array([
    [3, 1, 5, 7, 2, 8, 6, 4, 9],
    [4, 3, 2, 1, 7, 5, 8, 9, 6],
    [5, 9, 8, 6, 3, 2, 7, 1, 4]
])

calculate_checksum(data)
