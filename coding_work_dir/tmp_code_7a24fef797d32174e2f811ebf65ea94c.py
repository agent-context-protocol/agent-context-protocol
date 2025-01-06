
import numpy as np

# Sales data for Wharvton and Algrimand
sales_wharvton = np.array([1983, 2008, 2014, 2015, 2017, 2018])
sales_algrimand = np.array([1958, 1971, 1982, 1989, 1998, 2009])

# Calculate total sales
total_sales_wharvton = np.sum(sales_wharvton)
total_sales_algrimand = np.sum(sales_algrimand)

# Compare total sales and determine which city had greater total sales
if total_sales_wharvton > total_sales_algrimand:
    result = "Wharvton had greater total sales."
elif total_sales_algrimand > total_sales_wharvton:
    result = "Algrimand had greater total sales."
else:
    result = "Both cities had equal total sales."

print(total_sales_wharvton, total_sales_algrimand, result)
