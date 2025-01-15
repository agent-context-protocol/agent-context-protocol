
addresses = [8602, 6232, 2024]
even_count = sum(1 for address in addresses if address % 2 == 0)
print(even_count)
