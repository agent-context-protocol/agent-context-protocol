
import json
import numpy as np

json_string = '{"0000-0003-0396-0333": 1}'
data = json.loads(json_string)
values = list(data.values())
average = np.mean(values)

print(average)
