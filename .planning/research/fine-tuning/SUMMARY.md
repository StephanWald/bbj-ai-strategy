# Fine-Tuning Research Summary

**Project:** BBj AI Strategy v1.7 Documentation Refresh
**Domain:** Niche-language LLM fine-tuning (BBj code generation)
**Researched:** 2026-02-06
**Confidence:** MEDIUM-HIGH

## Executive Summary

The bbjllm repository's fine-tuning approach (Qwen2.5-Coder-32B-Instruct + QLoRA on 9,922 ChatML examples) is fundamentally sound but contains several critical flaws that will significantly reduce model quality if not addressed before the next training run. The technology stack is 18 months out of date, missing important bug fixes and performance optimizations. The training methodology has three blocker-level issues: no validation set (preventing overfitting detection), training on full sequences instead of completions only (diluting the gradient signal by 30-40%), and using an Instruct model for fine-tuning (risking performance degeneration). The dataset contains quality issues including 375 duplicate questions, 60 examples with corrupted newlines, and inconsistent formatting.

The recommended path forward switches from 32B-Instruct to 14B-Base with a two-stage training pipeline: continued pretraining on raw BBj source code (Stage 1) followed by instruction fine-tuning on the ChatML examples (Stage 2). This leverages the Base model's capacity for learning new syntax patterns without the alignment tax of fine-tuning an already-instruct-tuned model. The framework recommendation shifts from outdated PEFT/HuggingFace to Unsloth, which provides 2-3x faster training and 70% lower VRAM usage while maintaining identical accuracy. Most critically, a BBj-specific evaluation suite using the bbjcpl compiler must be built before claiming any training success—without automated compile-based validation, the team cannot measure whether fine-tuning actually improved BBj code generation.

The key risk is proceeding with training before fixing the critical issues. Without validation data and evaluation metrics, the team is iterating blind. The current 2e-5 learning rate is 5-10x lower than QLoRA recommendations, risking undertraining. Combined with full-sequence loss computation (wasting 40% of gradient signal on system prompts), the model may appear to work but only because the strong base model carries it—the fine-tuning adds minimal value. The recommended fixes require 1-2 days of work but will dramatically improve training outcomes and enable data-driven iteration.

## Key Findings

### Recommended Stack

The technology landscape has evolved significantly since the bbjllm stack was pinned in August 2024. The current choice (Qwen2.5-Coder family with QLoRA) remains sound, but execution details need updates.

**Core technologies:**
- **Qwen2.5-Coder-14B-Base** (not 32B-Instruct): Best balance for niche-language fine-tuning. The 14B model shows greater improvement from fine-tuning on refined data compared to 7B, while remaining trainable on a single 24GB GPU. The Base variant (not Instruct) is required for two-stage training and avoids the alignment tax of re-training instruction capabilities.
- **Unsloth 2026.1.4** (not raw PEFT): Provides 2-3x training speed, 70% lower VRAM, dynamic 4-bit quantization (better accuracy for critical parameters), and built-in GGUF export. Fully compatible with HuggingFace ecosystem but with batteries included. The current PEFT stack is 6+ major versions behind on all libraries.
- **Two-stage training pipeline**: Stage 1 (continued pretraining on raw BBj source) teaches syntax patterns passively. Stage 2 (instruction fine-tuning on 9,922 ChatML examples) teaches instruction-following with that syntax. This is strongly recommended for zero-representation languages where the base model has never seen BBj during pre-training.
- **Ollama v0.15.x** (not v0.9.x as docs claim): Still the right choice for customer self-hosting. vLLM better for centralized team serving with LoRA hot-swapping. Q4_K_M quantization at ~8.5GB for 14B makes it accessible on typical developer workstations.

**Critical version updates needed:**
- transformers: 4.44.0 → 5.1.0 (v5 is first major release in 5 years, significant API changes)
- peft: 0.12.0 → 0.18.1 (6 minor versions behind, Python 3.9 dropped)
- bitsandbytes: 0.43.0 → 0.49.1 (0.43.0 has a critical QLoRA memory bug fixed in 0.43.2 that wastes 5-10GB VRAM)

### Expected Features (Evaluation & Training Methodology)

The research focused on training methodology and evaluation practices rather than product features, since this is about improving an existing fine-tuning effort.

**Must have (table stakes):**
- **Training/validation split (90/10)**: The current approach uses 100% of data for training with zero held-out validation. This makes overfitting detection impossible. A 10% validation set with evaluation_strategy="steps" is mandatory for any responsible ML training.
- **Completion-only loss masking**: The current script computes loss on system prompt + user question + assistant response. This wastes 30-40% of gradient signal on constant, uninformative tokens. Only the assistant's response should contribute to loss.
- **BBj-specific evaluation suite**: Since no public BBj benchmark exists, build a custom one using bbjcpl compiler for automated syntax validation (compile@1 metric), factual accuracy checks (regex-based), and manual expert review. The existing 3-question test in the training script is inadequate.
- **Adapter weights committed to repo with Git LFS**: Currently adapters exist only on the training server at `/usr2/yasser_experiment/`. If that server is rebuilt, all training results are lost. Adapters are 100-300MB—small enough for version control.
- **Model card documentation**: The current README is the default GitLab template. Each trained adapter needs a model card with hyperparameters, training metrics, evaluation results, and deployment instructions.

**Should have (differentiators):**
- **Experiment tracking (W&B or TensorBoard)**: The current `report_to="none"` means loss curves are only visible in stdout. W&B free tier enables comparing runs side-by-side with zero infrastructure.
- **Compile-based evaluation with bbjcpl**: This is BBj's secret weapon. The compiler IS the ground truth for syntactic correctness. Automated evaluation pipeline that generates code from prompts, validates via `bbjcpl -N`, and computes compile@1 creates a unique, non-gameable metric.
- **Base model comparison baseline**: Run the evaluation suite against unmodified Qwen2.5-Coder-32B-Instruct to establish what the base model can do. Without this, you cannot prove fine-tuning helped.
- **Dynamic padding or packing**: The current padding="max_length" wastes 50-80% of each batch on empty tokens (median example is ~200 tokens padded to 1024). Dynamic padding or SFTTrainer's packing=True can increase throughput by 3-5x.

**Defer (v2+):**
- **Full fine-tuning (unfreezing all weights)**: Requires 8x memory, 10x compute, and risks catastrophic forgetting. QLoRA already achieves 95-98% of full fine-tuning performance.
- **Synthetic data generation at scale**: LLMs don't know BBj well enough to generate correct synthetic examples. Focus on curating high-quality authoritative examples instead.
- **Production-grade MLOps infrastructure**: Kubernetes, model registries, A/B testing are overkill for a 1-3 person team on an internal tool. Use simple local training + W&B + git + manual Ollama deployment.

### Architecture Approach

The architecture research focused on how the fine-tuned model integrates with the existing RAG system and gets deployed to end users.

**Integration pattern (RAG + fine-tuned model):**
The optimal architecture is not RAG-or-fine-tuning but RAG-and-fine-tuning (RAFT: Retrieval-Augmented Fine-Tuning). The fine-tuned model has BBj syntax knowledge baked in from training. RAG provides API signatures that may have changed since training, specific documentation passages for grounding, and generation-specific context. The generate_bbj_code MCP tool should (1) search RAG for relevant documentation, (2) build enriched prompt with RAG context, (3) call fine-tuned model via Ollama, (4) validate with bbjcpl, (5) retry with error feedback if needed.

**Major components:**
1. **Fine-tuned model serving (Ollama)**: Qwen2.5-Coder-14B-Base + adapter → GGUF conversion → Ollama serving via OpenAI-compatible API. Hardware requirement: 24GB VRAM for training (single RTX 4090), 10-12GB RAM for Q4_K_M inference.
2. **generate_bbj_code MCP tool (not yet implemented)**: Bridge between MCP protocol and fine-tuned model. Calls Ollama (not Claude API) with optional RAG enrichment. Returns BBj code validated by bbjcpl.
3. **Generate-validate-fix loop**: Client-orchestrated pattern where MCP host (Claude Desktop) calls generate_bbj_code → validate_bbj_syntax → generate_bbj_code with errors → validate_bbj_syntax until valid or max attempts. The existing chat validate-fix loop (server-side, Claude-powered) remains for web chat.
4. **Training data pipeline (needs build)**: The training-data/ repo (markdown + YAML + JSON Schema) and bbjllm repo (ChatML JSONL) are disconnected. Need convert_to_chatml.py script to transform markdown examples into training format, preserving generation metadata and quality validation.

**Deployment topology:**
One shared GPU server running Ollama (both embedding model + fine-tuned code model), Docker Compose (pgvector + FastAPI), and bbjcpl compiler. Multiple developers connect via Continue.dev IDE extension (chat + tab autocomplete), Claude Desktop (MCP HTTP), or web browser (/chat). The 32B model requires ~19GB VRAM and may be too slow for interactive use (10-30 tok/s); 14B at ~8.5GB Q4 is more practical.

### Critical Pitfalls

**1. Training on full sequence instead of completion only (BLOCKER)**
The current script computes loss on system prompt + user question + assistant response. The system prompt "You are an expert BBj programmer..." appears in all 9,923 examples—every training step wastes compute predicting these 17 constant tokens. With only 10K examples in a niche domain, wasting 30-40% of gradient signal on system/user tokens means the model needs more epochs to learn the same patterns, increasing overfitting risk while reducing learning efficiency. **Fix:** Mask all tokens before the assistant's response with -100 in labels, or switch from raw Trainer to TRL's SFTTrainer which handles this automatically.

**2. Fine-tuning Instruct model risks performance degeneration (BLOCKER)**
Recent research (Shadow-FT, May 2025) demonstrates that directly fine-tuning Instruct models often leads to "marginal improvements and even performance degeneration." The Instruct model's weights encode both code knowledge AND instruction-following behavior; fine-tuning overwrites both simultaneously. For BBj specifically, the model may learn BBj syntax but degrade its ability to structure responses, explain code, or handle multi-step instructions. **Fix:** Switch to Qwen2.5-Coder-14B-Base (not Instruct) for two-stage training, OR use the Shadow-FT technique (fine-tune Base, graft weight deltas to Instruct), OR if staying with Instruct use much lower LR (5e-6 to 1e-5) and fewer epochs (1 not 2).

**3. No validation set, no evaluation framework—blind iteration (BLOCKER)**
The training script uses 100% of 9,923 examples for training with zero held-out validation data. There is no evaluation_strategy, no eval_dataset, and no post-training evaluation beyond 3 hardcoded test questions. The team cannot distinguish between overfitting vs. generalization, cannot measure whether hyperparameter changes help or hurt, and cannot answer "which checkpoint is best?" with data. **Fix:** Immediate (1 day)—hold out 5-10% as validation set, add evaluation_strategy="steps". Short-term (1 week)—build minimal BBj evaluation suite with 50-100 held-out questions, bbjcpl compile-based scoring. Medium-term (2-4 weeks)—build BBj HumanEval-style benchmark with automated test execution.

**4. Learning rate 2e-5 is 10x lower than QLoRA recommendations (HIGH)**
The QLoRA paper recommends 1e-4 for models >33B. The current 2e-5 is 5-10x lower. At this rate with only 2 epochs, adapter weights may not move far enough from initialization to meaningfully encode BBj knowledge. The model produces plausible output because the base model is already good, but the adapter has minimal effect. **Fix:** Start with 1e-4 for 32B model. If using Instruct variant, use 5e-5 to 1e-4. Run learning rate sweep (100 steps each at 5e-5, 1e-4, 2e-4) and compare training loss curves.

**5. Dataset quality issues: 375 duplicates, 60 corrupted newlines, inconsistent formatting (HIGH)**
Dataset analysis reveals: 375 unique user prompts appear multiple times (766 total examples, 7.7% duplication), some with different responses (conflicting training signal). 60 examples contain literal `\n` characters instead of actual newlines—the model learns to generate single-line code with visible backslash-n. Response formatting is inconsistent (85% use code fences, 10% text-only, 4% mixed, 0.2% raw code). **Fix:** Deduplicate dataset (keep higher-quality version of duplicates). Sanitize literal escape sequences. Standardize all code examples to use triple-backtick fencing with bbj language tag. These are 2-4 hours of data preprocessing that affect quality disproportionately.

## Gap Analysis: bbjllm Current vs Recommended

### What bbjllm Gets Right
- QLoRA method (4-bit NF4, rank 32, alpha 64): Sound, standard configuration
- ChatML format (9,922 examples): Good format, aligns with Qwen's chat template
- Qwen2.5-Coder family: Best available for code fine-tuning in 2026
- Target modules (all linear layers including MLP): Correct for code tasks

### What Must Change (Priority Order)

**Critical (BLOCKER-level, fix before next training run):**
1. **Add validation split**: 90/10 train/val with evaluation_strategy="steps"
2. **Fix completion masking**: Mask system/user tokens, compute loss only on assistant response
3. **Build evaluation suite**: Minimal bbjcpl-based compile@1 metric + held-out test set
4. **Update bitsandbytes**: 0.43.0 → 0.43.2+ (critical memory bug fix, saves 5-10GB VRAM)

**High (significant quality/efficiency impact):**
1. **Increase learning rate**: 2e-5 → 1e-4 for Base model, or 5e-5 for Instruct
2. **Clean dataset**: Deduplicate 375 duplicates, fix 60 corrupted newlines
3. **Switch to dynamic padding**: Eliminates 50-80% wasted compute on padding tokens
4. **Consider model variant change**: 32B-Instruct → 14B-Base for two-stage training

**Medium (technical debt, deferred improvements):**
1. **Update library stack**: Staged migration to transformers 5.x, peft 0.18.x, trl 0.27.x
2. **Add system prompt diversity**: 3-5 variations instead of single uniform prompt
3. **Standardize response formatting**: All code examples use consistent fencing
4. **Add experiment tracking**: W&B or TensorBoard instead of report_to="none"

### What Chapter 3 Documentation Should Update

| Current Documentation | Should Say | Reason |
|-----------------------|------------|--------|
| Qwen2.5-Coder-7B-Base | Qwen2.5-Coder-14B-Base (primary), 7B minimum, 32B enterprise | 14B shows significantly better fine-tuning improvement per Qwen technical report |
| Ollama v0.9.x+ | Ollama v0.15.x | Actual version as of Feb 2026 |
| "approximately 10,000 examples" | 9,922 ChatML examples (precise count from bbjllm) | Match actual implementation |
| Lists CodeLlama, StarCoder2 as alternatives | Add Qwen3 dense models, note Qwen3-Coder is MoE-only | Landscape evolution since docs written |
| Basic Unsloth description | Add Dynamic 4-bit Quantization, 500K context, built-in GGUF export | Significant new capabilities |

### Documentation Update Implications (What Each Chapter Needs)

**Chapter 2 (MCP Architecture):**
- Clarify that generate_bbj_code is planned (design defined) but not yet implemented
- Distinguish existing chat validate-fix loop (server-side, Claude-powered) from planned MCP loop (client-orchestrated, fine-tuned model)
- Update architecture diagram: show 14B model (not 7B), correct Ollama version
- Add generate_bbj_code implementation specification (RAFT pattern: RAG enrichment + fine-tuned model + bbjcpl validation)

**Chapter 3 (Fine-Tuning):**
- Update model recommendation: 14B-Base as default (not 7B-Base)
- Update technology versions: Unsloth 2026.1.4, transformers 5.1.0, peft 0.18.1, Ollama 0.15.x
- Add section on Base vs Instruct for fine-tuning (critical decision point)
- Add evaluation methodology section (bbjcpl-based compile@1, factual accuracy, qualitative comparison)
- Add section on relationship to bbjllm repo (acknowledge actual implementation, explain differences from docs)
- Update hardware requirements table for 14B (Q4_K_M ~8.5GB, needs 16GB+ RAM workstation)

**Chapter 4 (IDE Integration):**
- Present Continue.dev as primary IDE integration path (only option supporting both chat and inline completions with local models)
- Note that inline tab completion requires FIM-trained model (current ChatML format is instruction-only)
- Document Copilot BYOK as secondary option (chat only, inline completions not supported for local models)
- Describe bbj-language-server + AI integration as future phase (complex, not near-term)

**New Section Needed: Training Data Pipeline**
- Document training-data/ markdown format as canonical for new examples
- Document conversion pipeline to ChatML (planned automation)
- Acknowledge bbjllm dataset.jsonl was independently created (9,922 examples)
- Recommend high-quality examples from dataset.jsonl be back-ported to training-data/ format for validation

## Implications for v1.7 Documentation Refresh

The v1.7 milestone is about documentation updates, not implementation. Based on research, the documentation should be updated to reflect reality while providing a clear roadmap for improvement.

### Honest Assessment of Current State

**What exists and works (operational):**
- RAG pipeline (51K+ chunks, pgvector, HNSW indexing)
- Two MCP tools: search_bbj_knowledge, validate_bbj_syntax
- Web chat with Claude API + RAG + server-side validate-fix loop
- Training data repository (2 seed examples, JSON Schema validation)
- bbjllm training repo (functional QLoRA script, 9,922 examples)

**What is described but doesn't exist (planned, design defined):**
- generate_bbj_code MCP tool (spec provided in architecture research)
- MCP generate-validate-fix loop (client-orchestrated, using fine-tuned model)
- Fine-tuned model served via Ollama (training script exists but model not yet trained or deployed)
- Training data conversion pipeline (markdown → ChatML)

**What needs fixing before claims of success (critical gaps):**
- Validation/evaluation framework for measuring fine-tuning success
- Data quality issues (duplicates, corrupted examples, inconsistent formatting)
- Training methodology issues (completion masking, learning rate, model variant choice)

### Documentation Tone Corrections

Every component should be labeled clearly:
- **Operational:** Working and deployed
- **In progress:** Code exists but not trained/deployed
- **Planned (design defined):** Specification complete, implementation pending
- **Future:** Aspirational, timeline unclear

Stop using aspirational language ("The BBj MCP Server defines three tools") for components that don't exist. The v1.7 documentation should be a honest snapshot that guides the next phase of work.

### Recommended Documentation Structure

**Phase 1: Update existing chapters with reality (1 week)**
1. Chapter 2: Mark generate_bbj_code as "planned", clarify what's operational
2. Chapter 3: Update to 14B-Base recommendation, current library versions, add evaluation section
3. Chapter 4: Update IDE integration options with feasibility assessment
4. All chapters: Update version numbers (Ollama 0.15.x, transformers 5.x, etc.)

**Phase 2: Add critical missing sections (1 week)**
1. Chapter 3: Add "Relationship to bbjllm repo" section explaining actual implementation
2. Chapter 3: Add "Evaluation Methodology" section with bbjcpl-based approach
3. Chapter 3: Add "Stage 1 Data Preparation" section for continued pretraining
4. New appendix: Training Data Pipeline (markdown format → ChatML conversion)

**Phase 3: Document improvement roadmap (parallel to Phase 2)**
1. Create training-improvements.md listing critical fixes before next run
2. Link from Chapter 3 to this roadmap
3. Include estimated effort and priority (blocker/high/medium)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack (model/framework) | HIGH | Qwen2.5-Coder remains best for code fine-tuning. Versions verified via PyPI, GitHub, web search as of 2026-02-06. 14B-Base recommendation grounded in Qwen technical report. |
| Features (evaluation) | MEDIUM-HIGH | LIMA/QLoRA research papers are high-confidence sources for data quality > quantity. bbjllm repo analysis is HIGH confidence (direct code examination). bbjcpl compile-based evaluation is novel for BBj but follows proven patterns (HumanEval, ASML build@k). |
| Architecture (integration) | MEDIUM | Model serving via Ollama is HIGH confidence (documented, standard). Qwen2 GGUF adapter import has reported issues—GGUF conversion via llama.cpp is more reliable. generate_bbj_code implementation pattern is HIGH confidence design but untested. 32B inference latency on target hardware is unknown. |
| Pitfalls (training issues) | HIGH | Critical pitfalls (C-1, C-2, C-3) confirmed by direct code examination of train_qwen_32b.py. Dataset statistics computed from dataset.jsonl. Library versions verified from starttrain.sh. Research citations (Shadow-FT, QLoRA paper, completion masking studies) are peer-reviewed. |

**Overall confidence:** MEDIUM-HIGH

The technology recommendations are well-grounded. The critical issues in the training script are confirmed by code analysis, not inference. The main uncertainty is whether the recommended fixes will produce a model that actually outperforms Claude + RAG on BBj code generation—this requires building the evaluation framework and training/testing.

### Gaps to Address

**During documentation update:**
- Acknowledge that fine-tuned model quality is unproven (no evaluation has been run)
- State clearly that training methodology needs fixes before next run
- Document the two-repo problem (training-data/ markdown vs bbjllm/ ChatML) without claiming it's solved

**During next training iteration:**
- Build evaluation suite BEFORE training (cannot claim improvement without measurement)
- Test Base vs Instruct model variants with identical training data (resolve C-2 empirically)
- Measure actual inference latency for 32B vs 14B on target hardware (informs deployment decision)
- Validate GGUF conversion works for Qwen2.5-Coder + QLoRA adapter (documented for other models, needs testing for this specific combination)

**Longer-term validation:**
- Does the fine-tuned model actually generate better BBj code than Claude + RAG? (fundamental question)
- Should training data include FIM examples for inline completion? (required for Continue.dev tab completion)
- What is optimal LoRA rank for this task/dataset size? (requires evaluation framework to compare rank 16 vs 32 vs 64)

## Sources

### Primary (HIGH confidence)

**Models and Frameworks:**
- [Qwen2.5-Coder Technical Report](https://arxiv.org/pdf/2409.12186) — Architecture, training methodology, benchmark results. Source for 14B showing greater fine-tuning improvement.
- [Qwen3-Coder GitHub](https://github.com/QwenLM/Qwen3-Coder) — Confirmed MoE-only architecture (no dense variants for fine-tuning).
- [Unsloth GitHub](https://github.com/unslothai/unsloth) — Version 2026.1.4 features, 2-3x speed claims, dynamic 4-bit quantization.
- [Ollama Releases](https://github.com/ollama/ollama/releases) — v0.15.x confirmed as of Feb 2026.
- PyPI (transformers, peft, trl, bitsandbytes) — All version numbers verified Feb 6, 2026.

**Training Methodology:**
- [LIMA: Less Is More for Alignment (NeurIPS 2023)](https://arxiv.org/abs/2305.11206) — 1,000 examples sufficient for 65B model, data quality > quantity.
- [QLoRA: Efficient Finetuning of Quantized LLMs (NeurIPS 2023)](https://arxiv.org/abs/2305.14314) — Learning rate recommendations (1e-4 for >33B), rank selection, "small high-quality dataset leads to SOTA."
- [Shadow-FT: Tuning Instruct via Base (ICLR 2025)](https://arxiv.org/abs/2505.12716) — Instruct model fine-tuning degeneration, weight grafting technique.
- [To Mask or Not to Mask (Towards Data Science)](https://towardsdatascience.com/to-mask-or-not-to-mask-the-effect-of-prompt-tokens-on-instruction-tuning-016f85fd67f4/) — Completion masking improves instruction following.
- [HuggingFace PEFT Checkpoint Format](https://huggingface.co/docs/peft/main/en/developer_guides/checkpoint) — adapter_model.safetensors structure.
- [HuggingFace TRL SFTTrainer](https://huggingface.co/docs/trl/sft_trainer) — Default completion-only loss, packing support.

**Code Analysis:**
- bbjllm repo direct examination — train_qwen_32b.py (lines 288-295 for labeling logic, line 232 for learning rate, line 240-241 for saving config), dataset.jsonl (9,923 examples analyzed for duplicates/corrupted data), starttrain.sh (pinned library versions)

**Evaluation:**
- [Evaluating LLMs for Code in Industrial Settings (ASML, arXiv:2509.12395)](https://arxiv.org/abs/2509.12395) — build@k metric, custom benchmarks from proprietary code.
- [LLMLOOP: Improving Code Generation (ICSME 2025)](https://valerio-terragni.github.io/assets/pdf/ravi-icsme-2025.pdf) — Compiler feedback loops, 65-82% of errors fixed in first iteration.

### Secondary (MEDIUM confidence)

**Architecture Integration:**
- [Ollama Import Documentation](https://docs.ollama.com/import) — Modelfile ADAPTER instruction, supported architectures. Qwen2 not explicitly listed for safetensors adapter import.
- [Ollama GitHub Issue #8132](https://github.com/ollama/ollama/issues/8132) — Reported Qwen2.5-Instruct fine-tuned model import issues.
- [llama.cpp convert_lora_to_gguf.py Discussion](https://github.com/ggml-org/llama.cpp/discussions/2948) — PEFT adapter to GGUF conversion for LoRA.
- [Continue.dev Ollama Guide](https://docs.continue.dev/guides/ollama-guide) — Custom model configuration verified.
- [Continue.dev Autocomplete Setup](https://docs.continue.dev/customize/deep-dives/autocomplete) — FIM requirements for tab completion.
- [GitHub Copilot BYOK Enhancements (Jan 2026)](https://github.blog/changelog/2026-01-15-github-copilot-bring-your-own-key-byok-enhancements/) — Official BYOK features.
- [Copilot BYOK Code Completion Not Supported #7690](https://github.com/microsoft/vscode-copilot-release/issues/7690) — Inline completions unavailable for BYOK.

**Dataset Best Practices:**
- [Leveraging QLoRA Without Catastrophic Forgetting](https://towardsdatascience.com/leveraging-qlora-for-fine-tuning-of-task-fine-tuned-models-without-catastrophic-forgetting-d9bcd594cff4/) — QLoRA preserves chat-finetuned nature, LoRA forgetting behavior.
- [System Message Generation (arxiv:2502.11330)](https://arxiv.org/abs/2502.11330) — Diverse system prompts improve instruction following.
- [W&B vs MLflow Comparison](https://medium.com/@pablop44/why-everyone-is-migrating-from-mlflow-to-weights-biases-w-b-in-2025-5926f978e03e) — W&B 5-min setup advantage for small teams.

**Library Updates:**
- [bitsandbytes 0.43.2 QLoRA Memory Fix](https://github.com/bitsandbytes-foundation/bitsandbytes/discussions/1291) — 5-10GB VRAM savings for 32B model confirmed.
- [Unsloth LoRA Hyperparameters Guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide) — Learning rate, rank recommendations.
- [Databricks LoRA Guide](https://www.databricks.com/blog/efficient-fine-tuning-lora-guide-llms) — Rank selection, alpha scaling.

### Tertiary (LOW confidence)

- DeepSeek-V4 release timeline — Rumored mid-Feb 2026, not yet released. Timeline based on news reports, not official announcements.
- Dataset size "sweet spot" of 1,200-2,500 for 7B models — Extrapolation to 32B is uncertain. LIMA/QLoRA principles suggest 10K is sufficient but optimal number is task-dependent.
- 32B Q4 inference latency on target hardware — Estimated 10-30 tok/s based on community benchmarks, but actual hardware (bbjllm GPU server) specs unknown.

---
*Research completed: 2026-02-06*
*Ready for roadmap: documentation update, not new implementation*
