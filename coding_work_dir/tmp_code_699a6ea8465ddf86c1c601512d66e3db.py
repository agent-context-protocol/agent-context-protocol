
import numpy as np

def calculate_isbn10_check_digit(tropicos_id):
    digits = np.array([int(d) for d in str(tropicos_id)])
    weights = np.arange(1, 10)
    checksum = np.sum(digits * weights)
    
    for check_digit in range(11):
        if (checksum + check_digit) % 11 == 0:
            return check_digit

tropicos_id = 100370510
check_digit = calculate_isbn10_check_digit(tropicos_id)
print(check_digit)
