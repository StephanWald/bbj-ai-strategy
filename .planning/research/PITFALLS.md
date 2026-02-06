# Domain Pitfalls: Fine-Tuning a Niche-Language Code Model

**Domain:** QLoRA fine-tuning of Qwen2.5-Coder-32B-Instruct for BBj (Business BASIC for Java), a niche language with near-zero public training data
**Researched:** 2026-02-06
**Focus:** Risks and common mistakes specific to the bbjllm fine-tuning project. Every pitfall references the actual training script (`train_qwen_32b.py`), dataset (`dataset.jsonl`), and configuration choices in the bbjllm repo.
**Supersedes:** Previous PITFALLS.md covered v1.5 alpha-ready feature integration pitfalls (SSE streaming, MCP mounting, connection pooling, etc.). Those issues are addressed in the shipped v1.5 system. This document covers fine-tuning pitfalls for the v1.7 documentation refresh.

---

## Critical Pitfalls (BLOCKER)

Mistakes that produce a model that is worse than the base model, waste GPU time on unrecoverable training runs, or make the fine-tuning effort fundamentally unsound.

---

### C-1: Training on Full Sequence Instead of Completion Only

**Severity:** BLOCKER
**Applies to current bbjllm approach:** YES -- confirmed in code

**What goes wrong:** The current `train_qwen_32b.py` (lines 288-295) creates labels by copying `input_ids` and only masking padding tokens with `-100`. This means the loss is computed on the ENTIRE sequence: system prompt, user question, AND assistant response. The model learns to predict the system prompt and user question tokens -- which are constant and uninformative -- diluting the gradient signal from the actual BBj code responses.

**Evidence from code:**
```python
# Current implementation (lines 288-295):
labels = model_inputs["input_ids"].copy()
labels = [
    -100 if token == tokenizer.pad_token_id else token
    for token in labels
]
```

The system prompt "You are an expert BBj programmer who helps users write and understand BBj code." appears in all 9,923 examples. Every training step wastes compute predicting these 17 tokens. The user prompts (averaging ~40 tokens each) are similarly wasted.

**Why it matters for BBj specifically:** With only 9,923 examples in a niche domain, every gradient signal counts. Wasting 30-40% of the loss signal on system/user tokens means the model needs more epochs or more data to learn the same BBj patterns -- increasing overfitting risk while reducing learning efficiency.

**Research context:** The standard practice in instruction fine-tuning is completion-only training. TRL's SFTTrainer computes loss on completion tokens only by default (`completion_only_loss=True`). The Hugging Face documentation states: "We want the model to learn to generate high-quality responses, not to predict user inputs." The current script uses raw `Trainer` instead of `SFTTrainer`, bypassing this built-in safeguard.

**Warning signs:**
- Training loss drops quickly (model learns to predict the fixed system prompt) but generation quality does not improve proportionally
- Model starts outputting system-prompt-like phrasing in its generated code
- Validation loss (if measured) is higher than expected given training loss

**Prevention:**
- Mask all tokens before the assistant's response with `-100` in labels. Identify the assistant turn boundary by locating the `<|im_start|>assistant` token sequence in the tokenized output, and set all labels before that point to `-100`.
- Alternatively, switch from raw `Trainer` to TRL's `SFTTrainer` which handles completion masking automatically for ChatML-formatted data.
- If continuing with raw `Trainer`, implement explicit mask logic:
  ```python
  # Find where assistant response starts
  assistant_start_token = tokenizer.encode("<|im_start|>assistant\n", add_special_tokens=False)
  # Mask everything before this point with -100
  ```

**Confidence:** HIGH -- Confirmed by reading the training script source code. The labeling logic is unambiguous. Research consensus (Sebastian Raschka's experiments, HuggingFace TRL defaults, multiple 2025 papers) strongly favors completion-only masking.

**Sources:**
- [To Mask or Not to Mask: The Effect of Prompt Tokens on Instruction Tuning](https://towardsdatascience.com/to-mask-or-not-to-mask-the-effect-of-prompt-tokens-on-instruction-tuning-016f85fd67f4/) -- Research showing masking prompt tokens improves instruction following
- [Sebastian Raschka: LLM Research Insights on Instruction Masking](https://magazine.sebastianraschka.com/p/llm-research-insights-instruction) -- Experimental validation of masking approaches
- [HuggingFace TRL SFTTrainer Docs](https://huggingface.co/docs/trl/sft_trainer) -- Default completion-only loss behavior

---

### C-2: Fine-Tuning Instruct Model Risks Performance Degeneration

**Severity:** BLOCKER
**Applies to current bbjllm approach:** YES -- using `Qwen/Qwen2.5-Coder-32B-Instruct`

**What goes wrong:** The model being fine-tuned is the Instruct variant, not the Base model. Recent research (Shadow-FT, May 2025) demonstrates that directly fine-tuning Instruct models often leads to "marginal improvements and even performance degeneration." The Instruct model has already been aligned through instruction tuning; further fine-tuning can degrade its instruction-following capabilities while adding domain knowledge -- a tradeoff called the "alignment tax."

**Why it happens:** The Instruct model's weights encode both code knowledge AND instruction-following behavior. Fine-tuning overwrites both simultaneously. LoRA weight deltas add to the aligned weights, and recent research confirms that "LoRA-tuned models can forget significant parts of the pre-training distribution, sometimes even more than fully fine-tuned models" due to the additive nature of the updates.

**The specific risk for BBj:** Qwen2.5-Coder-32B-Instruct is already a strong code model that can follow instructions like "Write BBj code to..." and produce structured responses with explanations. Fine-tuning on 10K BBj examples may teach it BBj syntax but degrade its ability to structure responses, explain code, or handle multi-step instructions -- the very things that make the Instruct variant useful for IDE integration.

**Research evidence:** The Shadow-FT paper (arxiv:2505.12716) found that paired Base and Instruct models have weight similarity greater than 98% for Llama 3.1 8B. Direct tuning of the Instruct model underperformed their alternative approach: fine-tune the Base model, then graft the weight deltas to the Instruct model (W_I+ = W_I + (W_B+ - W_B)).

**Qwen-specific guidance:** The official Qwen documentation states: "The Base model serves as a foundation for developers to fine-tune their own models." The Instruct model is described as "ready-to-use" -- implying the Base is the intended fine-tuning target.

**Warning signs:**
- Model generates correct BBj syntax but loses ability to explain code or follow complex instructions
- Responses become terse or lose formatting structure (the Instruct alignment is degrading)
- Model performs worse on general coding tasks despite improving on BBj-specific benchmarks

**Prevention options (ordered by effort):**
1. **Switch to Base model (recommended):** Fine-tune `Qwen2.5-Coder-32B` (Base) instead of `Qwen2.5-Coder-32B-Instruct`. This requires adjusting the chat template handling but is the standard approach.
2. **Shadow-FT technique:** Fine-tune the Base model with the current training data, then graft the weight deltas to the Instruct model. This preserves alignment while adding BBj knowledge. The technique is implemented at [github.com/wutaiqiang/Shadow-FT](https://github.com/wutaiqiang/Shadow-FT) and has been validated on Qwen models.
3. **If staying with Instruct:** Use a much lower learning rate (5e-6 to 1e-5 instead of 2e-5), fewer epochs (1 instead of 2), and monitor instruction-following quality via qualitative evaluation after each checkpoint.

**Confidence:** MEDIUM-HIGH -- The Shadow-FT paper is peer-reviewed (ICLR 2025 submission) and tested on Qwen models specifically. However, the paper evaluated general tasks, not niche-language code generation. The recommendation to use Base over Instruct for fine-tuning is consistent across Qwen's own documentation and community best practices, but the specific magnitude of degradation for code tasks is less well-documented.

**Sources:**
- [Shadow-FT: Tuning Instruct Model via Training on Paired Base Model](https://arxiv.org/abs/2505.12716) -- Demonstrates Instruct model degeneration and proposes Shadow-FT
- [Qwen2.5-Coder Family Blog](https://qwenlm.github.io/blog/qwen2.5-coder-family/) -- Official guidance on Base vs Instruct models
- [Difference Between Qwen 2.5 Coder Base and Instruct](https://www.byteplus.com/en/topic/417606) -- Community analysis of when to use each

---

### C-3: No Validation Set, No Evaluation Framework -- Blind Iteration

**Severity:** BLOCKER
**Applies to current bbjllm approach:** YES -- confirmed no eval split, no eval metrics

**What goes wrong:** The training script uses 100% of the 9,923 examples for training with zero held-out validation data. There is no `evaluation_strategy` in `TrainingArguments`, no `eval_dataset` passed to `Trainer`, and no post-training evaluation beyond 3 hardcoded test questions (`test_model()` at line 374). The team is iterating on hyperparameters and data without any systematic way to measure whether changes help or hurt.

**Why this is a BLOCKER, not just a concern:** Without evaluation, you cannot distinguish between:
- A model that memorized the training data (overfitting) vs. one that generalized BBj knowledge
- Improvement from hyperparameter changes vs. random variation
- Whether more epochs help or harm
- Whether data quality fixes improve the model

The 3 test questions in `test_model()` ("What is CHR() function in BBj?", "How do I read a CSV file in BBj?", "Write BBj code to use MSGBOX() function") are not a substitute for systematic evaluation. They test only 3 of the hundreds of BBj functions in the training set, are manually inspected (subjective), and are not held out from training (the model may have memorized answers to similar questions).

**Specific risk for BBj:** Because BBj has near-zero representation in public benchmarks, there is no existing evaluation suite to use. This means evaluation MUST be built by the team. Without it, the team cannot credibly claim the model has improved at BBj code generation -- a key claim in the strategy documentation.

**Warning signs:**
- Team says "the model seems better" based on anecdotal testing
- Training loss decreases but nobody can confirm generation quality improved
- Conflicting opinions on model quality within the team (no objective measure)
- Cannot answer "which checkpoint is best?" with data

**Prevention:**
1. **Immediate (1 day):** Hold out 5-10% of the dataset as a validation set. Add `evaluation_strategy="steps"` and `eval_steps=50` to `TrainingArguments`. This gives a validation loss curve that detects overfitting.
2. **Short-term (1 week):** Build a minimal BBj evaluation suite:
   - 50-100 hand-curated BBj questions with known-correct answers, HELD OUT from training
   - Categories: function knowledge (CHR, HTA, OPEN), GUI patterns (BBjWindow, BBjGrid), file operations, error handling
   - Scoring: compile the generated code with `bbjcpl -N` (binary pass/fail), plus keyword matching for explanation quality
   - Run evaluation after each training run; track scores across runs
3. **Medium-term (2-4 weeks):** Build a BBj HumanEval-style benchmark:
   - 30-50 BBj programming tasks with test assertions
   - Automated scoring via code execution in BBj runtime
   - This becomes the definitive measure of model quality

**Confidence:** HIGH -- The absence of evaluation code is confirmed by reading the training script. The recommendation to hold out validation data is universal in ML practice and not controversial.

**Sources:**
- [SuperAnnotate: Fine-tuning LLMs in 2025](https://www.superannotate.com/blog/llm-fine-tuning) -- "Regularly evaluate the model's performance on validation data to detect and address issues like overfitting"
- [Heavybit: LLM Fine-Tuning Guide for Engineering Teams](https://www.heavybit.com/library/article/llm-fine-tuning) -- "Validation monitors loss curves and other performance indicators to detect issues"
- [Unsloth: Fine-tuning LLMs Guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide) -- Evaluation setup recommendations

---

## High Severity Pitfalls

Mistakes that produce suboptimal results, waste training time, or create hidden quality problems that are difficult to detect.

---

### H-1: Learning Rate 2e-5 Is 10x Lower Than QLoRA Recommendations for This Model Size

**Severity:** HIGH
**Applies to current bbjllm approach:** YES -- `LEARNING_RATE = 2e-5` in training script

**What goes wrong:** The training script uses `2e-5` (0.00002) as the learning rate with a comment "Slightly lower for instruct model." However, the QLoRA literature and practitioner guides recommend significantly higher learning rates:

- **QLoRA paper:** Recommends 2e-4 for small models, 1e-4 for models >33B
- **Unsloth hyperparameters guide:** Recommends 2e-4 as a starting point for LoRA/QLoRA
- **NVIDIA NeMo QLoRA guide:** Uses 1e-4 for large models

The current rate (2e-5) is 5-10x lower than community recommendations. At 2e-5 with only 2 epochs, the adapter weights may not move far enough from their initialization to meaningfully encode BBj knowledge. The model produces output that looks reasonable (because the base Qwen model is already good at code) but has not actually learned much from the BBj-specific training data.

**Why this is tricky to detect:** At very low learning rates, the model still generates plausible code because the base model capabilities dominate. The training loss decreases (slowly), creating an illusion of learning. But the adapter has minimal effect -- you are essentially serving the base model with negligible modifications.

**Warning signs:**
- Training loss decreases very slowly across steps
- Output quality is similar to the base model without fine-tuning
- Adapter weights (in `adapter_model.safetensors`) are very small in magnitude
- Increasing epochs from 2 to 4 helps noticeably (because more steps are needed at the low learning rate)

**Prevention:**
- Start with `1e-4` for the 32B model (QLoRA paper recommendation for >33B models)
- If fine-tuning the Instruct variant (and accepting the risks in C-2), use a lower rate but not this low: `5e-5` to `1e-4`
- Use a learning rate sweep: train for 100 steps each at 5e-5, 1e-4, 2e-4, and compare training loss curves
- The current cosine scheduler and warmup are appropriate; only the base learning rate needs adjustment

**Confidence:** MEDIUM-HIGH -- The QLoRA paper's recommendations are well-established. However, the optimal learning rate depends on the specific dataset, model, and task. The 2e-5 rate is not wrong in all contexts (it is standard for full fine-tuning), but it is unusually conservative for QLoRA where the adapter parameters need larger updates because they are the only trainable weights.

**Sources:**
- [QLoRA Paper (NeurIPS 2023)](https://arxiv.org/abs/2305.14314) -- "2e-4 for small models, 1e-4 for big (>33B) models"
- [Unsloth LoRA Hyperparameters Guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide) -- "2e-4 as a starting point"
- [Databricks LoRA Guide](https://www.databricks.com/blog/efficient-fine-tuning-lora-guide-llms) -- Learning rate recommendations by model size

---

### H-2: Padding to max_length Wastes 50-80% of Each Batch on Empty Tokens

**Severity:** HIGH
**Applies to current bbjllm approach:** YES -- `padding="max_length"` at line 284

**What goes wrong:** The training script pads every example to 1024 tokens (`max_length=MAX_LENGTH`). But analysis of the dataset shows:

| Metric | Value |
|--------|-------|
| Median example length (chars) | 547 |
| P90 example length (chars) | 992 |
| Estimated examples >1024 tokens | ~7 (0.07%) |
| Estimated median token count | ~200 tokens |

For a median example of ~200 tokens padded to 1024, approximately 80% of each training step processes padding tokens. While padding tokens are masked from the loss (labels = -100), they still consume memory and compute for the forward and backward pass through attention layers.

With `batch_size=1` and `gradient_accumulation_steps=32`, each effective batch of 32 examples processes approximately 32 * 1024 = 32,768 tokens, of which roughly 26,000 are padding -- an enormous waste.

**Consequences:**
- Training is 3-5x slower than it needs to be
- GPU memory usage is higher than necessary (attention over 1024 tokens per example)
- On a remote GPU server (where the team pays by the hour), this directly translates to higher cost

**Prevention:**
- **Dynamic padding:** Use `padding=True` (pad to longest in batch) instead of `padding="max_length"`. With TRL's `SFTTrainer`, this is the default behavior.
- **Packing:** Use SFTTrainer's `packing=True` to concatenate multiple short examples into a single 1024-token sequence. This eliminates padding entirely and can increase training throughput by 3-5x. Given that the median example is ~200 tokens, you could pack ~5 examples per sequence.
- **If staying with raw Trainer:** Use a `DataCollatorWithPadding` instead of `default_data_collator` to enable dynamic padding per batch.

**Confidence:** HIGH -- The padding behavior is visible in the code. The dataset statistics are computed directly from the data. Dynamic padding and packing are well-documented efficiency improvements in the TRL and Transformers documentation.

---

### H-3: 60 Training Examples Have Corrupted Newlines (Literal `\n` in Code)

**Severity:** HIGH
**Applies to current bbjllm approach:** YES -- confirmed by dataset analysis

**What goes wrong:** 60 examples in the dataset (40 with only escaped newlines, 20 with a mix) contain literal backslash-n (`\n`) characters instead of actual newline characters in the assistant's response. For example, line 13 of the dataset:

```json
{"messages": [..., {"role": "assistant", "content": "```bbj\\nLET FLAG = 1\\nIF ! (FLAG) THEN PRINT \"False\" ELSE PRINT \"True\"\\n```"}]}
```

When rendered, this produces a single line: `` ```bbj\nLET FLAG = 1\nIF ! ... `` instead of properly formatted multi-line BBj code. The model learns to generate code with literal `\n` characters instead of actual newlines.

**Why it matters for BBj:** BBj code is line-oriented (like all BASIC dialects). A `\n` in the middle of a PRINT statement is not valid BBj. If the model learns to emit literal `\n` from these 60 examples, it will occasionally produce uncompilable code that looks correct at a glance but fails when pasted into a BBj IDE.

**Warning signs:**
- Generated BBj code appears on a single line with `\n` visible
- `bbjcpl -N` reports syntax errors on generated code due to literal backslash characters
- Code blocks in IDE completions display as single long lines

**Prevention:**
- Sanitize the dataset: Find all examples where assistant content contains literal `\n` (not actual newlines) and replace with actual newline characters
- Add a validation step to the data pipeline that rejects examples with literal escape sequences in code blocks
- This is a 10-minute fix that affects ~0.6% of the data, but those 60 examples can cause disproportionate quality issues in a 10K dataset

**Confidence:** HIGH -- Confirmed by direct inspection of the dataset. Line 13's repr() output shows the literal backslash-n characters unambiguously.

---

### H-4: 375 Duplicate User Prompts Create Memorization Bias

**Severity:** HIGH
**Applies to current bbjllm approach:** YES -- confirmed by dataset analysis

**What goes wrong:** The dataset contains 375 unique user prompts that appear more than once, covering 766 total examples (~7.7% of the dataset). The most common duplicates appear 3 times each. Some duplicates have slightly different assistant responses (e.g., one with REM comments, one without), but many are identical or near-identical.

Examples of exact duplicates found:
- "Write BBj code to pad a username field to 12 characters." (lines 5 and 9 -- one with REM comments, one without)
- "Write BBj code to check out a license for PAYROLL feature, version 3.0" (lines 6 and 10)
- "Use MAX() to determine the maximum of mixed literals and variables." (lines 8 and 11)

**Why duplicates are particularly harmful for niche domains:** With only 10K examples for a language with near-zero web presence, every example is precious. Duplicates do not add new information but increase the model's confidence on those specific patterns. The model becomes disproportionately good at answering "Write BBj code to pad a username field" but no better at generalizing to novel BBj tasks. This is a form of dataset bias that reduces effective dataset size.

**Worse case -- conflicting duplicates:** If the same user prompt appears with different assistant responses, the model receives contradictory training signal, increasing loss variance and potentially learning neither response well.

**Prevention:**
- Deduplicate by user prompt: Keep only one example per unique user prompt. If duplicates have different responses, keep the higher-quality one (longer, with code fences, with REM comments).
- After deduplication, the effective dataset size drops from ~9,923 to ~9,550. This is a minor loss of quantity but a meaningful gain in diversity.
- Consider near-duplicate detection: examples that differ only by case, punctuation, or trivial word changes should also be flagged and reviewed.

**Confidence:** HIGH -- Confirmed by direct dataset analysis. Counts and examples are exact.

---

### H-5: Uniform System Prompt Reduces Model Adaptability

**Severity:** HIGH
**Applies to current bbjllm approach:** YES -- single system prompt across all 9,923 examples

**What goes wrong:** Every training example uses the identical system prompt: "You are an expert BBj programmer who helps users write and understand BBj code." This teaches the model that it should ONLY respond in this persona. If the system prompt changes at inference time (e.g., "You are an IDE code completion engine. Complete the following BBj code fragment."), the model may behave unpredictably because it has never seen any other instruction framing.

**Research context:** A 2025 paper on system message generation (arxiv:2502.11330) found that "training open-source models with system messages tailored to diverse contexts is significantly more beneficial to align user instructions than using a common system message." Diverse system prompts help the model generalize across different use contexts.

**Specific risk for the bbjllm project:** The documented use cases include:
1. IDE code completion (Ollama serving) -- needs a code-completion-oriented prompt
2. Chat-based Q&A (documentation chat) -- needs an explanation-oriented prompt
3. MCP tool integration (generate_bbj_code) -- needs a structured-output prompt

All three use cases require different system prompts at inference. A model trained exclusively on one prompt may underperform when given a different one.

**Prevention:**
- Add 3-5 system prompt variations to the training data, distributed across examples:
  - "You are an expert BBj programmer who helps users write and understand BBj code." (current, keep for ~60%)
  - "You are a BBj code completion engine. Complete the code concisely." (~15%)
  - "You are a BBj programming assistant. Explain your code clearly with comments." (~15%)
  - "Generate BBj code for the following task. Include error handling." (~10%)
- This requires modifying the dataset generation pipeline but does not require new training examples -- only varying the system prompt on existing ones.
- If the model will be used primarily through Ollama with a fixed Modelfile, this is MEDIUM severity. If it will be used with varied prompts across different tools, this is HIGH.

**Confidence:** MEDIUM-HIGH -- The research on system prompt diversity is recent and well-supported. The specific impact on a code-generation model trained on a niche language is less well-studied, but the general principle (diverse training inputs improve generalization) is well-established.

**Sources:**
- [System Message Generation for User Preferences](https://arxiv.org/abs/2502.11330) -- Diverse system messages improve instruction following
- [Preserving Diversity in Supervised Fine-Tuning (ICLR 2025)](https://arxiv.org/abs/2408.16673) -- SFT with CE loss reduces output diversity

---

### H-6: bitsandbytes 0.43.0 Has a Critical QLoRA Memory Bug (Fixed in 0.43.2)

**Severity:** HIGH
**Applies to current bbjllm approach:** YES -- pinned to `bitsandbytes==0.43.0`

**What goes wrong:** Version 0.43.0 of bitsandbytes contains a bug where activations are unnecessarily allocated for frozen (non-LoRA) parameters during QLoRA training. This was fixed in version 0.43.2 with the change "delete useless buffered activation" (#1270). The memory impact is substantial:

| Model Size | seq_len=1024 | seq_len=4096 |
|-----------|-------------|-------------|
| 32B (estimated) | ~5-10 GB wasted | ~20-40 GB wasted |
| 70B (documented) | 10.1 GB wasted | ~40 GB wasted |
| 405B (documented) | 39 GB wasted | ~156 GB wasted |

For the 32B model at seq_len=1024, this bug wastes an estimated 5-10 GB of GPU memory that could be used for larger batch sizes, longer sequences, or simply avoiding OOM errors.

**Implications for the bbjllm project:** The training runs on a remote GPU server. Wasted GPU memory may have caused OOM errors that were worked around by reducing batch size or sequence length, when the actual fix was a 2-line dependency update.

**Prevention:**
- Update to `bitsandbytes>=0.43.2` (minimum fix version)
- Better yet, update to `bitsandbytes>=0.45.0` which includes Intel GPU support, macOS support, reduced wheel size, and further QLoRA optimizations
- The latest stable version as of January 2026 is 0.49.1

**Note:** There is a reported issue (GitHub #830) that updating bitsandbytes to versions 0.44+ can cause training slowdowns in some configurations. Test on a short run (100 steps) before committing to a full training run with the updated version.

**Confidence:** HIGH -- The bug and fix are documented in the official bitsandbytes changelog and release notes (v0.43.2). The memory savings are documented with specific numbers for various model sizes.

**Sources:**
- [bitsandbytes 0.43.2 Release Notes](https://github.com/bitsandbytes-foundation/bitsandbytes/releases/tag/0.43.2) -- QLoRA memory bug fix details
- [Discussion #1291: Significant QLoRA Mem Savings](https://github.com/bitsandbytes-foundation/bitsandbytes/discussions/1291) -- Community confirmation of memory savings
- [Issue #830: Training Slowdown After Upgrade](https://github.com/bitsandbytes-foundation/bitsandbytes/issues/830) -- Regression risk with newer versions

---

## Medium Severity Pitfalls

Mistakes that cause suboptimal results, inefficiency, or technical debt but do not prevent the model from functioning.

---

### M-1: 1024 Token Limit Is Adequate for This Dataset but Limits Future Growth

**Severity:** MEDIUM (currently adequate, HIGH if dataset expands)
**Applies to current bbjllm approach:** YES -- `MAX_LENGTH = 1024`

**What goes wrong:** The MAX_LENGTH of 1024 tokens truncates any example that exceeds this length. Analysis of the current dataset shows:

| Metric | Value |
|--------|-------|
| Total examples | 9,923 |
| Estimated >1024 tokens | ~7 (0.07%) |
| Longest example (chars) | 4,896 |
| Longest example (est. tokens) | ~1,450 |

**Current assessment:** 1024 tokens is adequate for 99.93% of the current training data. Only ~7 examples may be truncated, and those are the longest "comprehensive integration" examples. The code comment "Increased for Qwen (supports up to 32K)" suggests 1024 was chosen as a balance.

**The future risk:** Real-world BBj programs are longer than the training examples. A typical BBj GUI application (like the `cust-bbj.txt` in the PDF reference) is 100-200 lines, easily exceeding 2048 tokens. If the training data grows to include full program examples (which it should, for real-world utility), 1024 will truncate most of them. The model will never learn to generate programs longer than ~50 lines of BBj.

**At inference time:** When deployed via Ollama for IDE completions, the model's context window is set independently. But a model trained on max 1024 tokens may degrade when asked to generate or process longer sequences, because it has never seen them during training.

**Prevention:**
- For the current dataset: 1024 is fine. Do not change it just for the ~7 truncated examples.
- When expanding the dataset with longer examples: Increase to 2048 or 4096. The bitsandbytes QLoRA memory fix (H-6) will help accommodate longer sequences.
- Consider a two-phase approach: train at 1024 for short Q&A examples, then continue training at 2048-4096 with longer program examples (curriculum learning).
- The memory cost scales linearly with sequence length for QLoRA (quadratic attention is only in the frozen base model forward pass). Going from 1024 to 2048 roughly doubles peak memory from the adapter's perspective.

**Confidence:** HIGH for current assessment (dataset statistics are exact). MEDIUM for the future growth prediction (depends on what training data is added).

---

### M-2: Pinned Library Versions Are 18 Months Stale

**Severity:** MEDIUM
**Applies to current bbjllm approach:** YES -- all versions from Aug 2024

**What goes wrong:** The `starttrain.sh` pins specific versions of all ML libraries from mid-2024:

| Library | Pinned | Latest (Jan 2026) | Age |
|---------|--------|-------------------|-----|
| transformers | 4.44.0 | 4.57.6 | 18 months |
| peft | 0.12.0 | 0.15+ | 18 months |
| trl | 0.9.6 | 0.14+ | 18 months |
| bitsandbytes | 0.43.0 | 0.49.1 | 20 months |
| accelerate | 0.33.0 | 1.3+ | 18 months |
| datasets | 2.19.0 | 3.3+ | 18 months |

**What has been missed (HIGH impact):**
- bitsandbytes QLoRA memory bug fix (H-6) -- saves 5-10 GB of GPU memory
- PEFT 0.13+: EVA initialization (better LoRA convergence), lora_bias parameter, SHiRA adapters
- TRL improvements: dataset shuffling, enhanced loss functions, Liger Kernel integration (20% throughput improvement)
- Transformers v5: major release with new weight loader, updated PEFT integration

**What has been missed (MEDIUM impact):**
- Security patches across all libraries
- Qwen3 model support (future migration path)
- Improved gradient checkpointing implementations
- Better multi-GPU training support

**Risk of updating:** Updating all libraries simultaneously is risky. Version incompatibilities between transformers, peft, trl, and bitsandbytes are common. The original version pins were chosen to resolve a `use_seedable_sampler` compatibility error (noted in `starttrain.sh`).

**Prevention strategy -- staged updates:**
1. **Immediate (low risk):** Update bitsandbytes from 0.43.0 to 0.43.2 (same minor version, only the memory bug fix)
2. **Short-term (moderate risk):** Update bitsandbytes to 0.45.x, peft to 0.14.x, and test compatibility. Run a 100-step training sanity check.
3. **Medium-term:** Consider a full stack update to transformers 4.50+, peft 0.15+, trl 0.13+. Test thoroughly. This may require script changes due to API updates in TRL's SFTTrainer.
4. **Do NOT jump to transformers v5.x yet** -- this is a major version with breaking changes. Wait for the ecosystem to stabilize.

**Confidence:** HIGH -- Version numbers are confirmed from the training script. Release dates are confirmed from PyPI and GitHub. Specific improvements are confirmed from release notes.

**Sources:**
- [Transformers Releases](https://github.com/huggingface/transformers/releases) -- Full changelog
- [PEFT Releases](https://github.com/huggingface/peft/releases) -- EVA, SHiRA, lora_bias improvements
- [TRL Releases](https://github.com/huggingface/trl/releases) -- SFTTrainer improvements
- [bitsandbytes CHANGELOG.md](https://github.com/bitsandbytes-foundation/bitsandbytes/blob/main/CHANGELOG.md) -- Memory fix and QLoRA improvements

---

### M-3: LoRA Rank 32 / Alpha 64 Is Reasonable but Likely Overkill for 10K Examples

**Severity:** MEDIUM
**Applies to current bbjllm approach:** YES -- `LORA_R=32`, `LORA_ALPHA=64`

**What goes wrong:** Rank 32 with 7 target modules (q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj) creates a large number of trainable parameters relative to the dataset size. For a 32B model:

- Estimated trainable parameters at rank 32 with 7 modules: ~200-300M parameters
- Training examples: 9,923
- **Ratio: ~20,000-30,000 trainable parameters per training example**

This is an extremely high parameter-to-data ratio. While LoRA constrains the update space (preventing the worst overfitting), higher rank means more capacity to memorize the training set rather than learn generalizable patterns.

**The tradeoff:** Higher rank can capture more complex patterns (useful for learning a new programming language). But with only 10K examples, rank 16 (or even rank 8) might learn the same BBj patterns with less overfitting risk. The QLoRA paper found that performance plateaus above rank 16 for most tasks.

**Current alpha ratio is correct:** Alpha 64 / Rank 32 = 2x ratio, which matches Microsoft's LoRA codebase defaults and is standard practice.

**Prevention:**
- Try rank 16 as the default, compare with rank 32 using the evaluation framework (requires C-3 to be fixed first)
- If rank 32 is needed, consider reducing epochs from 2 to 1 to compensate for the higher capacity
- Monitor trainable parameters with `model.print_trainable_parameters()` (already in the script) and compare the percentage against recommendations (~0.5-2% of total parameters)
- The dropout of 0.05 is appropriate for a 32B model and helps slightly with overfitting

**Confidence:** MEDIUM -- The parameter count is estimated (not computed from the actual model). The general principle (fewer parameters for smaller datasets) is well-established, but the optimal rank for niche-language code generation is not well-studied. Rank 32 is not wrong -- it is a reasonable starting point -- but rank 16 should be tried for comparison.

**Sources:**
- [QLoRA Paper](https://arxiv.org/abs/2305.14314) -- Performance plateaus above rank 16
- [Entry Point AI: LoRA Fine-tuning & Hyperparameters Explained](https://www.entrypointai.com/blog/lora-fine-tuning/) -- Rank selection guidance
- [Databricks LoRA Guide](https://www.databricks.com/blog/efficient-fine-tuning-lora-guide-llms) -- "Use rank=16, alpha=32 as a starting point"

---

### M-4: 2 Epochs on 10K Examples Is Conservative but Overfitting Risk Depends on Other Fixes

**Severity:** MEDIUM
**Applies to current bbjllm approach:** YES -- `NUM_EPOCHS = 2`

**What goes wrong:** The interaction between epochs, learning rate, rank, and evaluation is complex. In isolation, 2 epochs is within the recommended range (1-3 epochs for instruction fine-tuning). But combined with other factors:

| Factor | Current | Risk Direction |
|--------|---------|---------------|
| Epochs | 2 | Moderate |
| Learning rate | 2e-5 (very low) | Undertraining |
| Rank | 32 (high) | Overfitting |
| Completion masking | None (C-1) | Diluted signal |
| Evaluation | None (C-3) | Cannot detect overfit |

If the learning rate is increased to 1e-4 (per H-1), 2 epochs may be TOO MANY because the model will learn faster. If completion masking is added (per C-1), the gradient signal becomes more focused, and 1 epoch may suffice.

**The conservative approach:**
- With current settings (2e-5 LR, no masking): 2 epochs likely undertrain. The model may need 3-4 epochs because the learning rate is too low and the signal is diluted.
- With recommended fixes (1e-4 LR, completion masking): 1 epoch may be optimal. Monitor validation loss and stop if it starts increasing.

**Prevention:**
- Fix C-1 (completion masking) and H-1 (learning rate) first, THEN tune epochs
- Start with 1 epoch after the fixes, evaluate, and add a second epoch only if the model is clearly undertrained
- Use checkpoint saving (`save_steps=50`, already configured) to pick the best checkpoint within an epoch rather than always using the final checkpoint

**Confidence:** MEDIUM -- The interaction effects make it impossible to recommend a specific epoch count without experimentation. The guidance here is directional: epochs should be tuned AFTER other fixes are applied.

---

### M-5: Response Format Inconsistency Across Training Examples

**Severity:** MEDIUM
**Applies to current bbjllm approach:** YES -- confirmed by dataset analysis

**What goes wrong:** The dataset has inconsistent formatting across assistant responses:

| Format | Count | Percentage |
|--------|-------|------------|
| Code with fences (` ```bbj ... ``` `) | 8,451 | 85.2% |
| Text-only explanation | 1,012 | 10.2% |
| Mixed (text + fenced code) | 441 | 4.4% |
| Raw code (no fences, no explanation) | 19 | 0.2% |

Additionally:
- Some code blocks use ` ``` ` without the `bbj` language tag
- Some examples use `>` prefix for code lines (line-by-line quoting, like email style) instead of code fences
- 257 examples contain raw BBj code keywords (PRINT, LET, REM) without any code fences or explanation structure

The model learns a probability distribution over these formats. At inference time, it may randomly switch between fenced code, raw code, and quoted code -- producing inconsistent output that confuses IDE completion engines and chat interfaces.

**Why this matters for Ollama/IDE integration:** IDE completions need predictable output format. If the model sometimes produces ` ```bbj\n... ``` ` and sometimes produces raw code, the IDE extension cannot reliably extract the code from the response. Similarly, the chat UI needs consistent markdown formatting to render properly.

**Prevention:**
- Standardize all code examples to use ` ```bbj ... ``` ` fencing
- Standardize response structure: for code questions, always use fenced code blocks; for explanation questions, use structured text with inline code references
- Remove the `>` quoted code format (lines like `>PRINT "hello"`) and replace with proper code fences
- This is a data preprocessing step that can be automated

**Confidence:** HIGH -- Format counts are computed directly from the dataset.

---

### M-6: No `save_only_model=True` Limits Checkpoint Usability

**Severity:** MEDIUM
**Applies to current bbjllm approach:** PARTIALLY -- `save_only_model=True` IS set (line 241), but `save_safetensors=True` (line 240) combined with the current save interval (`save_steps=50`) may produce excessive checkpoint volume

**What goes wrong:** With `save_steps=50` and approximately 310 total steps per epoch (9,923 examples / 32 effective batch size), each epoch creates ~6 checkpoints, totaling ~12 checkpoints over 2 epochs. Each checkpoint for a 32B model's LoRA adapter is relatively small (~100-200MB with rank 32), but the accumulated storage on the remote GPU server may be substantial. More importantly, there is no `save_total_limit` parameter set, meaning old checkpoints are never deleted.

**Prevention:**
- Add `save_total_limit=3` to `TrainingArguments` to keep only the 3 most recent checkpoints
- Alternatively, increase `save_steps` to 100 (saves every ~32% of an epoch instead of every ~16%)
- The `save_only_model=True` is correctly set, which avoids saving optimizer state

**Confidence:** HIGH -- Configuration is confirmed from the training script.

---

### M-7: Catastrophic Forgetting Is Real but Mitigated by QLoRA Architecture

**Severity:** MEDIUM (not a BLOCKER due to QLoRA's inherent protection)
**Applies to current bbjllm approach:** YES

**What goes wrong:** A common concern: 10K BBj examples on a 32B model -- will the model forget how to code in Python, Java, etc.? Research on this topic is nuanced:

**What QLoRA protects against:**
- The base model weights are frozen. Python, Java, and general coding knowledge stored in those weights is preserved.
- The LoRA adapter adds a small perturbation. At inference, the adapter can be removed to restore the exact base model.

**What QLoRA does NOT protect against:**
- The combined model (base + adapter) can still exhibit behavior shifts. The adapter may steer the model toward BBj patterns even when asked about Python.
- Research (2025) confirms that "LoRA-tuned models can forget significant parts of the pre-training distribution."
- The alignment tax: instruction-following quality may degrade (see C-2).

**Specific risk for a niche language:** Because BBj syntax is superficially similar to other BASIC dialects and even some general programming patterns, the adapter may create confusions. For example, if the model learns that `OPEN` in BBj takes specific parameters, it might apply that knowledge when asked about `open()` in Python.

**Why MEDIUM not HIGH:** The adapter can be toggled on/off. At inference via Ollama, users specifically invoke the BBj model when they want BBj. The risk is that the BBj model degrades on closely related tasks (like explaining general BASIC concepts), not that the base model is permanently damaged.

**Prevention:**
- Include a small number of non-BBj examples in the training data (5-10%) that demonstrate general coding knowledge. This acts as a regularizer.
- Test the fine-tuned model on general coding questions (Python, Java) to measure forgetting
- Use the adapter selectively -- only apply it when BBj code is being generated

**Confidence:** MEDIUM -- The theoretical risk is well-documented. The practical magnitude for code models trained via QLoRA on niche languages is less well-studied. The frozen-weights protection is real but not absolute.

**Sources:**
- [Leveraging QLoRA Without Catastrophic Forgetting](https://towardsdatascience.com/leveraging-qlora-for-fine-tuning-of-task-fine-tuned-models-without-catastrophic-forgetting-d9bcd594cff4/) -- LoRA forgetting behavior
- [Interpretable Catastrophic Forgetting via Instruction Vector](https://arxiv.org/abs/2406.12227) -- How instruction tuning modifies model behavior
- [Mitigating Forgetting in LLM Fine-Tuning](https://arxiv.org/abs/2506.09428) -- Recent mitigation approaches

---

## Low Severity Pitfalls

Issues that cause minor inefficiencies or are nice-to-fix but do not significantly impact model quality.

---

### L-1: `pad_token = eos_token` May Cause Subtle Generation Issues

**Severity:** LOW
**Applies to current bbjllm approach:** YES -- line 123

**What goes wrong:** The script sets `tokenizer.pad_token = tokenizer.eos_token` when `pad_token is None`. For Qwen2.5-Coder, the tokenizer may already have a designated pad token. Overriding it with `eos_token` means the model sees the same token for "end of sequence" and "padding," which can cause the model to end generation prematurely (confusing "I should stop generating" with "this was padding during training").

**Prevention:**
- Check if Qwen2.5-Coder's tokenizer already has a pad_token before overriding
- The Qwen2.5 tokenizer uses `<|endoftext|>` as eos and typically has `<|fim_pad|>` or similar available
- If a separate pad token exists, use it instead of eos

**Confidence:** MEDIUM -- This is a known issue in the community but the Qwen tokenizer may handle it correctly. Needs verification against the specific tokenizer configuration.

---

### L-2: `max_grad_norm=0.3` Is More Aggressive Than Standard

**Severity:** LOW
**Applies to current bbjllm approach:** YES -- line 232

**What goes wrong:** The gradient clipping norm of 0.3 is lower than the standard 1.0. This aggressively clips gradients, which can slow training convergence (effectively reducing the learning rate further on steps with large gradients). Combined with the already-low learning rate of 2e-5, this creates a very conservative optimization regime.

**Prevention:**
- If the learning rate is increased to 1e-4, keep `max_grad_norm=0.3` as a safety net
- If the learning rate stays at 2e-5, consider increasing `max_grad_norm` to 1.0 (the standard value)
- This is unlikely to cause major issues but may contribute to the undertrained-appearance noted in H-1

**Confidence:** MEDIUM -- The optimal gradient clipping value depends on the specific training dynamics. 0.3 is not wrong but is unusually conservative.

---

### L-3: `TOKENIZERS_PARALLELISM=false` May Slow Dataset Preprocessing

**Severity:** LOW
**Applies to current bbjllm approach:** YES -- line 17

**What goes wrong:** Setting `TOKENIZERS_PARALLELISM=false` disables multi-threaded tokenization. This avoids a known deadlock warning but makes dataset preprocessing slower. For 10K examples, this adds perhaps 10-30 seconds to preprocessing -- negligible compared to training time.

**Prevention:** Leave as-is. The deadlock warning is more disruptive than the slowdown. This is a standard workaround.

**Confidence:** HIGH -- This is a well-known setting with minimal impact.

---

### L-4: Training Script Not Structured for Experiment Tracking

**Severity:** LOW
**Applies to current bbjllm approach:** YES -- `report_to="none"` at line 236

**What goes wrong:** Training metrics are only logged to stdout with `logging_steps=5`. There is no integration with Weights & Biases, TensorBoard, or any experiment tracking tool. This means:
- Loss curves are only visible in terminal output (lost if session ends)
- No comparison between training runs
- No hyperparameter sweep tracking

**Prevention:**
- Minimal: Set `report_to="tensorboard"` and specify a `logging_dir`. TensorBoard requires no account or API key.
- Better: Set `report_to="wandb"` if the team has a Weights & Biases account. This enables comparing runs, tracking hyperparameters, and sharing results.
- Even simpler: Redirect stdout to a log file (`python train_qwen_32b.py 2>&1 | tee training_$(date +%Y%m%d_%H%M%S).log`)

**Confidence:** HIGH -- The `report_to` setting is confirmed from the training script.

---

## Phase-Specific Warning Matrix

| Concern Area | Pitfall | Severity | Fix Effort | Fix Before Next Training Run? |
|-------------|---------|----------|------------|------------------------------|
| Training signal | C-1: Full sequence training (no completion masking) | BLOCKER | 2-4 hours | YES |
| Model choice | C-2: Instruct model degeneration risk | BLOCKER | 1-2 days (if switching to Base) | EVALUATE |
| Evaluation | C-3: No validation set or evaluation framework | BLOCKER | 1 day (basic), 1 week (proper) | YES |
| Learning rate | H-1: 10x too low for QLoRA | HIGH | 5 minutes | YES |
| Efficiency | H-2: 80% of each batch is padding | HIGH | 1-2 hours | YES |
| Data quality | H-3: 60 examples with corrupted newlines | HIGH | 30 minutes | YES |
| Data quality | H-4: 375 duplicate user prompts | HIGH | 1-2 hours | YES |
| Data diversity | H-5: Uniform system prompt | HIGH | 2-4 hours | RECOMMENDED |
| Dependencies | H-6: bitsandbytes QLoRA memory bug | HIGH | 5 minutes | YES |
| Sequence length | M-1: 1024 limit adequate now, constrains growth | MEDIUM | N/A (future) | NO |
| Dependencies | M-2: 18-month-stale library stack | MEDIUM | 4-8 hours (staged) | STAGED |
| Hyperparameters | M-3: Rank 32 possibly overkill | MEDIUM | Requires eval framework | AFTER C-3 |
| Hyperparameters | M-4: Epoch count depends on other fixes | MEDIUM | Requires eval framework | AFTER C-3 |
| Data quality | M-5: Inconsistent response formatting | MEDIUM | 2-4 hours | RECOMMENDED |
| Checkpoints | M-6: No checkpoint limit | MEDIUM | 1 minute | YES |
| Forgetting | M-7: Catastrophic forgetting (mitigated by QLoRA) | MEDIUM | Requires eval framework | AFTER C-3 |

---

## Recommended Fix Order

Based on dependencies and impact, fix these issues in this order:

### Before Next Training Run (1-2 days)

1. **H-6: Update bitsandbytes** to 0.43.2+ (5 minutes, immediate memory savings)
2. **H-3: Fix corrupted newlines** in 60 training examples (30 minutes)
3. **H-4: Deduplicate** the dataset (1-2 hours)
4. **C-1: Add completion masking** -- either switch to SFTTrainer or add manual masking (2-4 hours)
5. **H-1: Increase learning rate** to 1e-4 (5 minutes)
6. **C-3: Add validation split** -- hold out 500-1000 examples, add eval_strategy to training args (2-4 hours)
7. **H-2: Switch to dynamic padding** or packing (1-2 hours)
8. **M-6: Add save_total_limit=3** (1 minute)

### Before Second Training Run (1 week)

9. **H-5: Add system prompt diversity** (2-4 hours)
10. **M-5: Standardize response formatting** (2-4 hours)
11. **C-3 continued: Build minimal evaluation suite** -- 50-100 held-out BBj questions with bbjcpl validation (1 week)
12. **M-2: Staged dependency update** -- bitsandbytes 0.45+, peft 0.14+ (4-8 hours including testing)

### Strategic Decision (requires team discussion)

13. **C-2: Evaluate Base vs Instruct** -- run one training on Base model, compare with Instruct results using the evaluation suite
14. **M-3/M-4: Hyperparameter tuning** -- use evaluation framework to compare rank 16 vs 32, 1 vs 2 epochs

---

## Sources

### QLoRA and Fine-Tuning Research
- [QLoRA Paper (Dettmers et al., NeurIPS 2023)](https://arxiv.org/abs/2305.14314) -- Original QLoRA paper with hyperparameter recommendations
- [Shadow-FT: Tuning Instruct via Base](https://arxiv.org/abs/2505.12716) -- Instruct model degeneration and mitigation
- [Leveraging QLoRA Without Catastrophic Forgetting](https://towardsdatascience.com/leveraging-qlora-for-fine-tuning-of-task-fine-tuned-models-without-catastrophic-forgetting-d9bcd594cff4/) -- Forgetting in LoRA-tuned models
- [Preserving Diversity in Supervised Fine-Tuning (ICLR 2025)](https://arxiv.org/abs/2408.16673) -- CE loss reduces output diversity

### Hyperparameter Guides
- [Unsloth LoRA Hyperparameters Guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide) -- Learning rate, rank, epoch recommendations
- [Databricks LoRA Guide](https://www.databricks.com/blog/efficient-fine-tuning-lora-guide-llms) -- Rank and alpha selection
- [Lightning AI: LoRA Insights from Hundreds of Experiments](https://lightning.ai/pages/community/lora-insights/) -- Practical findings

### Qwen-Specific
- [Qwen2.5-Coder Technical Report](https://arxiv.org/pdf/2409.12186) -- Model architecture and capabilities
- [Qwen2.5-Coder Family Blog](https://qwenlm.github.io/blog/qwen2.5-coder-family/) -- Official Base vs Instruct guidance
- [Qwen Fine-Tuning with Unsloth](https://unsloth.ai/blog/qwen-coder) -- Community fine-tuning guide

### Library Version Information
- [bitsandbytes 0.43.2 QLoRA Memory Fix](https://github.com/bitsandbytes-foundation/bitsandbytes/discussions/1291) -- Critical bug fix details
- [bitsandbytes Changelog](https://github.com/bitsandbytes-foundation/bitsandbytes/blob/main/CHANGELOG.md) -- Full version history
- [PEFT Releases](https://github.com/huggingface/peft/releases) -- EVA, SHiRA, and other improvements
- [TRL Releases](https://github.com/huggingface/trl/releases) -- SFTTrainer improvements
- [Transformers Releases](https://github.com/huggingface/transformers/releases) -- Version 4.44 to 4.57 changes

### Training Data and Evaluation
- [System Message Generation (arxiv:2502.11330)](https://arxiv.org/abs/2502.11330) -- System prompt diversity improves instruction following
- [To Mask or Not to Mask](https://towardsdatascience.com/to-mask-or-not-to-mask-the-effect-of-prompt-tokens-on-instruction-tuning-016f85fd67f4/) -- Completion masking research
- [HuggingFace TRL SFTTrainer](https://huggingface.co/docs/trl/sft_trainer) -- Default completion-only loss, packing support
- [SuperAnnotate: Fine-tuning LLMs 2025](https://www.superannotate.com/blog/llm-fine-tuning) -- Evaluation and overfitting detection
- [LLM Benchmarks 2026](https://llm-stats.com/benchmarks) -- Current evaluation landscape

---

*Research conducted 2026-02-06. All pitfalls verified against the actual bbjllm repo at `/Users/beff/_workspace/bbjllm/` (training script `train_qwen_32b.py`, dataset `dataset.jsonl` with 9,923 examples, environment script `starttrain.sh`). Dataset statistics computed from direct analysis of `dataset.jsonl`. Library versions confirmed from pinned dependencies in `starttrain.sh`. Previous PITFALLS.md covered v1.5 RAG system integration pitfalls; this document covers fine-tuning pitfalls for v1.7 documentation refresh.*
