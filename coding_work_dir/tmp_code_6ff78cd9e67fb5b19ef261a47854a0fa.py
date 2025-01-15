
import numpy as np

def calculate_expression(expression):
    try:
        return eval(expression)
    except Exception as e:
        return str(e)

expression = "8827"
result = calculate_expression(expression)
print(result)
