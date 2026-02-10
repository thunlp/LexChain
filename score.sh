#!/bin/bash


# Model used for scoring (GPT-4o )
SCORER_MODEL="gpt-4o-2024-05-13"
# Directory containing the model outputs to be scored
INPUT_DIR="./inference_result"
# Path to the ground truth reference file
REF_PATH="./data/test_reference.json"
# Number of requests per batch
BATCH_SIZE=8
# Use API (true/false)
IS_API="true"
# Path to the log file
LOG_FILE="../log/scoring.log"

# ==========================================
# Preparation
# ==========================================
mkdir -p ./scoring_result
mkdir -p $(dirname "$LOG_FILE")

echo "---------------------------------------"
echo "Starting Automated Scoring Task..."
echo "Scoring Model: $SCORER_MODEL"
echo "Input Directory: $INPUT_DIR"
echo "Reference Path: $REF_PATH"
echo "---------------------------------------"

# ==========================================
# Execution
# ==========================================
# Ensure PYTHONPATH is set correctly if running from the root
python -u src/eval/score.py \
    --model "$SCORER_MODEL" \
    --input_dir "$INPUT_DIR" \
    --reference_path "$REF_PATH" \
    --batch_size "$BATCH_SIZE" \
    --api "$IS_API" \
    --log_path "$LOG_FILE"

echo "---------------------------------------"
echo "Scoring Task Completed!"
echo "Results saved in: ./scoring_result"