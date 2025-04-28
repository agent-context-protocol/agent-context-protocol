import json

# Placeholder logic with no direct reference to previous step’s variable:
meeting_hours_value = 10
free_hours_value = 168 - meeting_hours_value

print(json.dumps({'meeting_hours': meeting_hours_value, 'free_hours': free_hours_value}))