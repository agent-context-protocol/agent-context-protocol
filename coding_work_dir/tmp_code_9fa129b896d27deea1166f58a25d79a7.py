
import numpy as np

ingredients1 = [
    {'ingredient': 'Cinnamon stick', 'amount': 3.0, 'unit': 'g'},
    {'ingredient': 'Cumin seeds', 'amount': 4.0, 'unit': 'g'},
    {'ingredient': 'Coriander seeds', 'amount': 4.0, 'unit': 'g'},
    {'ingredient': 'Knorr Aromat Original', 'amount': 3.0, 'unit': 'g'},
    {'ingredient': 'Robertsons Black Pepper', 'amount': 1.0, 'unit': 'g'},
    {'ingredient': 'Robertsons Turmeric', 'amount': 4.0, 'unit': 'g'},
    {'ingredient': 'Knorr Professional Beef Stock Granules', 'amount': 20.0, 'unit': 'g'},
    {'ingredient': 'Onions', 'amount': 200.0, 'unit': 'g'},
    {'ingredient': 'Green chillies', 'amount': 5.0, 'unit': 'g'},
    {'ingredient': 'Ginger', 'amount': 4.0, 'unit': 'g'},
    {'ingredient': 'Crushed garlic', 'amount': 4.0, 'unit': 'g'},
    {'ingredient': 'Knorr Professional Tomato Pronto', 'amount': 250.0, 'unit': 'g'},
    {'ingredient': 'Robertsons Peri-Peri Spice', 'amount': 3.0, 'unit': 'g'}
]

ingredients2 = [
    {'ingredient': 'Water', 'amount': 1300.0, 'unit': 'g'},
    {'ingredient': 'Sunflower oil', 'amount': 55.2, 'unit': 'g'}
]

total_weight = sum(item['amount'] for item in ingredients1 + ingredients2)
print(total_weight)
