# Frozen F1 technical smoke protocol

Scope: four public PAI cases (av/common/physics/robot), seed 0, 93 frames, 432x768, guidance 7, 35 steps, Cosmos-Predict2.5-2B post-trained. Inputs and provenance are frozen in configs/smoke.jsonl and manifests/smoke.json. Exclude these four IDs from independent confirmation sets.

## Baselines and adaptations

One process per arm, Native first then official WorldCache, four samples per process. Both arms share configs/f1_setup.json; only worldcache_enabled differs. WC settings follow the public README's all-module example, with threshold/retention/probe defaults. Guardrails are retained. Eager execution and text/tokenizer CPU offloading are explicitly a local technical-smoke profile; do not equate its latency with the paper's throughput configuration. No scalar/shrink hook is installed in F1.

Use the documented source-completion runtime for both arms. The runner verifies the pinned cache module and added model-source hashes. Model loading and compatibility remain unvalidated. A source hash is provenance, not proof of numerical equivalence.

## Measurement

Record process import/load overhead separately from each sample's generation, guardrails, save, and transfer costs. Synchronized denoising/decode/text/guardrail timers are installed identically in both arms. First samples are marked cold; do not label all later samples warm without inspecting traces. Independent first/last transformer-block hooks count true full and skipped-deep calls without modifying cache decisions.

The upstream resets PyTorch peak memory inside generation. Runner CUDA peak fields explicitly refer to the period after the most recent upstream reset, not whole-run peak. The supervisor separately samples nvidia-smi every ~5 seconds across import/load/generation, retaining observed memory and other compute processes; that is sampled peak, not exact instantaneous peak.

Validate 93 decoded frames, 432x768, 16 fps and 70 CFG denoiser calls. A blocked/missing/malformed output fails the arm rather than silently shrinking the sample count. Save video size and SHA256. Review every full video before scientific interpretation; a technical pass is not a quality result.

## Launch conditions and durable execution

Do not launch before authorized auxiliary weights, core checkpoints and data-disk cache are ready. Use one admitted GPU UUID and check live memory + compute processes immediately before each arm. No eviction of other tasks. Source and configs are synchronized before launch. Configure HF_HUB_CACHE to the prepared project cache; the runner is offline.

From the experiment project, invoke scripts/supervise_f1.py with --project, --runtime, --python, --gpu-uuid and a unique --output. It runs at most the remaining 4-GPU-hour first-batch budget, serially. It writes supervisor.json, per-arm logs, per-arm receipts and GPU monitor JSONL. Child process groups inherit the project lock; an independent timeout bounds execution even if the supervisor disappears. Never restart from an observation timeout: inspect the recorded PID/process group, lock and terminal receipts first. If a supervisor dies before accounting, reconcile the existing process/runtime and charge its actual or conservative upper-bound duration before another launch.

The supervisor aborts its own process group if another compute process appears on the selected GPU. Timing from interrupted/shared GPU runs is not accepted. No training, paid scoring or wider benchmark is launched by this script.

Status: runner implemented and CPU helper tests passed; whole runner and actual Cosmos outputs are NOT_RUN because Guardrail1 official authenticated access returns HTTP 403.
