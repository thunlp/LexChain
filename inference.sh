#!/bin/bash


MODEL="deepseek-v3.2"           # model path
MODE="vanilla"  # mode: vanilla, cot_lc, cot_vanilla
TEMPERATURE=0.7
INPUT="./data/test_input.json"   # input file
BATCH=8                      # batch size
IS_API="true"                   # API (true/false)
LOG_FILE="logs/inference.log"   # log path


# If you need to use the Qwen thinking mode, uncomment the following line

# THINK_FLAG="--enable_thinking"

# If you need to stream output, uncomment the following line
# STREAM_FLAG="--streaming"

# Create the necessary directories
mkdir -p inference_result
mkdir -p $(dirname "$LOG_FILE")

echo "---------------------------------------"
echo "Start the inference..."
echo "Model: $MODEL"
echo "Mode: $MODE"
echo "Batch: $BATCH"
echo "---------------------------------------"


python3 -u src/eval/inference.py \
    --model "$MODEL" \
    --mode "$MODE" \
    --input_path "$INPUT" \
    --batch_size "$BATCH" \
    --api "$IS_API" \
    --log_path "$LOG_FILE" \
    --temperature "$TEMPERATURE" \
    $THINK_FLAG \
    $STREAM_FLAG

echo "---------------------------------------"
echo "Task Completed"