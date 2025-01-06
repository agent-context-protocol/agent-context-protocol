from datasets import load_dataset
from GAIA.score import question_scorer
import asyncio
import os
import csv

dataset = load_dataset("gaia-benchmark/GAIA", '2023_level3', token="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")

SPLIT = 'validation'
num_samples_eval = 26

raw_questions = [dataset[SPLIT][i]['Question'] for i in range(num_samples_eval)]
file_names = [dataset[SPLIT][i]['file_name'] for i in range(num_samples_eval)]
final_answers = [dataset[SPLIT][i]['Final answer'] for i in range(num_samples_eval)]

questions_with_attachments = [
    f"{raw_question}\nAttachment: file:///Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_GAIA_Simple/GAIA/2023/{SPLIT}/{file_name}" 
    if file_name else raw_question 
    for raw_question, file_name in zip(raw_questions, file_names)
]

# # Calling the orchestrator for getting answers
# answers = []
# for i, query in enumerate(questions_with_attachments):
#     print("###########################")
#     print("###########################")
#     print(f"\nQuestion {i+1}\n")
#     answers.append(asyncio.run(run_orch_func(query)))


# Level 2
# Instead of hardcoding answers, read them from CSV using QuestionIndex (starting at 1).
answers_dict = {}
with open('answers_level3_hf.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Convert QuestionIndex to int
        question_index = int(row['QuestionIndex'])
        # Use question_index as key to store the answer
        answers_dict[question_index] = row['Answer']

# Build the answers list, filling in "None" if an answer is missing
answers = [answers_dict.get(i+1, "None") for i in range(num_samples_eval)]

# Getting the score
print("###########################")
print("###########################")
print("Scoring Now\n")
scores = [question_scorer(answer, gt_answer) for answer, gt_answer in zip(answers, final_answers)]

print(f"Final score: {sum(scores)}/{len(scores)} = {sum(scores)/len(scores):.2f}")