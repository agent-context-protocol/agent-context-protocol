
import numpy as np

def shoelace_polygon_area(coords):
    n = len(coords)
    area = 0
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    area = abs(area) / 2.0
    return area

vertices = [(0, 0), (1, 0), (1, 6), (5, 6), (5, 10), (13, 10), (13, 4), (7, 4), (7, 2.5), (13, 2.5), (13, 0), (1, 0)]

area = shoelace_polygon_area(vertices)
print(area)
