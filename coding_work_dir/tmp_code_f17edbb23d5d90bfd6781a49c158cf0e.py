
addresses = ['Michael Scott - 8602 Begonia Drive', 'Pam Beasley - 6232 Plumeria Lane', 'Creed Bratton - 2024 Orchid Avenue', 'William Schneider - 2024 Orchid Avenue']

def is_even_address(address):
    parts = address.split(' ')
    for part in parts:
        if part.isdigit() and int(part) % 2 == 0:
            return True
    return False

even_address_count = sum(1 for address in addresses if is_even_address(address))

print(even_address_count)
