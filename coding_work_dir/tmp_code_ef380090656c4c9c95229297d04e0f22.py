
import numpy as np
import pandas as pd

# Sample DataFrame representing the spreadsheet
data = {
    'Book': ['Book1', 'Book2', 'Book3'],
    'Start_Date': ['2023-01-01', '2023-02-01', '2023-03-01'],
    'End_Date': ['2023-01-05', '2023-02-10', '2023-03-06']
}

df = pd.DataFrame(data)

# Convert the date strings to datetime objects
df['Start_Date'] = pd.to_datetime(df['Start_Date'])
df['End_Date'] = pd.to_datetime(df['End_Date'])

# Calculate the number of days between Start_Date and End_Date
df['Num_Days'] = (df['End_Date'] - df['Start_Date']).dt.days

print(df[['Book', 'Num_Days']])
