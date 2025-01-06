import asyncio
import csv
import os
from run_orchestrator_GAIA import run_orch_func
from datasets import load_dataset
from GAIA.score import question_scorer

async def process_query(query, timeout=900):
    """Async helper that runs `run_orch_func` with a given timeout."""
    run_counter = 0
    while run_counter < 2:
        try:
            return await asyncio.wait_for(run_orch_func(query), timeout=timeout)
        except asyncio.TimeoutError:
            print(f"Timed out.\n")
            # return "Timed out"
        except Exception as e:
            print(f"Error occurred: {e}\n")
            # return "Error Occurred"
        run_counter += 1
    
    return "FAILED"

async def main():
    # Name of the CSV file
    csv_filename = "answers_level2_hf_res.csv"

    # ----------------------------------------------------
    # 1. Check if answers.csv exists; if not, create & write header.
    #    If it exists, figure out how many rows we already have.
    # ----------------------------------------------------
    if not os.path.exists(csv_filename):
        print(f"Creating new file {csv_filename} with header...")
        with open(csv_filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["QuestionIndex", "Query", "Answer", "GT_Answer"])
        processed_count = []
    else:
        # Count how many data rows are already in the CSV (excluding header)
        with open(csv_filename, "r", newline="") as f:
            reader = csv.DictReader(f) 
            processed_count = []
            print("reader: ",reader)
            for row in reader:
                processed_count.append(row["QuestionIndex"])  # Collect values from QuestionIndex column
        print(f"Found existing {csv_filename} with {processed_count} rows of answers. ")

    # ----------------------------------------------------
    # 2. Load dataset
    # ----------------------------------------------------
    dataset = load_dataset("gaia-benchmark/GAIA", '2023_level2',
                           token="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")
    SPLIT = 'validation'
    num_samples_eval = 86

    raw_questions = [dataset[SPLIT][i]['Question'] for i in range(num_samples_eval)]
    file_names = [dataset[SPLIT][i]['file_name'] for i in range(num_samples_eval)]
    final_answers = [dataset[SPLIT][i]['Final answer'] for i in range(num_samples_eval)]

    questions_with_attachments = [
        f"{raw_question}\nAttachment: file:///Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_GAIA_Simple/GAIA/2023/{SPLIT}/{file_name}"
        if file_name else raw_question
        for raw_question, file_name in zip(raw_questions, file_names)
    ]

    # print("\nquestions_with_attachments:", questions_with_attachments, "\n")

    # ----------------------------------------------------
    # 3. Process only the *unprocessed* questions
    # ----------------------------------------------------
    # We'll store answers for *all* questions here, but only fill
    # in the new ones after processed_count.
    answers = [None] * num_samples_eval

    for i, query in enumerate(questions_with_attachments):
        # If this question was processed in a previous run, skip.
        # Remember: processed_count tracks how many rows are in CSV
        #           i is zero-based, but CSV logs i+1 as QuestionIndex.
        # So if i < processed_count, it means i+1 <= processed_count has been done.
        if str(i+1) in processed_count or i+1 == 55:
            print(f"Skipping Question {i+1} (already in {csv_filename}).")
            continue
        # if i == 1 or i == 6 or i == 3:
        #     continue
        # if query.split(".")[-1] in ["pdb", "zip", "mp3", "mpga"]:
        if query.split(".")[-1] in ["mpga", ".MOV"]:
            continue

        print("###########################")
        print("###########################")
        print(f"\nQuestion {i+1}\n")

        # Call the async function with a timeout
        answer = await process_query(query, timeout=900)
        answers[i] = answer

        # Write the answer row immediately
        with open(csv_filename, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([i+1, query, answer, final_answers[i]])

    # # ----------------------------------------------------
    # # 4. Scoring
    # #    - If you only want to score *newly* processed questions, 
    # #      skip the ones that were previously processed.
    # # ----------------------------------------------------
    # newly_processed_answers = answers[processed_count:]  # from processed_count onward
    # newly_processed_gts = final_answers[processed_count:]

    # # Filter out any None placeholders (in case something was never processed).
    # valid_pairs = [
    #     (ans, gt)
    #     for ans, gt in zip(newly_processed_answers, newly_processed_gts)
    #     if ans is not None
    # ]

    # print("###########################")
    # print("###########################")
    # if not valid_pairs:
    #     print("No new questions were processed. No new score computed.")
    # else:
    #     print("Scoring newly processed questions:\n")
    #     new_scores = [question_scorer(a, g) for a, g in valid_pairs]
    #     print(f"Score for newly processed questions: {sum(new_scores)}/{len(new_scores)} "
    #           f"= {sum(new_scores)/len(new_scores):.2f}\n")

    # # ----------------------------------------------------
    # # (Optional) If you prefer to see the *cumulative* score
    # # across all questions, you must read back all answers
    # # from answers.csv, or store them in memory from the start.
    # # For a truly cumulative approach, you'd re-read the CSV
    # # and compute the total score. Example:
    # # 
    # # with open(csv_filename, "r", newline="") as f:
    # #     reader = csv.reader(f)
    # #     next(reader)  # skip header
    # #     all_rows = list(reader)  # each row is [QuestionIndex, Query, Answer, GT_Answer]
    # # 
    # # all_scores = []
    # # for row in all_rows:
    # #     _, _, ans, gt = row
    # #     all_scores.append(question_scorer(ans, gt))
    # # print(f"Total cumulative score: {sum(all_scores)}/{len(all_scores)}")
    # # ----------------------------------------------------

if __name__ == "__main__":
    asyncio.run(main())

# from run_orchestrator_GAIA import run_orch_func
# from datasets import load_dataset
# from GAIA.score import question_scorer
# import asyncio
# import os


# dataset = load_dataset("gaia-benchmark/GAIA", '2023_level3', token="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")

# SPLIT = 'validation'
# num_samples_eval = 26
# # raw_question = dataset[SPLIT][5]['Question']
# # file_name = dataset[SPLIT][5]['file_name']

# raw_questions = [dataset[SPLIT][i]['Question'] for i in range(num_samples_eval)]
# file_names = [dataset[SPLIT][i]['file_name'] for i in range(num_samples_eval)]
# final_answers = [dataset[SPLIT][i]['Final answer'] for i in range(num_samples_eval)]

# # print("file_names : ",file_names)

# questions_with_attachments = [
#     f"{raw_question}\nAttachment: file:///Users/aarjun1/Documents/Arjun/Princeton_Work/newCode/interpreter-translator-rapid_apis_GAIA_Simple/GAIA/2023/{SPLIT}/{file_name}" 
#     if file_name else raw_question 
#     for raw_question, file_name in zip(raw_questions, file_names)
# ]

# # print("\nquestions_with_attachments: ",questions_with_attachments)

# # # Calling the orchestrator for getting answers
# # answers = []
# # for i, query in enumerate(questions_with_attachments):
# #     print("###########################")
# #     print("###########################")
# #     print(f"\nQuestion {i+1}\n")
# #     answers.append(asyncio.run(run_orch_func(query)))

# # # Level 1
# # answers = ["17", "3", "1", "0.1777", "3", "Impact of COVID induced economic uncertainty on small businesses in Bharuch", "THE CASTLE", "Lucy", "Right", "FAILED", "(¬A → B) ↔ (A ∨ ¬B)", "4", "fluffy", "FAILED", "FAILED"]
# # # Level 2
# # answers = ["egalitarian", "34689", "41", "Remove r", "Time-Parking 2: Parallel Universe", "10", "12/15/11", "FAILED", "12345;67890", "Jamshid Amouzegar", "This Panel Was Dropped", "6", "16.700", "Indonesia, Myanmar", "scribal"]
# # Level 3
# answers = ["FAILED", "FAILED", "Jerome Wiesner", "FAILED", "160", "Birds, Mammals", "FAILED", "FAILED", "FAILED", "312", "FAILED", "0.0424", "8, 1, 3, 1, 8, 9", "0.00003", "12", "FAILED", "FAILED", "Pears, lemons", "8", "Out of the Silent Planet", "FAILED", "FAILED", "Demon Hunter, Druid, Mage, Paladin, Priest", "FAILED", "FAILED", "White;601"]

# # Getting the score
# print("###########################")
# print("###########################")
# print("Scoring Now\n")
# scores = [question_scorer(answer, gt_answer) for answer, gt_answer in zip(answers, final_answers)]

# print(f"Final score: {sum(scores)}/{len(scores)} = {sum(scores)/len(scores):.2f}")
