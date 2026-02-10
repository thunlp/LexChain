#!/bin/bash



# Update INPUT_DIR to the relative path where your .json score files are stored
INPUT_DIR="./scoring_result"
PYTHON_SCRIPT="src/eval/compute_score.py" # Update this to your actual script path




if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Directory $INPUT_DIR does not exist."
    exit 1
fi


echo "-------------------------------------------------------"
echo "Generating Score Summary..."
echo "Input Directory: $INPUT_DIR"
echo "-------------------------------------------------------"

python3 "$PYTHON_SCRIPT" --input_dir "$INPUT_DIR"

if [ $? -eq 0 ]; then
    echo "-------------------------------------------------------"
    echo "Success! Summary saved to $INPUT_DIR/scores_summary.xlsx"
else
    echo "Error: Summary generation failed."
    exit 1
fi