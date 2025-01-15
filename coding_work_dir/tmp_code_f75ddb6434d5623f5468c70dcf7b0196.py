
import json

# Sample JSON data (as a string)
json_data = '''
[
    {"name": "Alice", "qualifications": ["Bachelors", "Masters"]},
    {"name": "Bob", "qualifications": ["Bachelors"]},
    {"name": "Charlie", "qualifications": []},
    {"name": "David", "qualifications": ["Bachelors", "Masters", "PhD"]},
    {"name": "Eve", "qualifications": ["Masters"]}
]
'''

# Converting JSON string to Python list
applicants = json.loads(json_data)

# Count applicants missing only one qualification
count = sum(1 for applicant in applicants if len(applicant["qualifications"]) == 1)

print(count)
