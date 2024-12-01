from run_orchestrator_GAIA import run_orch_func
from datasets import load_dataset
from GAIA.score import question_scorer
import asyncio
import os


dataset = load_dataset("gaia-benchmark/GAIA", '2023_level3', token="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")

SPLIT = 'validation'
num_samples_eval = 26
# raw_question = dataset[SPLIT][5]['Question']
# file_name = dataset[SPLIT][5]['file_name']

raw_questions = [dataset[SPLIT][i]['Question'] for i in range(num_samples_eval)]
file_names = [dataset[SPLIT][i]['file_name'] for i in range(num_samples_eval)]
final_answers = [dataset[SPLIT][i]['Final answer'] for i in range(num_samples_eval)]

# print("file_names : ",file_names)

questions_with_attachments = [
    f"{raw_question}\nAttachment: file:///Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_GAIA_Simple/GAIA/2023/{SPLIT}/{file_name}" 
    if file_name else raw_question 
    for raw_question, file_name in zip(raw_questions, file_names)
]

# print("\nquestions_with_attachments: ",questions_with_attachments)

# # Calling the orchestrator for getting answers
# answers = []
# for i, query in enumerate(questions_with_attachments):
#     print("###########################")
#     print("###########################")
#     print(f"\nQuestion {i+1}\n")
#     answers.append(asyncio.run(run_orch_func(query)))

# # Level 1
# answers = ["17", "3", "1", "0.1777", "3", "Impact of COVID induced economic uncertainty on small businesses in Bharuch", "THE CASTLE", "Lucy", "Right", "FAILED", "(¬A → B) ↔ (A ∨ ¬B)", "4", "fluffy", "FAILED", "FAILED"]
# # Level 2
# answers = ["egalitarian", "34689", "41", "Remove r", "Time-Parking 2: Parallel Universe", "10", "12/15/11", "FAILED", "12345;67890", "Jamshid Amouzegar", "This Panel Was Dropped", "6", "16.700", "Indonesia, Myanmar", "scribal"]
# Level 3
answers = ["FAILED", "FAILED", "Jerome Wiesner", "FAILED", "160", "Birds, Mammals", "FAILED", "FAILED", "FAILED", "312", "FAILED", "0.0424", "8, 1, 3, 1, 8, 9", "0.00003", "12", "FAILED", "FAILED", "Pears, lemons", "8", "Out of the Silent Planet", "FAILED", "FAILED", "Demon Hunter, Druid, Mage, Paladin, Priest", "FAILED", "FAILED", "White;601"]

# Getting the score
print("###########################")
print("###########################")
print("Scoring Now\n")
scores = [question_scorer(answer, gt_answer) for answer, gt_answer in zip(answers, final_answers)]

print(f"Final score: {sum(scores)}/{len(scores)} = {sum(scores)/len(scores):.2f}")