import os
import json
import pandas as pd
import argparse
import logging


def compute_total_scores(input_path):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    keys = ["原告", "被告", "纠纷类型", "法律依据", "责任划分", "原告损失总额", "判决结果"]

    # Stores the sum of actual scores
    result = {k: 0.0 for k in keys}
    # Counts the number of valid occurrences for each dimension
    counts = {k: 0 for k in keys}

    for entry in data:
        if not isinstance(entry, dict) or "score" not in entry:
            continue

        score_field = entry["score"]
        if not isinstance(score_field, dict):
            continue

        for k in keys:
            if k in score_field:
                counts[k] += 1
                if k != "判决结果":
                    result[k] += score_field.get(k, {}).get("score", 0)
                else:
                    metrics = score_field[k]
                    acc = metrics.get("precision", {}).get("score", 0)
                    rec = metrics.get("recall", {}).get("score", 0)
                    if (acc + rec) > 0:
                        f1 = 2 * acc * rec / (acc + rec)
                        result[k] += f1

    # Calculate final percentage scores
    final_output = {}
    total_actual = 0.0
    total_possible = 0.0

    for k in keys:
        # Weighting: Standard fields are 2 points max, Dispute/Judgment are 1 point max
        max_val = 1 if k in ["纠纷类型", "判决结果"] else 2
        possible_score = counts[k] * max_val

        # Calculate individual dimension percentage
        if possible_score > 0:
            final_output[k] = round(result[k] * 100 / possible_score, 2)
        else:
            final_output[k] = 0.0

        # Accumulate for global Micro-average Overall score
        total_actual += result[k]
        total_possible += possible_score

    # Calculate Overall score (Micro-average)
    final_output["总分"] = round(total_actual * 100 / total_possible, 2) if total_possible > 0 else 0.0

    return final_output



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', type=str, default="../../scoring_result", help='Input directory')
    args = parser.parse_args()

    scores_summary = {}

    if os.path.exists(args.input_dir):
        for filename in os.listdir(args.input_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(args.input_dir, filename)
                model_name = filename.replace("_result.json", "")
                try:
                    scores_summary[model_name] = compute_total_scores(file_path)
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
    else:
        print(f"Directory not found: {args.input_dir}")

    # Initialize DataFrame from results dictionary
    df = pd.DataFrame.from_dict(scores_summary, orient='index')

    # Set index name before resetting to ensure the column name becomes "Result file name"
    df.index.name = "Result_file"
    df = df.reset_index()

    # Rename Chinese keys to English for the final Excel report
    rename_dict = {
        "原告": "Plaintiff",
        "被告": "Defendant",
        "纠纷类型": "Dispute",
        "法律依据": "Statute",
        "责任划分": "Liability",
        "原告损失总额": "Damages",
        "判决结果": "Judgment",
        "总分": "Overall"
    }
    df = df.rename(columns=rename_dict)


    df.insert(1, "Base_model", df["Result_file"].str.extract(r"^(.*?)(?:_|$)"))

    # Sort results by base model name (alphabetical) and then by Overall score (descending)
    df = df.sort_values(by=["Base_model", "Overall"], ascending=[True, False]).set_index("Result_file")

    # Export to Excel using XlsxWriter engine
    output_excel_path = os.path.join(args.input_dir, "scores_summary.xlsx")
    try:
        df.to_excel(output_excel_path, sheet_name='Scores', engine='xlsxwriter')
        print(f"Summary successfully saved to: {output_excel_path}")
    except Exception as e:
        print(f"Failed to save Excel file: {e}")