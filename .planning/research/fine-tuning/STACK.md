# Technology Stack: LLM Fine-Tuning for BBj Code Generation

**Project:** BBj AI Strategy -- Fine-Tuning Toolchain Evaluation
**Researched:** 2026-02-06
**Scope:** Model selection, fine-tuning framework, training approach, evaluation, serving
**Overall confidence:** HIGH (versions verified via PyPI, GitHub, and web search as of 2026-02-06)

---

## Executive Summary

The bbjllm repo's current approach (Qwen2.5-Coder-32B-Instruct + HuggingFace PEFT QLoRA) is fundamentally sound but uses severely outdated library versions and makes a debatable model choice. The documentation in Chapter 3 (recommending Qwen2.5-Coder-7B-Base with Unsloth) is closer to the right answer for this use case but also needs updates. This document provides the definitive 2026 recommendation.

**Key findings:**

1. **Model:** Qwen2.5-Coder-32B-Instruct is a defensible choice but overkill for the current dataset and hardware. Qwen2.5-Coder-14B-Base offers the best tradeoff for a niche-language fine-tuning project with ~10K examples. Start with 14B, scale to 32B if evaluation warrants it.

2. **Framework:** The bbjllm PEFT stack is 6+ major versions behind on every library. Unsloth remains the superior framework for single/dual-GPU QLoRA, delivering 2-3x speed and 70% less VRAM with zero accuracy loss. Switch to Unsloth.

3. **Approach:** QLoRA remains the correct approach. The current rank=32, alpha=64 settings are reasonable. Two-stage training (continued pretraining then instruction fine-tuning) is strongly recommended for a zero-representation language like BBj but must use the Base model, not Instruct, for Stage 1.

4. **Serving:** Ollama (now v0.15.x) remains the right choice for customer self-hosting. vLLM is better for centralized team serving with LoRA hot-swapping.

---

## 1. Model Landscape (February 2026)

### Current State of Code Models

The code model landscape has shifted dramatically since Qwen2.5-Coder's release in September 2024. Here is the current picture:

| Model Family | Available Sizes (Dense) | Release | License | FIM | Fine-Tune Friendly | Notes |
|---|---|---|---|---|---|---|
| **Qwen2.5-Coder** | 0.5B, 1.5B, 3B, 7B, 14B, 32B | Sep 2024 | Apache 2.0 | Yes | Yes | Proven ecosystem, best fine-tuning support |
| **Qwen3** (general) | 0.6B, 1.7B, 4B, 8B, 14B, 32B | Apr 2025 | Apache 2.0 | Yes | Yes | General model, not code-specialized |
| **Qwen3-Coder** | 30B-A3B (MoE), 480B-A35B (MoE) | Jul 2025 | Apache 2.0 | Yes | Difficult | MoE only, no dense variants for fine-tuning |
| **Qwen3-Coder-Next** | 80B-A3B (ultra-sparse MoE) | Feb 2026 | Apache 2.0 | Yes | Difficult | 3B active params, 512 experts, agentic focus |
| **DeepSeek-V3** | 671B MoE (37B active) | Dec 2024 | Custom | Yes | No (too large) | Inference only, not practical for fine-tuning |
| **DeepSeek-V4** | TBD | ~Feb 17, 2026 | Expected open-weight | TBD | TBD | Not yet released; rumors only |
| **CodeLlama** | 7B, 13B, 34B, 70B | Aug 2023 | Llama 2 | Yes | Yes | Surpassed by Qwen family on all benchmarks |
| **StarCoder2** | 3B, 7B, 15B | Feb 2024 | BigCode Open | Yes | Yes | Benchmark-surpassed by Qwen family |

**Confidence:** HIGH -- Model availability verified via HuggingFace collections and official GitHub repos.

### Has Qwen3-Coder Been Released?

Yes. Qwen3-Coder was released in July 2025, with Qwen3-Coder-Next following in February 2026. However, **all Qwen3-Coder variants are Mixture-of-Experts (MoE) architectures**, not dense models. The available variants are:

- **Qwen3-Coder-480B-A35B-Instruct:** 480B total, 35B active. For inference, not fine-tuning.
- **Qwen3-Coder-30B-A3B-Instruct:** 30B total, 3B active. Potentially fine-tunable but sparse.
- **Qwen3-Coder-Next:** 80B total, 3B active, 512 experts. Ultra-sparse, designed for agentic coding.

None of these are suitable for traditional QLoRA fine-tuning on a niche language. MoE models have different fine-tuning dynamics -- you need to target expert layers specifically, and the research on QLoRA for MoE code models is nascent. The standard Qwen3 (general) lineup does have dense models (8B, 14B, 32B) but these are general-purpose, not code-specialized.

**Recommendation:** Qwen2.5-Coder remains the best choice for dense-model code fine-tuning as of February 2026. When Qwen4-Coder or a dense Qwen3-Coder variant arrives, re-evaluate.

### What About DeepSeek-V4?

DeepSeek-V4 is rumored for mid-February 2026 but has NOT been released as of this writing. Even if released soon, it will likely be another massive MoE model unsuitable for QLoRA fine-tuning at the scale this project needs. Monitor but do not plan around it.

**Confidence:** MEDIUM -- DeepSeek-V4 timeline based on news reports, not official announcements.

---

## 2. Model Size and Variant Analysis

### The Core Question: 32B-Instruct vs 7B-Base vs 14B-Base

The bbjllm repo uses **Qwen2.5-Coder-32B-Instruct**. Chapter 3 docs recommend **Qwen2.5-Coder-7B-Base**. Neither is the optimal choice.

#### Instruct vs Base for Fine-Tuning

This is the most consequential decision and the current approach has a nuanced tradeoff:

| Factor | Base Model | Instruct Model |
|--------|-----------|----------------|
| **Continued pretraining (Stage 1)** | Correct choice. Base models accept raw text naturally. | Problematic. Continued pretraining on an Instruct model causes catastrophic forgetting of instruction capabilities. |
| **Instruction fine-tuning (Stage 2)** | Requires the model to learn instruction-following from scratch. Needs more data. | Already knows how to follow instructions. Needs less data to adapt to new domain. |
| **Small datasets (<1K examples)** | Struggles to learn both instruction format and domain knowledge. | Preferred. Leverages existing instruction capabilities. |
| **Medium datasets (1K-10K examples)** | Viable. Enough data to teach instruction-following alongside domain. | Also viable. Less risk of format issues. |
| **Large datasets (10K+ examples)** | Preferred. Full control over behavior. No inherited biases. | Works but may carry unwanted instruction biases that conflict with training data. |
| **Chat template compatibility** | Need to choose and train a template. | ChatML already built in (Qwen uses ChatML). |

**For the BBj project specifically (9,922 ChatML examples, niche language with near-zero representation):**

The bbjllm repo's choice of Instruct makes sense **if you skip Stage 1 (continued pretraining) and only do Stage 2 (instruction fine-tuning)**. The ChatML-formatted training data aligns directly with the Instruct model's expected format.

However, for a language with near-zero public training data, **the two-stage approach (continued pretraining + instruction fine-tuning) is strongly recommended** by current research. This means using the **Base** model, because continued pretraining on an Instruct model causes catastrophic forgetting of its instruction capabilities.

**Recommendation: Use Qwen2.5-Coder-14B-Base** with two-stage training:
- Stage 1: Continued pretraining on raw BBj source code (Base model learns BBj syntax)
- Stage 2: Instruction fine-tuning on the 9,922 ChatML examples (model learns to follow BBj instructions)

If hardware constraints force single-stage training (instruction fine-tuning only), then Instruct is acceptable as a shortcut. But document this as a known compromise.

#### Size Selection: 7B vs 14B vs 32B

| Factor | 7B | 14B | 32B |
|--------|-----|------|------|
| QLoRA VRAM (training) | ~12-16 GB | ~18-24 GB | ~24-40 GB |
| Single 24GB GPU (RTX 4090) | Comfortable | Tight but works | Requires multi-GPU or A100 |
| Inference (Q4_K_M GGUF) | ~4.5 GB | ~8.5 GB | ~19 GB |
| Customer self-hosting | Any modern machine | 16GB+ RAM workstation | Server-class, 32GB+ RAM |
| Code generation quality | Good for common patterns | Better for complex logic, fewer hallucinations | Best, but diminishing returns |
| Capacity to learn new language | Adequate for 10K examples | Better -- larger models benefit more from fine-tuning on refined data | Best capacity, but also needs more data |

Research from the Qwen2.5-Coder technical report confirms: "the improvement in performance for the 14B and 32B models is notably greater compared to the 7B variant, suggesting that larger models demonstrate a greater capacity to learn and benefit from refined data."

**Why 14B over 7B:** The 7B model is fine for standard fine-tuning tasks, but BBj is a zero-representation language. The model needs to learn an entirely new syntax, API surface, and idiom set from scratch. A 14B model has more capacity for this kind of deep domain adaptation while remaining trainable on a single 24GB GPU with QLoRA.

**Why 14B over 32B:** The 32B model requires multi-GPU training (the bbjllm repo runs on a multi-GPU server, so this is feasible). However, inference at 32B-Q4 requires ~19GB -- pushing customer self-hosting onto server-class hardware. The 14B-Q4 at ~8.5GB runs on a typical developer workstation with a mid-range GPU. For this project's target audience (BBj developers, not ML engineers), inference accessibility matters as much as peak quality.

**If the multi-GPU server is available and customer self-hosting is not a near-term concern**, 32B remains a valid choice. The 32B model will produce higher-quality output. But the documentation should acknowledge the inference cost.

**Recommendation: Qwen2.5-Coder-14B-Base as default, with 32B-Base as the "enterprise" variant for team-served deployments.**

**Confidence:** HIGH -- Size/VRAM requirements verified against multiple benchmarks and Qwen technical report.

---

## 3. Fine-Tuning Toolchain (February 2026)

### Current bbjllm Stack vs Latest Versions

The bbjllm repo uses dramatically outdated versions:

| Library | bbjllm Version | Latest Version (Feb 2026) | Gap | Breaking Changes |
|---------|---------------|--------------------------|-----|-----------------|
| `transformers` | 4.44.0 | **5.1.0** (Feb 5, 2026) | Major version jump (v4 to v5) | Yes -- v5 is first major release in 5 years. Significant API changes. |
| `peft` | 0.12.0 | **0.18.1** (Jan 9, 2026) | 6 minor versions behind | Yes -- PEFT 0.18.0+ required for Transformers v5 compatibility. Python 3.9 dropped. |
| `trl` | 0.9.6 | **0.27.2** (Feb 3, 2026) | 18 minor versions behind | Yes -- extensive API evolution. |
| `bitsandbytes` | 0.43.0 | **0.49.1** (Jan 8, 2026) | 6 minor versions behind | Likely some. |

**Assessment: The bbjllm stack is severely outdated.** Transformers v5 is a ground-up rearchitecture. Continuing with v4.44.0 means missing bug fixes, model support improvements, and performance optimizations accumulated over 18 months.

**However**, simply bumping versions will break the existing training scripts. The v4-to-v5 migration is non-trivial.

### Recommended Framework: Unsloth

Rather than updating the raw HuggingFace stack, the recommendation is to switch to **Unsloth** as the training framework. Here is why:

| Factor | HuggingFace PEFT (raw) | Unsloth |
|--------|----------------------|---------|
| Training speed | Baseline | **2-3x faster** (custom Triton kernels for RoPE + MLP) |
| VRAM usage | Baseline | **~70% less** via aggressive memory optimization |
| Accuracy | Baseline | **Identical** (same mathematical operations) |
| Qwen2.5-Coder support | Yes | Yes (explicitly supported, pre-quantized models on HF) |
| Multi-GPU | DeepSpeed/FSDP | Preliminary DDP support (full release expected early 2026) |
| GGUF export | Requires separate llama.cpp step | **Built-in** direct GGUF export |
| Ecosystem compatibility | Native HF | **Fully compatible** with HF Hub, PEFT, TRL |
| Dynamic 4-bit quantization | Standard BnB 4-bit | **Dynamic quantization** -- selectively skips quantization for critical params, +accuracy for <10% more VRAM |
| Long context training | Standard | **500K+ context** on single 80GB GPU |
| Learning curve | Must wire together transformers+peft+trl+bitsandbytes | Single API, batteries included |

**Unsloth version:** `2026.1.4` (latest on PyPI as of Feb 2026)

**Critical advantage for this project:** Unsloth's Dynamic 4-bit Quantization is particularly valuable for niche-language fine-tuning. Standard BnB 4-bit quantization treats all parameters equally, but some model layers are more important for learning new patterns. Unsloth dynamically opts not to quantize certain critical parameters, achieving better accuracy with minimal VRAM overhead. For a task like teaching BBj syntax from scratch, this matters.

**Multi-GPU concern:** The bbjllm repo uses a multi-GPU server. Unsloth's multi-GPU support (DDP) is in preliminary state with full release expected early 2026. If multi-GPU is strictly required right now, two options:
1. Use Unsloth on a single GPU (fastest training per-GPU, may be sufficient for 14B QLoRA)
2. Use LLaMA-Factory or Axolotl for multi-GPU, with some speed tradeoff

For a 14B model with QLoRA, a single 24GB GPU is sufficient. Multi-GPU is only needed for 32B or full fine-tuning.

**Confidence:** HIGH -- Unsloth capabilities verified via official docs and GitHub. Version verified on PyPI. Qwen2.5-Coder support confirmed with pre-quantized models on HuggingFace.

### Alternative Frameworks Comparison

| Framework | Best For | Multi-GPU | GUI | LoRA/QLoRA | Key Feature |
|-----------|---------|-----------|-----|------------|-------------|
| **Unsloth** | Speed + memory efficiency on 1-2 GPUs | Preliminary DDP | No (code-first) | Excellent | 2-3x speed, dynamic quantization, built-in GGUF export |
| **LLaMA-Factory** | Accessible fine-tuning with web UI | Yes (DeepSpeed, FSDP) | Yes (LlamaBoard) | Good | No-code option, 100+ model support, SFT/DPO/PPO |
| **Axolotl** | Advanced training recipes, production pipelines | Yes (DeepSpeed, FSDP, Sequence Parallelism) | No (YAML config) | Good | QAT support, multimodal, GRPO/reward modeling |
| **torchtune** | PyTorch-native, minimal abstraction | Yes (multi-node) | No (YAML config) | Good | <600 LOC recipes, PyTorch ecosystem alignment |
| **Raw HF (transformers+peft+trl)** | Maximum control, debugging | Yes (via accelerate/DeepSpeed) | No | Full | Most flexibility, most boilerplate |

**Recommendation:** Unsloth for the primary training pipeline. If multi-GPU is essential for 32B training, use LLaMA-Factory as the fallback (it has a web UI that lowers the barrier for non-ML engineers and supports Qwen models natively).

### If Staying with HuggingFace PEFT

If the team prefers to stay with the raw HF stack rather than adopting Unsloth, here are the minimum version updates:

```bash
pip install \
  transformers>=5.1.0 \
  peft>=0.18.1 \
  trl>=0.27.0 \
  bitsandbytes>=0.49.1 \
  accelerate>=1.4.0

# Python 3.10+ required (PEFT 0.18+ dropped Python 3.9)
```

**Warning:** The transformers v4-to-v5 migration is significant. Expect breaking changes in model loading, tokenizer handling, and training loop APIs. Budget time for migration testing.

**Confidence:** HIGH -- All version numbers verified on PyPI with release dates.

---

## 4. Training Approach

### QLoRA: Still the Right Choice

QLoRA remains the recommended approach for this project in 2026. The fundamentals have not changed:

- **Full fine-tuning** of a 14B model requires ~60-80GB VRAM (multiple A100s). Overkill for a 10K-example dataset.
- **LoRA** (without quantization) requires ~24-32GB for 14B. Possible but wastes memory on frozen weight storage.
- **QLoRA** reduces frozen weights to 4-bit, cutting VRAM to ~18-24GB for 14B. Fits on a single RTX 4090/A6000.

Recent 2026 literature confirms: "QLoRA achieves 95-98% of full fine-tuning performance while using only 0.1-1% of trainable parameters." The <2% quality gap vs full fine-tuning is not worth the 4-8x hardware cost for this project.

### Recommended Hyperparameters

The bbjllm repo uses rank=32, alpha=64, which follows the standard 2x alpha/rank ratio. This is reasonable. Here are updated recommendations based on 2026 best practices:

| Parameter | bbjllm Current | Recommended | Rationale |
|-----------|---------------|-------------|-----------|
| LoRA rank (r) | 32 | **32-64** | Higher rank for learning new language. 32 is minimum for niche domain; 64 if VRAM allows. |
| LoRA alpha | 64 | **2x rank** (64-128) | Standard scaling. Keep alpha = 2 * rank. |
| LoRA target modules | (unknown) | **All linear layers** | Apply to attention AND MLP layers. Recent research confirms MLP inclusion significantly improves code task performance. |
| Quantization | NF4 4-bit | **NF4 4-bit** (or Unsloth Dynamic 4-bit) | NF4 remains the standard. Unsloth's dynamic variant is better if using Unsloth. |
| Double quantization | (unknown) | **Yes** | Reduces memory further with negligible quality impact. |
| Learning rate | (unknown) | **2e-4 (Stage 1), 5e-5 (Stage 2)** | Higher for pretraining, lower for instruction tuning to avoid catastrophic forgetting. |
| Epochs | (unknown) | **1-3** | More risks overfitting on 10K examples. Start with 1 epoch, evaluate, add more only if underfitting. |
| Batch size | (unknown) | **4-8 (with gradient accumulation to effective 32-64)** | Standard for QLoRA training. |
| Max sequence length | (unknown) | **2048-4096** | BBj functions are compact. 4096 accommodates longer class definitions. |
| Warmup ratio | (unknown) | **0.03-0.1** | Standard warmup for LoRA fine-tuning. |
| Weight decay | (unknown) | **0.01** | Light regularization. |
| Optimizer | (unknown) | **adamw_8bit** (paged) | 8-bit AdamW saves VRAM. Unsloth uses this by default. |

#### Advanced: rsLoRA (Rank-Stabilized LoRA)

For higher rank values (64+), consider using **rsLoRA** which scales alpha by sqrt(rank) instead of linearly. This prevents training instability at high ranks. PEFT 0.18+ and Unsloth both support rsLoRA.

#### Target Module Selection

This is critical and often misconfigured. **Apply LoRA to ALL linear layers, not just attention:**

```python
# Unsloth approach (recommended)
model = FastLanguageModel.get_peft_model(
    model,
    r=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                     "gate_proj", "up_proj", "down_proj"],
    lora_alpha=64,
    lora_dropout=0,  # Unsloth recommends 0 dropout
    bias="none",
    use_gradient_checkpointing="unsloth",  # Unsloth-specific optimization
)
```

Including MLP layers (gate_proj, up_proj, down_proj) is especially important for learning new syntax patterns, as code structure knowledge is heavily encoded in MLP layers.

**Confidence:** HIGH -- Hyperparameter recommendations verified against Unsloth docs, Databricks LoRA guide, and multiple 2025-2026 fine-tuning guides.

### Two-Stage Training Pipeline

For BBj (near-zero public representation), the two-stage approach is strongly recommended:

```
Stage 1: Continued Pretraining (CPT)
  Input:  Raw BBj source code (no instruction formatting)
  Model:  Qwen2.5-Coder-14B-Base
  Goal:   Teach the model BBj syntax, tokens, patterns
  LR:     2e-4 (higher learning rate for new knowledge)
  Format: Plain text, next-token prediction
  Data:   All available BBj source files, documentation text

Stage 2: Instruction Fine-Tuning (IFT)
  Input:  9,922 ChatML examples
  Model:  Stage 1 output (adapter merged or chained)
  Goal:   Teach the model to follow BBj-specific instructions
  LR:     5e-5 (lower to preserve Stage 1 knowledge)
  Format: ChatML conversation format
  Data:   Existing JSONL training data
```

**Why not skip Stage 1?** The Qwen2.5-Coder training data covers 92 programming languages, but BBj is almost certainly not among them. Without Stage 1, the model must simultaneously learn BBj syntax AND instruction-following behavior from just 10K examples. Stage 1 lets it first absorb the syntax passively (cheaper, from raw code), then Stage 2 teaches it to apply that knowledge in instruction contexts.

**Stage 1 data sources:** Raw BBj source code from the same corpus that generated the training examples -- sample programs, library code, customer code snippets (sanitized). This does not need ChatML formatting. Plain .bbj files fed as continuation sequences.

**Important:** Stage 1 MUST use the Base model, not Instruct. Research confirms that continued pretraining on an Instruct model causes catastrophic forgetting of instruction capabilities. The Base model does not have this problem because it has no instruction capabilities to forget.

**Confidence:** HIGH -- Two-stage approach validated by multiple 2025-2026 papers and the Qwen technical report.

### What About the Instruct Shortcut?

The bbjllm repo uses 32B-Instruct with single-stage instruction fine-tuning. This is a valid shortcut with known tradeoffs:

**Pros:**
- Simpler pipeline (one stage instead of two)
- ChatML data works immediately (Instruct model already knows the format)
- Preserves general instruction-following from Qwen's RLHF training

**Cons:**
- Cannot do continued pretraining (would destroy instruction capabilities)
- Model must learn BBj syntax entirely from instruction examples (less efficient)
- Inherited biases from Qwen's instruction training may conflict with BBj patterns
- Harder to debug whether errors are from insufficient BBj knowledge vs instruction confusion

**If sticking with the Instruct shortcut:** At minimum, ensure the training data has high syntactic diversity. The model needs to see enough BBj patterns purely through instruction examples to compensate for the missing pretraining stage.

---

## 5. Evaluation Practices

### Frameworks for Code Generation Evaluation

| Framework | Type | Purpose | BBj Applicability |
|-----------|------|---------|-------------------|
| **BigCode Evaluation Harness** | Automated | HumanEval, MBPP, APPS (Python tasks) | Low -- measures general coding, not BBj. Use as catastrophic-forgetting detector. |
| **BigCodeBench** | Automated | Realistic tasks with library usage | Low -- Python-centric. |
| **bbjcpl validation** | Custom | Compile BBj output, check for syntax errors | **High** -- directly measures syntactic validity. The project's #1 metric. |
| **Manual expert review** | Human | BBj developers grade outputs for correctness, idiom adherence, generation awareness | **High** -- no substitute for domain expert evaluation. |

### Recommended BBj-Specific Evaluation Pipeline

Since no off-the-shelf benchmark exists for BBj, build a custom evaluation suite:

#### Tier 1: Syntactic Validity (Automated)

Use `bbjcpl -N` to compile generated code. This is the project's target metric: **95%+ syntactically valid code.**

```
Evaluation set: 200-500 held-out BBj generation prompts
Process: Generate code -> write to .bbj file -> run bbjcpl -N -> parse stderr
Metric: % of generations that compile without errors
Target: >= 95%
```

The existing bbjcpltool infrastructure already supports this workflow. Automate it as a post-training evaluation script.

#### Tier 2: Semantic Correctness (Semi-Automated)

For a subset of evaluations, check that generated code does what was asked:

- Does a "create a BBj grid" prompt produce code with `BBjGrid` objects?
- Does a "file I/O" prompt use correct channel syntax?
- Does generation-labeled code use the right API generation?

This can be partially automated with pattern matching (does output contain expected API calls?) and partially requires human review.

#### Tier 3: General Capability Retention (Automated)

Run HumanEval (Python) on the fine-tuned model and compare to the base Qwen2.5-Coder-14B scores. If HumanEval drops more than 5%, the model is catastrophically forgetting general code knowledge. Adjust the training mix.

#### Tier 4: Real-World Usage (Human)

Have BBj developers use the model for actual tasks (via Ollama + IDE integration) and collect feedback. This is the ultimate measure but hardest to systematize. Start collecting this data as soon as a viable model exists.

### Evaluation Set Construction

Reserve 5-10% of training data as a held-out evaluation set. Do NOT train on these examples. Additionally, create a separate "challenge set" with:

- Edge cases (error handling, unusual syntax patterns)
- Generation-specific questions (asking for DWC code when context suggests character UI)
- Multi-generational code (mixing old and new patterns)
- Common BBj pitfalls (channel management, object lifecycle)

**Confidence:** HIGH for the approach, MEDIUM for specific metrics (the 95% target is aspirational and based on the project's stated goals, not empirical baseline).

---

## 6. Serving Stack

### Ollama: Still the Right Choice for Self-Hosting

Ollama is now at **v0.15.x** (not v0.9.x as stated in Chapter 3 docs -- this needs correction). Recent additions:

| Feature | Status | Notes |
|---------|--------|-------|
| LoRA adapter serving | Supported via ADAPTER directive in Modelfile | Requires GGUF-format adapter |
| Multiple LoRA adapters | Supported (PR #7667) | Can load multiple adapters simultaneously |
| OpenAI-compatible API | Full support | `/v1/chat/completions`, `/v1/completions` |
| Anthropic-format API | Supported | Tool calling, structured JSON output |
| GGUF quantization formats | All standard formats | Q4_0, Q4_K_M, Q8_0, F16, etc. |
| `ollama launch` command | New in v0.15 | Direct integration with Claude Code, Codex, etc. |

**For customer self-hosting (single developer or small team):** Ollama remains unbeatable. One binary install, `ollama run bbj-coder`, done. The model file is portable and works offline.

### vLLM: Better for Team/Centralized Serving

For the project's own inference server (serving the RAG-powered chat), **vLLM** is the better choice:

| Factor | Ollama | vLLM |
|--------|--------|------|
| Setup complexity | Minimal | Moderate (Python, CUDA dependencies) |
| Throughput | Good for single user | Excellent for concurrent users |
| Dynamic LoRA hot-swap | Via Modelfile rebuild | **Runtime API (`/v1/load_lora_adapter`)** |
| Multi-adapter serving | Supported but basic | **Per-request adapter selection** |
| Continuous batching | Basic | **Advanced PagedAttention** |
| Production scaling | Not designed for it | Built for production serving |
| Customer self-hosting | Perfect | Too complex for most BBj developers |

**Recommendation:**
- **Customer-facing deployment:** Ollama (simplicity wins)
- **Team inference server / RAG backend:** vLLM (performance wins)
- **Development / evaluation:** Ollama (quick iteration)

### Serving the 14B Model

| Quantization | Size | Ollama RAM | vLLM VRAM | Quality | Recommendation |
|---|---|---|---|---|---|
| Q4_K_M | ~8.5 GB | 10-12 GB RAM | 10 GB VRAM | Good | **Default for deployment** |
| Q8_0 | ~15 GB | 18-20 GB RAM | 16 GB VRAM | Very good | High-end workstations |
| F16 | ~28 GB | 32+ GB RAM | 28 GB VRAM | Full | Evaluation only |

Q4_K_M at ~8.5GB comfortably runs on a workstation with 16GB RAM or a GPU with 10GB VRAM. This is accessible for BBj developers without requiring server-class hardware.

**Confidence:** HIGH -- Ollama version verified on GitHub releases. vLLM LoRA capabilities verified in official docs.

---

## 7. Gap Analysis: bbjllm vs Recommended Approach

### What bbjllm Gets Right

| Aspect | bbjllm Choice | Assessment |
|--------|--------------|------------|
| QLoRA method | 4-bit NF4, rank 32, alpha 64 | Sound. Standard configuration. |
| ChatML format | 9,922 ChatML examples in JSONL | Good format, aligns with Qwen's chat template. |
| Qwen2.5-Coder family | Correct model family | Best available for code fine-tuning in 2026. |

### What Should Change

| Aspect | bbjllm Current | Recommended | Priority |
|--------|---------------|-------------|----------|
| **Library versions** | transformers 4.44, peft 0.12, trl 0.9.6, bnb 0.43 | Switch to Unsloth 2026.1.4 (or update to transformers 5.1, peft 0.18.1, trl 0.27.2, bnb 0.49.1) | **Critical** -- current versions are ~18 months stale |
| **Model variant** | 32B-Instruct | 14B-Base (or 32B-Base if multi-GPU justified) | **High** -- enables two-stage training |
| **Training stages** | Single-stage instruction fine-tuning | Two-stage: continued pretraining + instruction fine-tuning | **High** -- significant quality improvement for zero-representation language |
| **Framework** | Raw HF PEFT | Unsloth | **Medium** -- 2-3x speed improvement, simpler code |
| **Evaluation** | (none documented) | bbjcpl-based syntactic validation + HumanEval retention check | **High** -- cannot measure progress without evaluation |
| **GGUF export** | (unknown) | Built-in via Unsloth or llama.cpp convert | **Medium** -- needed for Ollama serving |

### What Chapter 3 Gets Right

| Aspect | Chapter 3 Claim | Assessment |
|--------|----------------|------------|
| Qwen2.5-Coder family | Correct | Still the best family for this task |
| QLoRA method | Correct | Still the recommended approach |
| Unsloth framework | Correct | Still recommended over raw HF PEFT |
| Two-stage training | Correct | Strongly recommended for BBj |
| Ollama serving | Correct | Still the right self-hosting solution |
| GGUF via llama.cpp | Correct | Still needed (Unsloth can also export directly) |

### What Chapter 3 Should Update

| Aspect | Chapter 3 Current | Should Be | Why |
|--------|-------------------|-----------|-----|
| **Model size** | 7B-Base | **14B-Base** (primary), 7B-Base (minimum) | 14B shows significantly better improvement from fine-tuning per Qwen technical report |
| **Ollama version** | "v0.9.x+" | **v0.15.x** | Ollama is at 0.15.x, not 0.9.x |
| **Model comparison table** | Lists CodeLlama, StarCoder2 as alternatives | Add **Qwen3** (general) dense models, note **Qwen3-Coder** is MoE-only | Landscape has evolved |
| **Qwen3-Coder note** | Notes MoE-only, recommends waiting | Correct but update with Qwen3-Coder-Next (Feb 2026) information | New model released |
| **Training data status** | "approximately 10,000" | **9,922 ChatML examples** (precise count from bbjllm) | Match actual implementation |
| **Unsloth features** | Basic description | Add Dynamic 4-bit Quantization, 500K context, GRPO support | Significant new capabilities |
| **Hardware table** | RTX 4090 for 7B | Update for 14B requirements (RTX 4090 still works with QLoRA) | Reflects new model size recommendation |

---

## 8. Complete Recommended Stack

### Training Environment

```bash
# Core training framework
pip install unsloth

# Unsloth pulls in compatible versions of:
#   transformers >= 5.0
#   peft >= 0.18
#   trl >= 0.27
#   bitsandbytes >= 0.49
#   torch >= 2.5

# Additional useful libraries
pip install datasets        # HuggingFace datasets for data loading
pip install wandb           # Experiment tracking (optional but recommended)
pip install evaluate        # HuggingFace evaluation library
```

### Model Downloads

```bash
# Primary model (14B-Base)
# Downloaded automatically by Unsloth, or pre-download:
huggingface-cli download Qwen/Qwen2.5-Coder-14B

# Pre-quantized for QLoRA (saves download time):
huggingface-cli download unsloth/Qwen2.5-Coder-14B-bnb-4bit

# If using 32B for enterprise variant:
huggingface-cli download unsloth/Qwen2.5-Coder-32B-bnb-4bit
```

### GGUF Conversion and Serving

```bash
# Option A: Unsloth built-in export (recommended)
# In training script:
#   model.save_pretrained_gguf("bbj-coder-14b", tokenizer, quantization_method="q4_k_m")

# Option B: Manual conversion via llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make
python convert_hf_to_gguf.py /path/to/merged/model --outtype q4_k_m

# Ollama deployment
ollama create bbj-coder -f Modelfile
ollama run bbj-coder
```

### Version Matrix (All Verified 2026-02-06)

| Component | Version | Source | Role |
|-----------|---------|--------|------|
| Unsloth | 2026.1.4 | PyPI | Training framework (wraps transformers, peft, trl) |
| transformers | 5.1.0 | PyPI (Feb 5, 2026) | Model architecture (pulled by Unsloth) |
| peft | 0.18.1 | PyPI (Jan 9, 2026) | LoRA/QLoRA adapters (pulled by Unsloth) |
| trl | 0.27.2 | PyPI (Feb 3, 2026) | SFT trainer (pulled by Unsloth) |
| bitsandbytes | 0.49.1 | PyPI (Jan 8, 2026) | 4-bit quantization (pulled by Unsloth) |
| Ollama | 0.15.5 | GitHub (Feb 2026) | Inference serving |
| llama.cpp | Latest | GitHub | GGUF conversion (if not using Unsloth export) |
| Python | >= 3.10 | Required by peft 0.18+ | Runtime |
| CUDA | >= 12.1 | NVIDIA | GPU compute (bbjllm server already has 12.1) |

---

## 9. Training Data Format Alignment

### bbjllm Format: ChatML JSONL

The bbjllm repo has 9,922 examples in ChatML JSONL format. This is compatible with both Unsloth and raw HF TRL for instruction fine-tuning (Stage 2).

Example format (inferred from project context):
```json
{"messages": [
  {"role": "system", "content": "You are a BBj programming assistant."},
  {"role": "user", "content": "Write a BBj function that opens a file and reads records"},
  {"role": "assistant", "content": "rem Open file and read records\nOPEN (1)\"data.dat\"\n..."}
]}
```

### Stage 1 Data (Continued Pretraining)

For Stage 1, raw BBj source code does NOT need ChatML formatting. Feed it as plain text:

```json
{"text": "class public OrderForm\n  field private BBjTopLevelWindow window!\n  ..."}
```

**Data source for Stage 1:** Extract raw BBj code from the same corpus used to create the training examples. Strip instruction formatting, keep only the code. Also include raw BBj source files from documentation samples, tutorial code, etc.

### Unsloth Data Loading

Unsloth integrates with HuggingFace datasets. The existing JSONL files work directly:

```python
from datasets import load_dataset

# Stage 2: Instruction fine-tuning
dataset = load_dataset("json", data_files="training_data.jsonl", split="train")

# Unsloth SFT
from unsloth import FastLanguageModel
from trl import SFTTrainer

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",  # or use chat template formatting
    max_seq_length=4096,
    # ... other args
)
```

**Confidence:** HIGH -- Unsloth + TRL SFTTrainer + HF datasets is the standard pipeline, well-documented.

---

## 10. Implications for Documentation Updates

### Chapter 3 Sections Requiring Updates

| Section | Current Content | Required Update |
|---------|----------------|-----------------|
| TL;DR tip box | "Qwen2.5-Coder-7B" + "Unsloth" | Change to "Qwen2.5-Coder-14B" (keep Unsloth) |
| Base Model Selection decision box | "Qwen2.5-Coder-7B-Base" | Change to "Qwen2.5-Coder-14B-Base" with 7B as minimum tier |
| Model Comparison table | Lists CodeLlama, StarCoder2, DeepSeek-V3 | Add Qwen3 dense, Qwen3-Coder (MoE note), DeepSeek-V4 (unreleased) |
| "A Note on Newer Models" section | Only mentions Qwen3-Coder (July 2025 MoE) | Add Qwen3-Coder-Next (Feb 2026), note still MoE-only |
| Size Rationale section | Recommends 7B | Update to recommend 14B primary, with 7B as minimum and 32B as enterprise |
| Hardware Requirements table | Based on 7B sizes | Update for 14B (Q4_K_M ~8.5GB, needs 16GB+ RAM) |
| Hosting via Ollama decision box | "Ollama (v0.9.x+)" | Change to "Ollama (v0.15.x+)" |
| Ollama features description | Mentions Anthropic format as new | Update to reflect v0.15.x capabilities including `ollama launch` |
| Current Status note box | "Qwen2.5-Coder-7B-Base selected" | Update to reflect actual bbjllm state and recommended changes |

### New Sections to Add

1. **Relationship to bbjllm repo:** Acknowledge the actual implementation exists, explain how it differs from docs, and state the recommended path forward.

2. **Stage 1 data preparation:** The current docs describe Stage 1 conceptually but do not explain how to prepare raw BBj code for continued pretraining. Add practical guidance.

3. **Evaluation methodology:** Chapter 3 mentions evaluation conceptually but has no concrete evaluation pipeline. Add the bbjcpl-based approach described above.

---

## Sources

### Models
- [Qwen3-Coder GitHub](https://github.com/QwenLM/Qwen3-Coder) -- Model family overview, sizes, architecture
- [Qwen3-Coder-Next Announcement](https://www.marktechpost.com/2026/02/03/qwen-team-releases-qwen3-coder-next-an-open-weight-language-model-designed-specifically-for-coding-agents-and-local-development/) -- Feb 2026 release details
- [Qwen3-Coder HuggingFace Collection](https://huggingface.co/collections/Qwen/qwen3-coder) -- Available model variants
- [Qwen3 GitHub](https://github.com/QwenLM/Qwen3) -- Dense model sizes (0.6B-32B)
- [Qwen2.5-Coder Technical Report](https://arxiv.org/pdf/2409.12186) -- Architecture, training, benchmarks
- [Qwen2.5-Coder HuggingFace](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct) -- Model card
- [DeepSeek-V4 Reports](https://introl.com/blog/deepseek-v4-february-2026-coding-model-release) -- Expected release, not yet available

### Fine-Tuning Frameworks
- [Unsloth GitHub](https://github.com/unslothai/unsloth) -- Version 2026.1.4, feature list
- [Unsloth Qwen2.5-Coder Support](https://unsloth.ai/blog/qwen-coder) -- Official blog post
- [Unsloth LoRA Hyperparameters Guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide) -- Recommended settings
- [Unsloth Dynamic 4-bit Quantization](https://unslothai.substack.com/p/unsloth-december-update) -- December 2025 update
- [LLaMA-Factory GitHub](https://github.com/hiyouga/LlamaFactory) -- Multi-GPU alternative
- [Axolotl GitHub](https://github.com/axolotl-ai-cloud/axolotl) -- Advanced training recipes
- [torchtune GitHub](https://github.com/meta-pytorch/torchtune) -- PyTorch native option

### Library Versions (All Verified on PyPI 2026-02-06)
- [transformers 5.1.0](https://pypi.org/project/transformers/) -- Released Feb 5, 2026
- [peft 0.18.1](https://pypi.org/project/peft/) -- Released Jan 9, 2026
- [trl 0.27.2](https://pypi.org/project/trl/) -- Released Feb 3, 2026
- [bitsandbytes 0.49.1](https://pypi.org/project/bitsandbytes/) -- Released Jan 8, 2026
- [Unsloth 2026.1.4](https://pypi.org/project/unsloth/) -- Latest on PyPI

### Training Methodology
- [LoRA vs QLoRA Best Practices 2026](https://www.index.dev/blog/top-ai-fine-tuning-tools-lora-vs-qlora-vs-full) -- Comparison and recommendations
- [Databricks LoRA Guide](https://www.databricks.com/blog/efficient-fine-tuning-lora-guide-llms) -- Hyperparameter recommendations
- [rsLoRA Paper](https://huggingface.co/blog/damjan-k/rslora) -- Rank-stabilized scaling
- [Continued Pretraining vs Instruction Fine-Tuning](https://arxiv.org/abs/2410.10739) -- Two-stage approach research
- [Instruct vs Base Model Selection](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/what-model-should-i-use) -- Unsloth official guidance
- [Data-efficient LLM Fine-tuning for Code Generation](https://arxiv.org/html/2504.12687v1) -- Data quality research

### Evaluation
- [BigCode Evaluation Harness](https://github.com/bigcode-project/bigcode-evaluation-harness) -- Code generation evaluation framework
- [BigCodeBench](https://github.com/bigcode-project/bigcodebench) -- Practical task evaluation

### Serving
- [Ollama Releases](https://github.com/ollama/ollama/releases) -- v0.15.x (Feb 2026)
- [Ollama Modelfile Reference](https://docs.ollama.com/modelfile) -- ADAPTER and configuration
- [vLLM LoRA Adapters](https://docs.vllm.ai/en/latest/features/lora/) -- Dynamic LoRA serving
- [vLLM vs Ollama Comparison](https://blog.worldline.tech/2026/01/29/llm-inference-battle.html) -- Jan 2026 benchmark

---

*Research conducted 2026-02-06. All version numbers verified against PyPI, GitHub releases, and official documentation as of research date. Model landscape reflects publicly available models only; unreleased models (DeepSeek-V4) are flagged as MEDIUM confidence.*
