
def convert_time_24_to_12(time_24):
    # Split the input time string into hour and minute parts
    hour, minute = map(int, time_24.split(':'))

    # Determine AM or PM and convert the hour
    if hour == 0:
        hour_12 = 12
        period = 'AM'
    elif 1 <= hour <= 11:
        hour_12 = hour
        period = 'AM'
    elif hour == 12:
        hour_12 = 12
        period = 'PM'
    else:
        hour_12 = hour - 12
        period = 'PM'

    # Form the final 12-hour format time string
    time_12 = f"{hour_12}:{minute:02} {period}"

    return time_12

# Example usage
time_24 = '14:30'
time_12 = convert_time_24_to_12(time_24)
print(time_12)  # Output: 2:30 PM
