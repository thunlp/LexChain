import argparse
import json
import os
import asyncio
import re
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import logging
from src.models.load_model import LLMPipeline

scoring_prompt = """
下面是对于一个法律案例分析问题一个AI助手回答和标准答案。请你以公正的评判者的身份，评估AI回答与标准答案的对齐度。

我们会给您需要你评估的AI助手回答和标准答案。你需要按照遵守以下的流程：
1. 根据不同字段对AI助手的答案进行评价，给出每个维度中的分数
2. 遵守下面的评分规则，对每个维度进行评价和解释
3. 你的打分需要尽可能严格，打分必须是整数。
4. 如果模型回答不完整，则打0分。

对于每个维度的打分细则如下：

1.原告（0~2 分）

注意事项：
	1.	若标准答案中使用“等”字样省略部分主体，模型如列举更多原告，只要无明显错误且未遗漏标准答案中的原告，不扣分。
	2.	模型使用简称（如“张某”替代“张三”），若表达清晰且语义明确，亦不扣分。

评分标准：
• 2 分：准确识别全部原告，名称无误，描述清晰；
• 1 分：仅识别部分原告，或存在遗漏；
• 0 分：未提及原告或识别错误（如张冠李戴）。

2.被告（0~2 分）

注意事项：
	1.	若标准答案中使用“等”字样省略部分主体，模型如列举更多被告，只要无明显错误且未遗漏标准答案中的被告，不扣分。
	2.	模型使用简称（如“李某”代替“李四”），若表达清晰且语义明确，亦不扣分。

评分标准：
• 2 分：准确识别全部被告，名称无误，描述清晰；
• 1 分：仅识别部分被告，或存在遗漏；
• 0 分：未提及被告或识别错误（如误将被告识为原告等）。

3. 纠纷类型（0~1 分）
评分标准：
 • 1 分：准确判断纠纷类型，模型回答的纠纷类型与标准答案完全一致。
 • 0 分：错误或未提及纠纷类型。

4. 法律依据（0~2 分）
评分标准：
 • 2 分：正确引用所有相关法律条文。
 • 1 分：正确引用部分相关法律条文，但存在遗漏。
 • 0 分：未提供任何法律依据或依据完全错误。


5. 责任划分（0~2 分）
说明：责任为“0”或“无”视为不承担责任，两者等价处理。评分依据包括责任主体、责任比例、承担责任方式及履行方式的准确性和完整性。
评分标准：
2 分（完全正确）：
- 所有责任主体明确，命名准确；
- 各方“承担责任比例”与标准答案完全一致；
- “承担责任方式”分类全面准确（如赔偿损失、相关鉴定费等），无遗漏；
- 各项“履行方式”描述清晰、具体，金额或履行内容与标准答案一致；
- 推理过程与法律依据合理、完整，基本符合标准答案逻辑及适用条款。
1 分（部分正确）：
- 责任主体识别正确，但“承担责任比例”与标准答案存在轻微偏差（±10%以内）；
- 或“承担责任方式”分类不全（漏项）、履行方式模糊但仍体现部分正确逻辑；
- 或责任比例和承担方式基本正确，但推理过程或法律依据描述不准确或不完整；
- 或只覆盖了部分责任主体，另一方完全缺失。
0 分（完全错误或缺失）：
- 责任主体识别错误或遗漏关键主体；
- 责任比例与标准答案严重不符；
- 承担责任方式及履行方式缺失、混乱或完全错误；
- 推理过程逻辑错误，法律依据不相关或完全缺失。


6. 原告损失总额（0~2 分）
注意：1.如模型回复未说明具体金额，但标准答案同样未具体说明金额，则不算错
2. 金额为“0”和金额为无均指无需赔偿，打分时这两种表述等价处理。
评分标准：
 • 2 分：准确列明原告的损失金额，单位和数值无误，与标准答案完全一致。
 • 1 分：金额略有偏差，单位或表述存在轻微问题，但和标准答案近似。
 • 0 分：未提及原告损失金额或完全错误。

7. 判决结果（各 0~1 小数评分）

请分别对 AI 回答的 精准率和 召回率进行评分，定义如下：
	•	精准率= 模型回答中正确条目数 ÷ 回答的总条目数
	•	召回率 = 模型回答中正确条目数 ÷ 标准答案的总条目数

评分理由格式要求（reason 字段）：
	•	对于精准率：
模型回答中正确条目数为 a，总条目数为 b，精准率为 a/b
	•	对于召回率：
模型回答中正确条目数为 a，标准答案条目总数为 c，召回率为 a/c


评分结果为 0 到 1 之间的小数（保留两位小数），不作整数化处理。

评分说明：
- 每条判决内容需与标准答案在责任主体、赔偿内容、金额、履行期限等完全方面一致；
- 金额误差、主体错误或漏项均视为该条不正确；
- 条目顺序不作严格要求，但内容需明确对应；

返回JSON格式为：
{
  "原告": {
    "reason": <分析和评价>,
    "score": <分数>
  },
  "被告": {
    "reason": <分析和评价>,
    "score": <分数>
  },
  "纠纷类型": {
    "reason": <分析和评价>,
    "score": <分数>
  },
  "法律依据": {
    "reason": <分析和评价>,
    "score": <分数>
  },
  "责任划分": {
    "reason": <分析和评价>,
    "score": <分数>
  },
  "原告损失总额": {
    "reason": <分析和评价>,
    "score": <分数>
  },
  "判决结果": {
    "precision": {
      "reason": <模型回答中正确条目数为 a，回答总条目数为 b，精准率为 a/b。其中判定为正确的条目如下：
                    1. 回答条目："..."，匹配标准答案条目："..."
                    2. 回答条目："..."，匹配标准答案条目："..."
                    ……
                    >,
      "score": <精准率得分>
    },
    "recall": {
      "reason": <模型回答中正确条目数为 a，标准答案条目总数为 c，召回率为 a/c。其中判定为正确的条目如下：
                    1. 回答条目："..."，匹配标准答案条目："..."
                    2. 回答条目："..."，匹配标准答案条目："..."
                    ……
                    >,
      "score": <召回率得分>
    }
  }
}

***


"""


def chunks(lst, batch_size):
    for i in range(0, len(lst), batch_size):
        yield lst[i:i + batch_size]


def extract_json_from_markdown(s):
    match = re.search(r"```json\s*(\{.*?\})\s*```", s, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return s


def prepare_inputs(data, scoring_prompt,reference):
    inputs = []
    reference_dict={item['uniqid']:item['reference']for item in reference}
    for item in data:
        uniqid=item.get('uniqid')
        refr=reference_dict[uniqid]
        inp = f"标准回答{refr}模型回答{str(item['output'])}"
        inputs.append(f"{scoring_prompt}\n{inp}")
    return inputs


def run_batch_scoring(reference_path, pipeline, scoring_prompt, input_path, output_path, batch_size=8):
    REQUIRED_KEYS = ["原告", "被告", "纠纷类型", "法律依据", "责任划分", "原告损失总额", "判决结果"]

    existing_outputs = {}
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f_out:
            try:
                existing_list = json.load(f_out)
                existing_outputs = {str(item["uniqid"]): item for item in existing_list}
            except json.JSONDecodeError:
                logging.warning("Output file exists but is not decodable. It will be overwritten.")

    deduplicated = list(existing_outputs.values())
    uniqid_set = set(existing_outputs.keys())

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        data = [item for item in data if str(item["uniqid"]) not in existing_outputs]

    with open(reference_path, 'r', encoding='utf-8') as f:
        reference = json.load(f)

    all_results = []
    total_batches = (len(data) + batch_size - 1) // batch_size

    for batch_idx, batch in enumerate(chunks(data, batch_size), start=1):
        print(f"Scoring batch {batch_idx}/{total_batches}...")
        inputs = prepare_inputs(batch, scoring_prompt, reference)
        responses = asyncio.run(pipeline.call_batch_async(inputs))
        batch_results = []

        for i, response in enumerate(responses):
            current_uniqid = str(batch[i]["uniqid"])

            item = {
                "uniqid": batch[i]["uniqid"],
                "pred": batch[i].get("output", batch[i].get("pred", ""))
            }

            if not response or not response.strip():
                logging.warning(f"Empty response for uniqid = {current_uniqid}")
                continue
            elif response.strip() == "Request failed":
                logging.error(f"Request failed for uniqid = {current_uniqid}")
                continue

            cleaned = extract_json_from_markdown(response)
            try:
                score = json.loads(cleaned)

                missing_keys = [k for k in REQUIRED_KEYS if k not in score]
                if missing_keys:
                    logging.warning(f"Uniqid {current_uniqid} skipped: Missing fields {missing_keys}")
                    continue

                if not isinstance(score["判决结果"], dict) or \
                        "precision" not in score["判决结果"] or \
                        "recall" not in score["判决结果"]:
                    logging.warning(f"Uniqid {current_uniqid} skipped: Invalid '判决结果' format")
                    continue

                item["score"] = score

            except json.JSONDecodeError:
                logging.error(f"JSON Decode Error for uniqid {current_uniqid}. Content snippet: {repr(response[:100])}")
                continue

            all_results.append(item)
            batch_results.append(item)


        for item in batch_results:
            if str(item["uniqid"]) not in uniqid_set:
                uniqid_set.add(str(item["uniqid"]))
                deduplicated.append(item)

        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(deduplicated, f, ensure_ascii=False, indent=2)

        print(f"Batch {batch_idx} completed\n")

    print(f"Batch scoring completed. Results saved to: {output_path}")
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch scoring script")
    parser.add_argument(
        '--input_dir',
        type=str,
        default="../inference_result",
        help="Directory path of input files"
    )

    parser.add_argument(
        '--reference_path',
        type=str,
        default="../data/test_reference.json",
        help="Path of reference file"
    )

    parser.add_argument(
        '--batch_size',
        type=int,
        default=16,
        help="Batch size"
    )

    parser.add_argument(
        '--log_path',
        type=str,
        default="../log/scoring.log",
        help="Path to log file"
    )

    parser.add_argument(
        '--model',
        type=str,
        default="gpt-4o-2024-05-13",
        help="LLM for scoring"
    )

    parser.add_argument(
        '--api',
        type=str,
        default='true',
        help="Set to 'true' to use API, 'false' to use local model"
    )

    args = parser.parse_args()
    os.makedirs(os.path.dirname(args.log_path), exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(args.log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)

    pipeline = LLMPipeline(model=args.model, opensource=args.api.lower() == "false", env_path=".env")

    for file_name in os.listdir(args.input_dir):
        if file_name.endswith(".json"):
            input_path = os.path.join(args.input_dir, file_name)
            model_name = file_name.replace("_output_sampled.json", "").replace("_output.json", "")
            print(model_name)
            output_path = os.path.join("./scoring_result", f"{model_name}_result.json")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            run_batch_scoring(
                pipeline=pipeline,
                scoring_prompt=scoring_prompt,
                input_path=input_path,
                output_path=output_path,
                batch_size=args.batch_size,
                reference_path=args.reference_path
            )
