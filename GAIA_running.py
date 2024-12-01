from datasets import load_dataset
dataset = load_dataset("gaia-benchmark/GAIA", '2023_level3', token="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")

SPLIT = 'validation'
index = 21
raw_question = dataset[SPLIT][index]['Question']
file_name = dataset[SPLIT][index]['file_name']

if file_name:
    question = f"{raw_question}\nAttachment: file:///Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_GAIA_Simple/GAIA/2023/{SPLIT}/{file_name}"
else:
    question = f"{raw_question}"

print("question: ",question)