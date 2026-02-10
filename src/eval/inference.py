import json
import argparse
import os
import logging
import asyncio
import sys
from typing import Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.models.load_model import LLMPipeline

PROMPT_MAP = {
    "vanilla": "src/prompts/vanilla.txt",
    "cot_lc": "src/prompts/cot_lawchain.txt",
    "cot_vanilla": "src/prompts/cot_vanilla.txt"
}


def load_prompt(mode: str, custom_path: Optional[str] = None) -> str:
    if custom_path is not None:
        with open(custom_path, 'r', encoding='utf-8') as f:
            return f.read()
    path = PROMPT_MAP.get(mode)
    if not path or not os.path.exists(path):
        raise ValueError(f"Prompt file doesn't exist: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def chunks(lst, batch_size):
    for i in range(0, len(lst), batch_size):
        yield lst[i:i + batch_size]



async def run_batch_inference(pipeline, test_prompt, json_path, output_path, batch_size=10):
    existing_outputs = {}
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f_out:
                existing_list = json.load(f_out)
                existing_outputs = {item["uniqid"]: item for item in existing_list}
                print(f"Skip {len(existing_outputs)} pieces of data.")
        except json.JSONDecodeError:
            backup_path = output_path + ".backup"
            logging.warning(f"Failed to parse output file. Backed up to: {backup_path}")
            os.rename(output_path, backup_path)

    deduplicated = list(existing_outputs.values())
    uniqid_set = set(existing_outputs.keys())

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        data = [item for item in data if item["uniqid"] not in existing_outputs]

    test_result = []
    total_batches = (len(data) + batch_size - 1) // batch_size
    batch_counter = 1

    for batch in chunks(data, batch_size):
        print(f"Processing batch {batch_counter}/{total_batches}...")
        inputs = []
        for item in batch:
            inputs.append(test_prompt.format(item['input']))


        responses = await pipeline.call_batch_async(inputs)

        batch_result = []
        for i, item in enumerate(batch):
            result_text = responses[i]


            if isinstance(result_text, Exception):
                logging.error(f"Error for uniqid {item['uniqid']}: {str(result_text)}")
                continue

            result_text_str = str(result_text).strip()

            if result_text_str == "Request failed" or not result_text_str:
                logging.warning(f"Skipping failed or empty response for uniqid: {item['uniqid']}")
                continue

            result_item = {
                "uniqid": item["uniqid"],
                "output": result_text_str,
            }
            test_result.append(result_item)
            batch_result.append(result_item)

        print(f"Batch {batch_counter} completed\n")
        batch_counter += 1

        for item in batch_result:
            if item["uniqid"] not in uniqid_set:
                uniqid_set.add(item["uniqid"])
                deduplicated.append(item)

        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(deduplicated, f, ensure_ascii=False, indent=2)

    print(f"All batches processed. Results saved to: {output_path}")
    return test_result



async def main():
    parser = argparse.ArgumentParser(description="Unified inference main script")
    parser.add_argument('--mode', type=str, choices=['vanilla', 'cot_lc', 'cot_vanilla'], required=True)
    parser.add_argument('--prompt_path', type=str, default=None)
    parser.add_argument('--model', type=str, required=True)
    parser.add_argument('--input_path', type=str, required=True)
    parser.add_argument('--output_path', type=str)
    parser.add_argument('--batch_size', type=int, default=16)
    parser.add_argument('--log_path', type=str, default="inference.log")
    parser.add_argument('--api', type=str, default="true")
    parser.add_argument('--env', type=str, default=".env")
    parser.add_argument('--enable_thinking', action='store_true')
    parser.add_argument('--streaming', action='store_true')
    parser.add_argument('--temperature', default=0.7, type=float)
    args = parser.parse_args()


    model_name = args.model.split("/")[-1]
    if args.enable_thinking:
        model_name += "_enable_thinking"
    mode_suffix = {"vanilla": "vanilla", "cot_lc": "cot_lawchain", "cot_vanilla": "cot_vanilla"}.get(args.mode,
                                                                                                     args.mode)
    args.output_path = f"inference_result/{model_name}_{mode_suffix}_output.json"

    if not os.path.exists("inference_result"):
        os.makedirs("inference_result")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(args.log_path, encoding='utf-8'), logging.StreamHandler()]
    )

    prompt = load_prompt(args.mode, args.prompt_path)


    pipeline = LLMPipeline(
        model=args.model,
        opensource=args.api.lower() != "true",
        env_path=args.env,
        cot=args.enable_thinking,
        streaming=args.streaming,
        temperature=args.temperature
    )


    await run_batch_inference(
        pipeline=pipeline,
        test_prompt=prompt,
        json_path=args.input_path,
        output_path=args.output_path,
        batch_size=args.batch_size
    )


if __name__ == "__main__":

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")