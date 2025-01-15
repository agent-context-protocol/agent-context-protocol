
import pandas as pd

# Load the CSV file
file_path = '/Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_GAIA_Simple/GAIA/2023/validation/8d46b8d6-b38a-47ff-ac74-cda14cf2d19b.csv'
data = pd.read_csv(file_path)

# Filter penguins that do not live on 'Dream' island or have a 'bill_length_mm' greater than 42
filtered_penguins = data[(data['island'] != 'Dream') | (data['bill_length_mm'] > 42)]

# Count the filtered penguins
count = len(filtered_penguins)

# Print the result
print(count)
