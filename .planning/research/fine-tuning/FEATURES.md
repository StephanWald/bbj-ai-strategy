# Feature Landscape: Fine-Tuning Evaluation & Training Best Practices

**Domain:** Niche code model fine-tuning (BBj on Qwen2.5-Coder-32B-Instruct with QLoRA)
**Researched:** 2026-02-06
**Overall confidence:** MEDIUM-HIGH (grounded in current bbjllm repo analysis, LIMA/QLoRA research papers, ASML industrial evaluation study, HuggingFace PEFT docs, and current experiment tracking landscape)

---

## Research Context

### What Already Exists (bbjllm Repo)

| Component | Current State | Assessment |
|-----------|--------------|------------|
| Training data | 9,922 ChatML JSONL examples in `dataset/dataset.jsonl` | EXISTS, needs quality audit |
| Training script | `scripts/train_qwen_32b.py` -- PEFT/QLoRA with 4-bit NF4 | EXISTS, functional but missing evaluation |
| Setup script | `scripts/starttrain.sh` -- CentOS/yum-based environment setup | EXISTS, pinned to specific library versions |
| README | Default GitLab template -- no project-specific content | MISSING real documentation |
| Evaluation suite | None | MISSING entirely |
| Experiment tracking | `report_to="none"` in training script | MISSING entirely |
| Model card | None | MISSING entirely |
| Training logs | Not committed to repo | MISSING |
| Adapter weights | Saved to `/usr2/yasser_experiment/` on training server, not committed | MISSING from repo |
| Data quality validation | None for JSONL dataset | MISSING |

### Training Data Analysis (from bbjllm/dataset/dataset.jsonl)

| Metric | Value | Assessment |
|--------|-------|------------|
| Total examples | 9,922 | Adequate for QLoRA on instruct model (LIMA showed 1K is enough for alignment; 10K is generous) |
| System message | Single uniform prompt across all examples | GOOD for consistency |
| Duplicate questions | 375 unique questions appear 2-3 times each | NEEDS DEDUP -- ~4% duplication rate |
| Very short responses (<=10 chars) | 22 examples | NEEDS REVIEW -- likely incomplete completion fragments |
| Short responses (<50 chars) | 234 examples (2.4%) | Some are valid short answers, others may be truncated |
| Long responses (>1000 chars) | 596 examples (6%) | Good presence of detailed examples |
| Median response length | 414 characters | Reasonable for code + explanation |
| Contains code | 9,309 examples (93.8%) | GOOD -- strong code representation |
| Response length range | 1 to 4,725 chars | Wide range, check extremes |

### Training Configuration Analysis (from train_qwen_32b.py)

| Parameter | Value | Assessment |
|-----------|-------|------------|
| Base model | Qwen2.5-Coder-32B-Instruct | GOOD -- instruct-tuned base, strong code model |
| Quantization | 4-bit NF4, double quantization | GOOD -- standard QLoRA config |
| LoRA rank | r=32, alpha=64 | REASONABLE -- higher than original QLoRA paper's recommendation of r=64 for 33B, but alpha/r ratio of 2 is standard |
| Target modules | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj | GOOD -- all linear layers, matches best practice |
| Learning rate | 2e-5 | GOOD for instruct model (lower than base model fine-tuning) |
| Epochs | 2 | REASONABLE for instruct model, but needs validation loss monitoring |
| Effective batch size | 32 (1 x 32 gradient accumulation) | GOOD |
| Max sequence length | 1024 | CONCERN -- may truncate longer examples (p90 is 857 chars before tokenization) |
| Eval/validation split | None | CRITICAL GAP -- no validation set, no overfitting detection |
| Experiment tracking | Disabled (`report_to="none"`) | CRITICAL GAP |

---

## Table Stakes

Features that any responsible fine-tuning effort MUST have before claiming results. Without these, the team cannot answer "did fine-tuning work?"

### TS-1: Training/Validation Split

| Aspect | Details |
|--------|---------|
| **Feature** | Split 9,922 examples into training (90%) and validation (10%) sets with stratified sampling |
| **Why Required** | The current training script uses ALL data for training with zero validation. There is no way to detect overfitting. Without a held-out set, training loss going down means nothing -- the model could be memorizing examples. |
| **Complexity** | Low |
| **Implementation** | Add `dataset.train_test_split(test_size=0.1, seed=42)` before training. Log validation loss alongside training loss. |

**What the split should look like:**
- 8,930 training examples
- 992 validation examples
- Stratified by question type if possible (code completion, explanation, function reference)
- Deterministic seed so splits are reproducible
- Validation set committed to repo separately so it is never accidentally included in training

**Confidence: HIGH** -- This is standard ML practice. The HuggingFace Trainer natively supports eval_dataset.

### TS-2: Training Loss and Validation Loss Logging

| Aspect | Details |
|--------|---------|
| **Feature** | Log training loss, validation loss, and learning rate per step/epoch to a file that gets committed to the repo |
| **Why Required** | The current training script prints to stdout but nothing is saved. After training completes, there is no record of how training progressed. Without loss curves, you cannot diagnose underfitting, overfitting, or training instability. |
| **Complexity** | Low |
| **Implementation** | At minimum: change `report_to="none"` to `report_to="tensorboard"` and commit the `runs/` directory. Better: use W&B free tier. Best: log to JSON file alongside adapter weights. |

**What to log per training step:**
- `step`, `epoch`, `training_loss`, `learning_rate`

**What to log per evaluation:**
- `step`, `epoch`, `eval_loss`, `eval_perplexity`

**Minimum viable approach (no external tools):**
```python
# In TrainingArguments:
evaluation_strategy="steps",
eval_steps=50,
logging_dir="./logs",
report_to="tensorboard",
```

Then commit `./logs/` to the repo after each training run.

**Confidence: HIGH** -- HuggingFace Trainer supports this natively.

### TS-3: Adapter Weights Committed to Repo

| Aspect | Details |
|--------|---------|
| **Feature** | Commit trained PEFT adapter files to the bbjllm repository |
| **Why Required** | Currently, adapter weights exist only on the training server at `/usr2/yasser_experiment/`. If that server is rebuilt, all training results are lost. The adapter files for a 32B QLoRA model are small (typically 100-300MB) and MUST be version-controlled. |
| **Complexity** | Low |
| **Depends On** | Git LFS for files >100MB |

**What PEFT saves (verified against HuggingFace docs):**
- `adapter_model.safetensors` -- the actual LoRA weights (typically 100-300MB for r=32 on a 32B model)
- `adapter_config.json` -- LoRA configuration (r, alpha, target modules, etc.)
- `README.md` -- auto-generated model card stub

**Repo structure recommendation:**
```
bbjllm/
  adapters/
    v1/
      adapter_model.safetensors   # Git LFS
      adapter_config.json
      training_config.json        # snapshot of all hyperparameters
      training_log.json           # loss curves
      eval_results.json           # benchmark results
    v2/
      ... (next training run)
  dataset/
    dataset.jsonl
    train.jsonl                   # training split
    val.jsonl                     # validation split
  eval/
    ... (evaluation suite)
  scripts/
    train_qwen_32b.py
    starttrain.sh
```

**Confidence: HIGH** -- PEFT adapter files are designed to be small and shareable. The official HuggingFace docs describe this exact pattern.

### TS-4: Basic Evaluation Suite (BBj-Specific)

| Aspect | Details |
|--------|---------|
| **Feature** | A set of BBj code generation tasks with automated correctness checking |
| **Why Required** | Without evaluation, there is literally no way to answer "is the fine-tuned model better than the base model?" or "did this training run improve over the last one?" The absence of evaluation is the single largest gap in the current setup. |
| **Complexity** | Medium-High |
| **Depends On** | bbjcpl compiler availability for syntax checking |

**Evaluation design -- three tiers:**

**Tier 1: Syntax Correctness (automated, compile-based)**
- Generate BBj code for N prompts
- Run each through `bbjcpl -N` (syntax-only compilation)
- Metric: `compile@1` -- fraction of generated code that compiles
- This is the BBj equivalent of the ASML paper's `build@k` metric
- Minimum 50 prompts covering: built-in functions, GUI creation, file I/O, string operations, OOP, error handling

**Tier 2: Factual Correctness (automated, pattern-matching)**
- Ask questions about BBj functions/APIs with known answers
- Check response contains correct information
- Example: "What does CHR$(65) return?" -- answer must contain "A"
- Example: "What is the syntax for OPEN verb?" -- answer must contain channel number pattern
- Minimum 30 factual questions with regex-based answer validation

**Tier 3: Qualitative Comparison (manual, side-by-side)**
- Same prompt given to base model (Qwen2.5-Coder-32B-Instruct without adapter) and fine-tuned model
- Human evaluator (BBj engineer) rates which response is better
- 20 prompts covering realistic development scenarios
- Record results in a structured format

**Why three tiers:**
- Tier 1 catches syntactic regressions (did fine-tuning break code generation?)
- Tier 2 catches factual regressions (did fine-tuning introduce wrong information?)
- Tier 3 measures actual improvement (is the fine-tuned model more useful?)

**Confidence: MEDIUM-HIGH** -- The compile-based approach is novel for BBj but follows the same logic as HumanEval's pass@k and ASML's build@k. The bbjcpl compiler makes Tier 1 uniquely feasible for BBj. Tier 2 is straightforward. Tier 3 requires human time but is essential.

### TS-5: Data Quality Validation Script

| Aspect | Details |
|--------|---------|
| **Feature** | Automated quality checks on the 9,922 JSONL training examples |
| **Why Required** | The current dataset has known issues: 375 duplicate questions, 22 very short responses (some just fragments like `"10)"`), and no validation that code blocks are syntactically correct. Data quality has more impact on fine-tuning outcomes than hyperparameter tuning (per LIMA paper and QLoRA insights). |
| **Complexity** | Medium |

**What the validation script should check:**

1. **Format validation:**
   - Every line is valid JSON
   - Every example has `messages` array with exactly 3 elements (system, user, assistant)
   - Roles are in correct order
   - No empty content fields

2. **Duplicate detection:**
   - Exact duplicate questions
   - Near-duplicate questions (Levenshtein distance < 10% of length)
   - Flag but do not auto-remove (some duplicates with different answers are intentional augmentation)

3. **Length outliers:**
   - Responses shorter than 20 characters (likely fragments)
   - Responses longer than 4000 characters (may get truncated at MAX_LENGTH=1024 tokens)
   - Questions shorter than 10 characters

4. **Content quality signals:**
   - Code block presence in code-generation answers
   - BBj-specific patterns in code blocks (REM, PRINT, BBjAPI, etc.)
   - Balanced representation across topic areas

5. **Tokenization length check:**
   - Apply Qwen tokenizer to formatted examples
   - Flag examples that exceed MAX_LENGTH (1024 tokens)
   - Report truncation statistics

**Output:** JSON report with per-check pass/fail counts, flagged examples by category.

**Confidence: HIGH** -- Straightforward Python script. The training-data repo already has a simpler validator (`training-data/scripts/validate.py`). This extends that pattern to the JSONL dataset.

### TS-6: Model Card / README

| Aspect | Details |
|--------|---------|
| **Feature** | Replace the default GitLab README with a proper project README and include a model card for each trained adapter |
| **Why Required** | The current README is the GitLab default template. No one can understand what this repo does, how to use the trained model, or what results have been achieved. For an internal team, this is the difference between "a personal experiment" and "a team resource." |
| **Complexity** | Low |

**README.md should contain:**
1. Project description (what, why)
2. Repository structure
3. How to run training
4. How to evaluate
5. How to deploy to Ollama
6. Current best results
7. Known limitations

**Model card (per adapter version) should contain:**
1. Base model and version
2. Training data description (count, topics covered)
3. Training configuration (all hyperparameters)
4. Training metrics (final train/val loss, epochs)
5. Evaluation results (compile@1, factual accuracy, qualitative comparison)
6. Known limitations and failure modes
7. Deployment instructions (GGUF conversion, Ollama Modelfile)
8. Date trained, who trained it

**Format:** Follow HuggingFace Annotated Model Card Template adapted for internal use. The full HuggingFace template includes ethical considerations, bias analysis, etc. -- for an internal BBj model, focus on technical details and usage instructions.

**Confidence: HIGH** -- Standard documentation practice. HuggingFace provides templates.

---

## Differentiators

Features that elevate the fine-tuning effort from "we ran training" to "we have a systematic, improvable process."

### D-1: Experiment Tracking with Weights & Biases

| Aspect | Details |
|--------|---------|
| **Feature** | Integrate W&B free tier for experiment tracking across training runs |
| **Value Proposition** | Enables comparing runs side-by-side: different hyperparameters, different data subsets, different epochs. The free tier supports unlimited experiments for individuals. Without this, comparing runs requires manual spreadsheet tracking. |
| **Complexity** | Low |
| **Implementation** | Change `report_to="none"` to `report_to="wandb"`, add `WANDB_PROJECT="bbjllm"` env var |

**Why W&B over MLflow or simple logs:**
- W&B free tier is zero-infrastructure (hosted, no server to run)
- 5-minute setup vs MLflow's 30-minute setup
- Superior visualization for loss curves and run comparison
- HuggingFace Trainer has native W&B integration (`report_to="wandb"`)
- Small team (1-3 people) does not need MLflow's enterprise features
- If the team is allergic to cloud services, TensorBoard is the fallback (`report_to="tensorboard"`)

**What W&B tracks automatically with HuggingFace Trainer:**
- Training loss per step
- Validation loss per step
- Learning rate schedule
- GPU utilization
- All hyperparameters
- System metrics (memory, temperature)
- Model artifacts (optional)

**Confidence: HIGH** -- W&B + HuggingFace Trainer integration is well-documented and widely used. Literally a 2-line change in the training script.

### D-2: Compile-Based Evaluation with bbjcpl

| Aspect | Details |
|--------|---------|
| **Feature** | Automated evaluation pipeline that generates BBj code from prompts and validates syntax via bbjcpl compiler |
| **Value Proposition** | This is the BBj-specific secret weapon. No public BBj benchmark exists, but the BBj compiler IS the ground truth for syntactic correctness. This creates a unique, automated, non-gameable evaluation metric. |
| **Complexity** | Medium |
| **Depends On** | bbjcpl binary, trained model accessible via Ollama or direct inference |

**Evaluation pipeline design:**

```
eval/
  prompts/
    syntax/          # 50+ prompts testing BBj syntax knowledge
      builtin-functions.jsonl
      gui-creation.jsonl
      file-io.jsonl
      string-ops.jsonl
      oop-patterns.jsonl
      error-handling.jsonl
    factual/         # 30+ prompts testing BBj knowledge
      function-reference.jsonl
      api-knowledge.jsonl
    realistic/       # 20+ prompts for qualitative eval
      development-scenarios.jsonl
  scripts/
    run_eval.py      # Generate responses, run bbjcpl, score
    compare_runs.py  # Compare two eval runs side-by-side
  results/
    v1/
      syntax_results.json
      factual_results.json
      qualitative_results.json
    v2/
      ...
```

**`run_eval.py` workflow:**
1. Load prompts from JSONL files
2. For each prompt, generate response using the model (via Ollama API or direct inference)
3. Extract code blocks from response
4. Write each code block to temp .bbj file
5. Run `bbjcpl -N <file>` and capture exit code + stderr
6. Record: prompt, response, code_block, compiles (bool), error_message (if any)
7. Calculate aggregate metrics: compile@1, compile@5 (if generating multiple samples)
8. Save results as JSON

**Metrics:**
- `compile@1`: Fraction of prompts where the first generated code compiles
- `compile@5`: Fraction of prompts where at least one of 5 generated samples compiles
- `factual_accuracy`: Fraction of factual questions answered correctly (regex-based)
- `base_vs_finetuned`: Side-by-side comparison scores

**Confidence: MEDIUM-HIGH** -- The bbjcpl integration is proven (bbjcpltool exists). The evaluation framework is novel for BBj but follows established patterns (HumanEval, ASML build@k). Main uncertainty: extracting clean code blocks from model output is sometimes messy.

### D-3: Base Model Comparison Baseline

| Aspect | Details |
|--------|---------|
| **Feature** | Run the evaluation suite against the UNMODIFIED Qwen2.5-Coder-32B-Instruct model to establish a baseline |
| **Value Proposition** | Without a baseline, you cannot prove fine-tuning helped. If the base model already gets 0% compile rate on BBj, that is useful context. If it gets 30%, you need fine-tuning to beat 30%. Without this data point, all fine-tuning claims are ungrounded. |
| **Complexity** | Low (once eval suite exists) |
| **Depends On** | D-2 evaluation suite |

**What to measure:**
- Run identical eval prompts against base model (no adapter)
- Run identical eval prompts against fine-tuned model (with adapter)
- Compare: compile@1, factual accuracy, response quality
- Document delta in eval results

**Why this matters for BBj specifically:**
The original strategy paper claims "LLMs have near-zero training data on BBj." This is the hypothesis. The baseline evaluation either confirms it (base model compile@1 near 0%) or challenges it (maybe Qwen2.5-Coder already knows some BBj from training data). Either result is valuable.

**Confidence: HIGH** -- Trivially achievable once the eval suite exists. Just run it twice.

### D-4: GGUF Export and Ollama Deployment Pipeline

| Aspect | Details |
|--------|---------|
| **Feature** | Documented, reproducible pipeline to merge PEFT adapter into base model, convert to GGUF, quantize, and deploy via Ollama |
| **Value Proposition** | The fine-tuned model is useless if it cannot be deployed. The downstream consumers (IDE extension, MCP server, web chat) all access the model through Ollama. Without a clear merge-quantize-deploy pipeline, the adapter weights sitting in the repo are academic. |
| **Complexity** | Medium |

**Pipeline steps (verified against 2025-2026 documentation):**

1. **Merge adapter into base model:**
```python
from peft import PeftModel
from transformers import AutoModelForCausalLM
base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-32B-Instruct")
model = PeftModel.from_pretrained(base, "./adapters/v1")
merged = model.merge_and_unload()
merged.save_pretrained("./merged_model")
```

2. **Convert to GGUF:**
```bash
python llama.cpp/convert_hf_to_gguf.py ./merged_model --outfile bbj-qwen-32b-f16.gguf
```

3. **Quantize:**
```bash
llama.cpp/bin/llama-quantize bbj-qwen-32b-f16.gguf bbj-qwen-32b-q4_k_m.gguf Q4_K_M
```

4. **Create Ollama Modelfile:**
```
FROM ./bbj-qwen-32b-q4_k_m.gguf
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop "<|im_end|>"
SYSTEM "You are an expert BBj programmer who helps users write and understand BBj code."
```

5. **Import into Ollama:**
```bash
ollama create bbj-coder -f Modelfile
ollama run bbj-coder "Write a BBj program that opens a window"
```

**Important note:** For a 32B model, the Q4_K_M quantized GGUF will be approximately 18-20GB. This is large but within Ollama's capabilities on machines with sufficient RAM (32GB+ recommended).

**Alternative: Unsloth path.** If the team switches to Unsloth for training (which supports Qwen2.5), Unsloth can export directly to Ollama GGUF with automatic Modelfile creation, skipping the manual merge/convert/quantize steps. This is worth investigating but requires changing the training framework.

**Confidence: MEDIUM** -- The merge-convert-quantize-deploy pipeline is well-documented for other models. The main risk is that 32B model merging requires significant RAM (64GB+ for FP16 merge) and may need to be done on a machine with enough resources.

### D-5: Iterative Training Workflow Documentation

| Aspect | Details |
|--------|---------|
| **Feature** | Documented process for running training iterations: when to retrain, how to compare runs, when to stop |
| **Value Proposition** | Without a defined workflow, training is ad-hoc. "Yasser ran it once" is not a process. A documented workflow enables any team member to run training, evaluate results, and make data-driven decisions about next steps. |
| **Complexity** | Low (documentation) |

**Recommended iterative workflow:**

```
1. DATA PREPARATION
   - Run data quality validation script
   - Fix flagged issues (duplicates, truncated examples)
   - Split into train/val sets
   - Commit clean dataset

2. TRAINING RUN
   - Set experiment name in W&B (or log file)
   - Record all hyperparameters
   - Monitor training loss + validation loss during training
   - Save adapter weights + training logs

3. EVALUATION
   - Run eval suite (compile@1, factual accuracy)
   - Compare against baseline (base model) and previous best
   - If improved: commit adapter + eval results as new version
   - If not improved: diagnose (overfitting? bad data? wrong hyperparams?)

4. DEPLOYMENT (if improved)
   - Merge adapter + convert to GGUF + quantize
   - Import to Ollama
   - Smoke test with manual prompts
   - Update model card with new results

5. DATA IMPROVEMENT (cycle back to step 1)
   - Based on eval failures, identify weak areas
   - Add training examples for those areas
   - Re-run from step 1
```

**When to stop training within a run:**
- Validation loss has not improved for 2 consecutive evaluation steps
- Training loss continues dropping but validation loss is rising (overfitting)
- After 2-3 epochs for an instruct model (more epochs risk catastrophic forgetting)

**When to stop iterating overall:**
- compile@1 exceeds 70% on syntax prompts
- Qualitative evaluation shows clear improvement over base model
- Engineers report the model is useful in practice
- Diminishing returns on additional training data

**Confidence: HIGH** -- This is standard ML workflow best practice applied to the BBj context.

---

## Anti-Features

Features to deliberately NOT pursue. Each would waste time or actively harm the fine-tuning effort.

### AF-1: Full Fine-Tuning (Unfreezing All Weights)

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Full fine-tuning of the 32B model | Requires 8x the memory, 10x the compute, and risks catastrophic forgetting of the base model's general coding ability. For a 32B model, full fine-tuning would need multiple A100-80GB GPUs. The QLoRA approach already achieves 80-90% of full fine-tuning quality. | Continue with QLoRA. If quality plateaus, increase LoRA rank (r=64 or r=128) before considering full fine-tuning. |

### AF-2: Training a BBj-Specific Tokenizer

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Extending the tokenizer with BBj-specific tokens | Modifying the tokenizer requires resizing the model's embedding layer, which invalidates the pre-trained weights. For 10K examples, the tokenizer overhead is negligible. BBj keywords (PRINT, REM, OPEN, etc.) are already well-tokenized by Qwen's tokenizer since they are common English words. | Use the existing Qwen tokenizer as-is. If specific BBj tokens are poorly tokenized (e.g., `BBjAPI()`, `sysgui!`), address this in training data formatting, not tokenizer modification. |

### AF-3: Multi-Turn Conversation Training Data

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Converting training data to multi-turn conversations | The current single-turn format (system + user + assistant) is correct for a code assistant. Multi-turn training requires careful handling of conversation context, attention masking, and loss computation on only the assistant turns. It adds complexity without clear benefit for code generation tasks. | Keep single-turn format. Each example is an independent question-answer pair. If multi-turn is needed later, build it as a separate, smaller dataset. |

### AF-4: Synthetic Data Generation at Scale

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Using GPT-4/Claude to generate 100K+ synthetic BBj training examples | LLMs do not know BBj well enough to generate correct BBj code. Synthetic examples would contain the same hallucinations the fine-tuning is meant to fix. This creates a garbage-in-garbage-out cycle. | Focus on curating high-quality examples from authoritative sources: official documentation, real BBj programs, expert-written examples. 10K high-quality examples > 100K synthetic ones (LIMA principle). |

### AF-5: Obsessing Over Hyperparameter Tuning

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Running grid search over learning rates, LoRA ranks, dropout values, etc. | The current hyperparameters are within the recommended range for QLoRA on a 32B instruct model. Data quality has 5-10x more impact than hyperparameter tuning (per QLoRA paper: "data quality and formatting matter more than most hyperparameters"). The team's time is better spent improving training data. | Use the current hyperparameters as default. Only adjust if evaluation reveals specific issues (e.g., reduce LR if training is unstable, increase rank if model underfits). |

### AF-6: Deploying Without Evaluation

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Merging the adapter, deploying to Ollama, and declaring success | Without evaluation, there is no evidence the fine-tuned model is better than the base model. It might even be worse (catastrophic forgetting). Deploying an unevaluated model erodes trust when it generates wrong BBj code. | Establish the evaluation baseline (TS-4, D-2, D-3) BEFORE deploying. Only deploy when evaluation shows clear improvement. |

### AF-7: Production-Grade MLOps Infrastructure

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Setting up Kubernetes, model registries, A/B testing, automated retraining pipelines | The team is 1-3 people working on an internal tool for a niche language. MLOps infrastructure has a 3-6 month payoff timeline. The immediate need is "does the model work at all?" | Use the simplest possible workflow: local training, W&B free tier for tracking, git for version control, manual Ollama deployment. Scale up infrastructure only after proving the model is useful. |

---

## Feature Dependencies

### Dependency Graph

```
Data Quality Validation (TS-5)
  |
  +--> Clean Dataset
  |     |
  |     +--> Train/Val Split (TS-1)
  |           |
  |           +--> Training with Loss Logging (TS-2)
  |                 |
  |                 +--> Adapter Weights Committed (TS-3)
  |                 |     |
  |                 |     +--> Model Card (TS-6)
  |                 |     |
  |                 |     +--> GGUF Export Pipeline (D-4)
  |                 |           |
  |                 |           +--> Ollama Deployment
  |                 |
  |                 +--> Evaluation Suite (TS-4)
  |                       |
  |                       +--> Base Model Baseline (D-3)
  |                       |
  |                       +--> Compile-Based Eval (D-2)
  |
  +--> W&B Integration (D-1) [independent, can add anytime]
  |
  +--> Iterative Workflow Docs (D-5) [independent, can write anytime]
```

### Critical Path

The shortest path to "we know if fine-tuning worked":

1. **TS-5: Data quality validation** -- find and fix data issues
2. **TS-1: Train/val split** -- enable overfitting detection
3. **TS-4: Evaluation suite** -- define what "works" means
4. **D-3: Base model baseline** -- establish comparison point
5. **TS-2: Training with logging** -- retrain with proper monitoring
6. **TS-3: Commit adapter weights** -- preserve results
7. **TS-6: Model card** -- document what was done

### Independent Tracks

These can be built in parallel:
- **D-1: W&B integration** -- 2-line change, do immediately
- **D-5: Iterative workflow docs** -- write anytime
- **D-4: GGUF export pipeline** -- test independently from eval

---

## Dataset Size Analysis

### Is 10K Examples Enough for a 32B QLoRA Model?

**Short answer: Yes, likely more than enough for the instruct-tuning use case.**

**Evidence:**

| Source | Finding | Confidence |
|--------|---------|------------|
| LIMA paper (2023) | 1,000 carefully curated examples on 65B LLaMA achieved performance competitive with GPT-4 in 43% of human evaluations | HIGH |
| QLoRA paper (2023) | "small high-quality dataset leads to state-of-the-art results, even when using smaller models" | HIGH |
| Qwen2.5 fine-tuning guides (2025) | "1,200-2,500 examples was the sweet spot for a 7B LoRA" -- implies 10K for 32B is generous | MEDIUM |
| General consensus (2025-2026) | Data quality > data quantity for instruction-tuned base models | HIGH |

**Key insight for BBj:** The base model (Qwen2.5-Coder-32B-Instruct) already knows how to write code, follow instructions, and produce well-structured responses. Fine-tuning is NOT teaching it to code from scratch -- it is teaching it BBj-specific syntax and APIs. This is a relatively narrow skill that does not require massive data.

**Expected quality curve:**
- 0-500 examples: Model learns BBj exists, basic syntax patterns
- 500-2000 examples: Rapid improvement in correct BBj code generation
- 2000-5000 examples: Improving coverage of BBj API surface area
- 5000-10000 examples: Diminishing returns, marginal improvements
- 10000+: Very diminishing returns unless new topic areas are added

**Recommendation:** The current 9,922 examples are sufficient in quantity. Focus on QUALITY over adding more examples. Specifically:
1. Remove or fix the 375 duplicate questions
2. Review and fix the 22 very-short responses
3. Verify code examples compile with bbjcpl
4. Ensure balanced coverage across BBj topic areas (built-in functions, GUI, file I/O, OOP, DWC)

### Catastrophic Forgetting Risk

**Concern:** Fine-tuning on 10K BBj-only examples could cause the model to "forget" general coding ability.

**Mitigation (built into current approach):**
- QLoRA only modifies adapter weights, not base model weights -- inherently limits forgetting
- Using an instruct-tuned base model (already trained on millions of instruction pairs) provides strong foundation
- 2 epochs is conservative (more epochs = more forgetting risk)
- The effective training data is small relative to the model's capacity

**Research finding (2025):** "Through qLoRA we can preserve the chat-finetuned nature of the base model and hence mitigate catastrophic forgetting." Using QLoRA on an already-instruct-tuned model is specifically favorable for avoiding forgetting.

**Validation approach:** Include a few non-BBj prompts in the evaluation suite (e.g., "Write a Python function to sort a list") to verify general coding ability is preserved.

---

## Training Artifact Checklist

### What the bbjllm Repo SHOULD Contain

**Required (Table Stakes):**

- [ ] `README.md` -- Project description, how to train, how to evaluate, how to deploy
- [ ] `dataset/dataset.jsonl` -- Full training dataset (EXISTS)
- [ ] `dataset/train.jsonl` -- Training split (90%)
- [ ] `dataset/val.jsonl` -- Validation split (10%)
- [ ] `dataset/DATASHEET.md` -- Data description: sources, collection method, statistics
- [ ] `scripts/train_qwen_32b.py` -- Training script (EXISTS, needs eval integration)
- [ ] `scripts/starttrain.sh` -- Environment setup (EXISTS)
- [ ] `scripts/validate_data.py` -- Data quality validation
- [ ] `eval/prompts/` -- Evaluation prompts (syntax, factual, realistic)
- [ ] `eval/scripts/run_eval.py` -- Evaluation runner
- [ ] `eval/baselines/base_model_results.json` -- Base model performance
- [ ] `adapters/v{N}/adapter_model.safetensors` -- Trained adapter (Git LFS)
- [ ] `adapters/v{N}/adapter_config.json` -- Adapter configuration
- [ ] `adapters/v{N}/training_config.json` -- All hyperparameters
- [ ] `adapters/v{N}/training_log.json` -- Loss curves
- [ ] `adapters/v{N}/eval_results.json` -- Evaluation scores
- [ ] `adapters/v{N}/MODEL_CARD.md` -- What, how, results, limitations
- [ ] `.gitattributes` -- Git LFS tracking for .safetensors files
- [ ] `Modelfile` -- Ollama model definition

**Recommended (Differentiators):**

- [ ] `scripts/export_gguf.sh` -- Merge + convert + quantize pipeline
- [ ] `scripts/compare_runs.py` -- Side-by-side run comparison
- [ ] `eval/results/v{N}/` -- Per-run evaluation outputs
- [ ] `wandb/` or `logs/` -- Experiment tracking data (if not using hosted W&B)
- [ ] `docs/TRAINING_GUIDE.md` -- Step-by-step training workflow

**Do NOT commit:**

- Full model weights (base model is 60GB+ on HuggingFace, downloaded at training time)
- Intermediate checkpoints (large, only adapter from best/final checkpoint matters)
- Python virtual environments or `__pycache__/`
- API keys or credentials
- Training server-specific paths (use environment variables)

---

## MVP Recommendation

For the v1.7 documentation recommendations, prioritize in this order:

### Phase 1: Foundation (Must recommend in documentation)

1. **TS-5: Data quality validation** -- Script to audit the 9,922 examples
2. **TS-1: Train/val split** -- 90/10 split with fixed seed
3. **TS-2: Training loss logging** -- At minimum TensorBoard, ideally W&B
4. **TS-3: Adapter weights in repo** -- Git LFS for .safetensors
5. **TS-6: Model card** -- Document what was trained and results

### Phase 2: Evaluation (Must recommend in documentation)

6. **TS-4: Evaluation suite** -- Compile-based + factual + qualitative
7. **D-3: Base model baseline** -- Prove fine-tuning helps
8. **D-2: bbjcpl compile evaluation** -- Unique BBj advantage

### Phase 3: Workflow (Should recommend in documentation)

9. **D-1: W&B integration** -- 2-line change, high value
10. **D-5: Iterative workflow** -- Process documentation
11. **D-4: GGUF export pipeline** -- End-to-end deployment

---

## Sources

### HIGH Confidence (Papers, Official Documentation)

- [LIMA: Less Is More for Alignment](https://arxiv.org/abs/2305.11206) -- NeurIPS 2023. 1,000 examples sufficient for competitive performance on 65B model. Core evidence for data quality > quantity.
- [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314) -- NeurIPS 2023. "Small high-quality dataset leads to state-of-the-art results." Data quality > hyperparameters.
- [HuggingFace PEFT Checkpoint Format](https://huggingface.co/docs/peft/main/en/developer_guides/checkpoint) -- adapter_model.safetensors + adapter_config.json structure.
- [HuggingFace Annotated Model Card Template](https://huggingface.co/docs/hub/en/model-card-annotated) -- Standard model documentation template.
- [Evaluating LLMs for Code in Industrial Settings (ASML)](https://arxiv.org/abs/2509.12395) -- September 2025. Custom benchmark from 156 proprietary code examples, build@k metric, few-shot prompting significantly outperforms zero-shot.
- bbjllm repo analysis -- Direct examination of `dataset/dataset.jsonl` (9,922 examples), `scripts/train_qwen_32b.py`, `scripts/starttrain.sh`.

### MEDIUM Confidence (Multiple Sources Agree)

- [LoRA & QLoRA Fine-Tuning Best Practices](https://lightning.ai/pages/community/lora-insights/) -- Lightning AI. "Data quality and formatting matter more than most hyperparameters."
- [W&B vs MLflow Comparison 2025](https://medium.com/@pablop44/why-everyone-is-migrating-from-mlflow-to-weights-biases-w-b-in-2025-5926f978e03e) -- W&B 5-min setup vs MLflow 30-min, superior for small teams.
- [Catastrophic Forgetting Mitigation with QLoRA](https://towardsdatascience.com/leveraging-qlora-for-fine-tuning-of-task-fine-tuned-models-without-catastrophic-forgetting-d9bcd594cff4/) -- QLoRA preserves chat-finetuned nature of base model.
- [Ollama Model Import](https://docs.ollama.com/import) -- GGUF import workflow.
- [Qwen2.5 Fine-Tuning Guides](https://www.f22labs.com/blogs/complete-guide-to-fine-tuning-qwen2-5-vl-model/) -- LoRA configuration recommendations.

### LOW Confidence (Needs Validation)

- Dataset size "sweet spot" of 1,200-2,500 for 7B models -- extrapolation to 32B is uncertain. More parameters may need more examples, or the instruct base may compensate.
- Compile@1 metric for BBj -- novel metric, inspired by HumanEval pass@k and ASML build@k but not validated for BBj specifically. Needs empirical validation.
- GGUF export pipeline for Qwen2.5-Coder-32B -- documented for other models but not specifically tested with this model + QLoRA adapter combination. RAM requirements for 32B FP16 merge may be prohibitive on some machines.
