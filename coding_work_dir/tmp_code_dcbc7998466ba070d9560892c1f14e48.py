
import sympy as sp

# Define the variable and function
x = sp.symbols('x')
A = sp.symbols('A', constant=True)
f = A * x**2

# Calculate the derivative
f_derivative = sp.diff(f, x)

# Print the result
print(f_derivative)
