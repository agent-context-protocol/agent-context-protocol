
import numpy as np

date_strings = [
    'Fire and Blood: Start Date - 2022-01-01, End Date - 2022-02-14',
    'Song of Solomon: Start Date - 2022-02-15, End Date - 2022-04-04',
    'The Lost Symbol: Start Date - 2022-04-05, End Date - 2022-06-10',
    '2001: A Space Odyssey: Start Date - 2022-06-11, End Date - 2022-07-04',
    'American Gods: Start Date - 2022-07-05, End Date - 2022-08-24',
    'Out of the Silent Planet: Start Date - 2022-08-25, End Date - 2022-09-30',
    'The Andromeda Strain: Start Date - 2022-10-01, End Date - 2022-10-31',
    'Brave New World: Start Date - 2022-11-01, End Date - 2022-11-20',
    'Silence: Start Date - 2022-11-21, End Date - 2022-12-24',
    'The Shining: Start Date - 2022-12-25, End Date - 2022-12-31'
]

days_between = []
for entry in date_strings:
    start_str = entry.split('- ')[1].split(',')[0].strip()
    end_str = entry.split('- ')[2].strip()
    start_date = np.datetime64(start_str)
    end_date = np.datetime64(end_str)
    days_diff = (end_date - start_date).astype(int)
    days_between.append(days_diff)

print(days_between)
