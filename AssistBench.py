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
    csv_filename = "answers_val_assist.csv"

    # ----------------------------------------------------
    # 1. Check if answers.csv exists; if not, create & write header.
    #    If it exists, figure out how many rows we already have.
    # ----------------------------------------------------
    if not os.path.exists(csv_filename):
        print(f"Creating new file {csv_filename} with header...")
        with open(csv_filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["QuestionIndex", "Query", "Answer", "GT_Answer"])
        processed_count = 0
    else:
        # Count how many data rows are already in the CSV (excluding header)
        with open(csv_filename, "r", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            rows = list(reader)
            processed_count = len(rows)
        print(f"Found existing {csv_filename} with {processed_count} rows of answers. "
              f"Will skip those and continue from question {processed_count + 1}.\n")

    # ----------------------------------------------------
    # 2. Load dataset
    # ----------------------------------------------------
    dataset = load_dataset("AssistantBench/AssistantBench", split = 'validation',
                           token="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")
    # SPLIT = 'validation'
    num_samples_eval = 33

    print("\n dataset:", dataset, "\n")

    raw_questions = [dataset[i]['task'] for i in range(num_samples_eval)]
    final_answers = [dataset[i]['answer'] for i in range(num_samples_eval)]

    # print("\nraw_questions:", raw_questions, "\n")
    # print("\nfinal_answers:", final_answers, "\n")

    # ----------------------------------------------------
    # 3. Process only the *unprocessed* questions
    # ----------------------------------------------------
    # We'll store answers for *all* questions here, but only fill
    # in the new ones after processed_count.
    answers = [None] * num_samples_eval

    for i, query in enumerate(raw_questions):
        # If this question was processed in a previous run, skip.
        # Remember: processed_count tracks how many rows are in CSV
        #           i is zero-based, but CSV logs i+1 as QuestionIndex.
        # So if i < processed_count, it means i+1 <= processed_count has been done.
        if i < processed_count or i < 9:
            print(f"Skipping Question {i+1} (already in {csv_filename}).")
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


if __name__ == "__main__":
    asyncio.run(main())

