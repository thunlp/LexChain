

<h1 align="center">LexChain: Modeling Legal Reasoning Chains for Chinese Tort Case Analysis</h1>

<p align="center">
  🌐 <a href="https://github.com/thunlp/LexChain" target="_blank">GitHub</a> • 📚 <a href="https://arxiv.org/abs/2510.17602" target="_blank">arXiv</a> • 🤗 <a href="https://huggingface.co/datasets/lexchain" target="_blank">HuggingFace</a>
</p>

---

Legal reasoning is central to legal decision-making, yet current computational methods mostly rely on oversimplified frameworks (e.g., syllogism, IRAC), often tailored to criminal law. To address this, we introduce **LexChain**, a legally informed, structured reasoning framework that explicitly models the multi-step process of **civil tort analysis** in **Chinese law**.

We formalize the **tort legal reasoning (TLR) task**, build a **high-quality benchmark (LexChain<sub>eval</sub>)**, and propose a suite of reasoning-enhanced prompting and training strategies. Our findings show that structured legal reasoning significantly improves LLMs’ performance in tort case analysis and generalizes to broader legal AI tasks.

---

## ✨ The LexChain Framework
LexChain models tort case reasoning via a **three-stage chain**:

1. **Legal Element Identification**
   - Recognize plaintiffs, defendants, dispute types, and applicable statutes.

2. **Liability Analysis**
   - Reason over conduct, harm, causation, and fault.
   - Assign liability proportions and calculate damages.

3. **Judgment Summarization**
   - Produce legally grounded, structured decisions.

Each sub-task aligns with verifiable reasoning steps, enabling granular evaluation.

---

## 🧪 Benchmark: LexChain<sub>eval</sub>
We curate **1,000 real-world tort cases** from China Judgments Online.

- Covers **45+ dispute types** (e.g., traffic, product, service liability)
- Annotated with: facts, parties, statutes, damages, liability, compensation, judgment and more
- Validated by legal experts

### Dataset Structure
LexChain<sub>eval</sub> consists of two aligned `.json` files:

#### ✉️ `input.json`
```json
{
  "id": 1,
  "uniqid": "aa9cb149-c445-4d78-b1df-a7eda70423ad",
  "input": "以下是【案件事实】:... 以下是【原告主张】:..."
}
```

#### 🔗 `reference.json`
```json
{
  "id": 1,
  "uniqid": "aa9cb149-c445-4d78-b1df-a7eda70423ad",
  "reference": {
    "原告": "...",
    "责任划分": { "...": { "责任比例": "...", "承担责任方式": "..." ...} ...},
    "损失总额": "...",
    "判决结果": "..."
  }
}
```

Entries in the two files are matched via `uniqid`.

---

## 🤓 Task: Tort Legal Reasoning (TLR)
**Input:** Case facts & claims  
**Output:** Structured legal reasoning chain with:
- Parties (plaintiffs, defendants)
- Dispute type
- Applicable legal statutes
- Existence of liability
- Proportional liability
- Total damages
- Monetary compensation
- Other forms of liability bearing
- Judgment summary

Models are evaluated for their handling of the full reasoning workflow in tort analysis.

---

## 🔍 Evaluation Protocol
We propose an **LLM-as-a-Judge** rubric based on 7 key subtasks:

| Subtask | Description |
|--------|-------------|
| Plaintiff | Identify plaintiffs |
| Defendant | Identify defendants |
| Dispute | Determine dispute type |
| Statute | Match relevant laws |
| Liability | Determine liability and bearing |
| Damages | Estimate damages |
| Judgment | Summarize final ruling |

Evaluator: GPT-4o (rating quality validated by human experts; 94.9% rating accuracy, κ=0.619)

---

## 📊 Results: LexChain<sub>eval</sub>
We evaluate various LLMs (GPT-4o, Claude, DeepSeek, Qwen, etc.) on the LexChain<sub>eval</sub> benchmark:

| Model                  | Overall | Plaintiff | Defendant | Dispute | Statute | Liability | Damages | Judgment |
|------------------------|---------|-----------|-----------|---------|---------|-----------|---------|----------|
| **GPT-4o**             | 41.17   | 97.20     | 87.05     | 9.90    | 10.35   | 18.10     | 20.05   | 18.67    |
| w/ Prompt<sub>LC</sub> | 48.83   | 97.40     | 89.15     | 17.60   | 28.70   | 30.30     | 25.75   | 25.75    |
| **o3-mini**            | 40.22   | 97.00     | 86.70     | 6.40    | 11.65   | 18.45     | 17.55   | 13.57    |
| w/ Prompt<sub>LC</sub> | 50.41   | 97.80     | 89.10     | 18.70   | 33.40   | 32.80     | 26.55   | 26.89    |
| **Claude-Sonnet-4**    | 44.24   | 97.00     | 89.30     | 31.50   | 11.90   | 20.15     | 19.55   | 23.59    |
| w/ Prompt<sub>LC</sub> | 52.90   | **98.65** | 91.05     | 38.40   | 30.90   | 34.20     | 28.20   | 30.36    |
| **DeepSeek-V3**        | 46.91   | 97.80     | 87.35     | 35.20   | 20.85   | 22.45     | 22.60   | 25.60    |
| w/ Prompt<sub>LC</sub> | 54.71   | 97.70     | 89.40     | 45.50   | 35.45   | 35.15     | 29.35   | 36.86    |
| **DeepSeek-R1**        | 45.36   | 97.50     | 89.35     | 28.70   | 12.45   | 23.30     | 21.25   | 27.94    |
| w/ Prompt<sub>LC</sub> | **60.84** | 98.10   | **92.50** | 58.40   | **44.30** | **41.70** | **37.80** | **42.92** |
| **Qwen-3-8B**          | 48.79   | 97.50     | 88.60     | 29.50   | 30.70   | 26.35     | 22.35   | 24.92    |
| w/ Prompt<sub>LC</sub> | 53.30   | 97.40     | 89.15     | 38.00   | 39.85   | 32.45     | 27.60   | 28.71    |
| w/ SFT<sub>Syll</sub>  | 39.65   | 96.40     | 86.70     | 13.90   | 13.05   | 16.00     | 12.55   | 12.47    |
| w/ SFT<sub>LC</sub>    | 55.36   | 96.85     | 87.85     | **59.00** | 43.70 | 29.05     | 26.80   | 36.88    |
| w/ DPO<sub>LC</sub>    | 51.17   | 96.20     | 88.85     | 36.00   | 41.95   | 25.55     | 21.00   | 30.95    |
| **InternLM-3-8B**      | 41.61   | 96.10     | 86.10     | 20.00   | 15.70   | 17.70     | 16.15   | 15.80    |
| w/ Prompt<sub>LC</sub> | 48.58   | 96.85     | 86.20     | 26.40   | 32.95   | 29.65     | 19.55   | 26.10    |
| w/ SFT<sub>Syll</sub>  | 40.32   | 95.60     | 82.35     | 14.60   | 20.05   | 18.75     | 11.80   | 12.13    |
| w/ SFT<sub>LC</sub>    | 44.89   | 92.85     | 74.30     | 49.90   | 38.95   | 17.55     | 11.80   | 17.91    |
| w/ DPO<sub>LC</sub>    | 42.67   | 92.80     | 76.95     | 25.10   | 36.05   | 20.05     | 9.40    | 16.43    |
| **Llama-3.1-8B**       | 37.16   | 97.05     | 85.20     | 2.80    | 6.75    | 13.20     | 13.50   | 11.71    |
| w/ Prompt<sub>LC</sub> | 40.35   | 96.75     | 84.05     | 5.90    | 19.10   | 18.40     | 14.35   | 13.04    |
| w/ SFT<sub>Syll</sub>  | 33.61   | 93.70     | 79.75     | 1.40    | 4.70    | 9.65      | 12.45   | 1.48     |
| w/ SFT<sub>LC</sub>    | 51.35   | 97.10     | 86.75     | 48.00   | 39.60   | 24.15     | 23.50   | 25.95    |
| w/ DPO<sub>LC</sub>    | 44.57   | 96.55     | 85.20     | 15.70   | 33.30   | 18.85     | 15.75   | 19.84    |

---

## 🔗 Resources
- 📂 Dataset: [Hugging Face](https://huggingface.co/datasets/lexchain/LawChain-eval)
- 🖋️ Codebase: [GitHub](https://github.com/thunlp/LexChain)
- 📄 Paper: [arXiv:2510.17602](https://arxiv.org/abs/2510.17602)


## Usage

This repository contains simple scripts to run inference, automated scoring, and summary generation for an evaluation pipeline. The main scripts live at the repository root and call Python modules under `src/eval`.

### Prerequisites

- Python 3.8+
- A working virtual environment (recommended)
- Install Python dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Create a `.env` file in the project root and set the following environment variables: `API_KEY` and `URL` (used by scripts that call remote model APIs)


### File layout (important files)

- `inference.sh` — run model inference and save outputs to `inference_result`.
- `score.sh` — score model outputs against references, results saved to `scoring_result`.
- `run_summary.sh` — aggregate scoring JSON files into an Excel summary (`scoring_result/scores_summary.xlsx`).
- `data/test_input.json` — example input file for inference.
- `data/test_reference.json` — example reference file for scoring.
- `src/eval/` — contains Python scripts used by the shell wrappers (`inference.py`, `score.py`, `compute_score.py`).

### Data

The data files are NOT included in this repository. Please download the required datasets and place them into the `data/` directory using the exact filenames shown below (the scripts expect these names):

- `data/test_input.json` — input file for inference
- `data/test_reference.json` — ground-truth references for scoring

If you place files with different names, edit the shell scripts or Python arguments to point to your filenames.

### Quick usage

Make scripts executable (only required once):

```bash
chmod +x *.sh
```

Run inference (edit the variables at the top of `inference.sh` if needed):

```bash
./inference.sh
```

Run scoring (edit `INPUT_DIR`, `REF_PATH`, or other variables at the top of `score.sh` if needed):

```bash
./score.sh
```

Generate score summary from `scoring_result`:

```bash
./run_summary.sh
```

Model deployment (note)

If you want to use vLLM, please deploy your model server yourself and ensure it is reachable at the host and port below:

- --host 0.0.0.0
- --port 8000

Adjust your `*.sh` file accordingly. Once the server is up at that address, the scripts can call it as needed.


### Output locations

- Inference outputs: `inference_result/`
- Scoring outputs: `scoring_result/`
- Logs: `logs/` (path configured in each script)
- Summary Excel: `scoring_result/scores_summary.xlsx`

## 🖊️ Citation
```bibtex
@misc{xie2025lexchain,
      title={LexChain: Modeling Legal Reasoning Chains for Chinese Tort Case Analysis}, 
      author={Huiyuan Xie and Chenyang Li and Huining Zhu and Chubin Zhang and Yuxiao Ye and Zhenghao Liu and Zhiyuan Liu},
      year={2025},
      eprint={2510.17602},
      archivePrefix={arXiv},
      url={https://arxiv.org/abs/2510.17602}, 
}
```



