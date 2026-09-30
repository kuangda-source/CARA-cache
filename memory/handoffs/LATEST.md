# User decision resolved — F1 r2 preparation

2026-09-30 user explicitly chose current-code technical comparison first. Approval supersedes decision-pending sections below. New frozen protocol validates exact36-point UniPC/Karras grid,72CFGcalls, unchangedWC70-call horizon; per-call trace records counter reset. Run fresh4+4 paired outputs; do not reuse r1 timing because it lacks measured receipt. First-batch budget remains4GPUh with0.183703h used before r2.

# Latest: F1 stopped; sampler protocol decision pending

F1 r1 Native generated one valid-format video and passed safety, then failed the 70-CFG-call assertion. Supervisor 2370231/child 2370237 exited (code 1, 418.42s); GPU is free. Total budget 0.183703/4h. WC never ran. Exact observed block counts were lost before the assertion; do not invent a receipt. Artifact reports/private/native-r1-av.mp4 is excluded from Git, hash/format receipt in reports/f1_smoke_r1_artifact.json.

CPU diagnostic of the actual runtime proves default FlowUniPCMultistepScheduler with Karras mode yields 36 steps for requested35, not paper35Euler. WorldCache horizon remains70 vs actual72 calls, causing early reset. User decision asked: complete public-code four-case technical baseline then separately add Euler (recommended), or reconstruct/validate35Euler first. Answer pending; do not launch dependent GPU work. See research/10_SAMPLER_PROTOCOL_DECISION.md. Runner now saves pending sample/scheduler/count data before assertions but still rejects non70 counts; diagnostic code compiled, not yet deployed. All source and safety preparation remains usable.

# Latest handoff — F1 smoke r1 running

User authorized autonomous WorldCache/OMR experimentation with a private GitHub repo and stopping only for major decisions. Guardrail permission blocker is resolved: screenshot granted access and server token official HEAD HTTP 200. No new login/token needed. All 81 required Guardrail files downloaded and hash-verified; Qwen/SigLIP already verified and CPU forward tested. Full retained safety GPU probe passed, 43.84 supervised seconds, with actual Blocklist, Qwen3Guard, VideoContentSafetyFilter and RetinaFaceFilter. Compatibility on benign synthetic inputs only.

F1 launched on the prepared two-card server GPU1 UUID GPU-cebf7119-cf03-23b9-e192-cd196332b704 after admission (24MiB, no compute apps). Supervisor 2370231, Native timeout child 2370237. Remote root /home/gaokuangda/data/gkd/worldcache_omr, outputs/f1-smoke-r1. It runs Native then official WorldCache, four frozen cases each, sequentially under remaining 4 GPU-hour cap. Inspect supervisor.json, native/receipt.json, worldcache/receipt.json, logs and actual processes; never restart on an observation timeout. No videos confirmed yet.

Use project TCP SSH localhost33621, gaokuangda key id_ed25519, HostKeyAlias=[localhost]:33620, StrictHostKeyChecking=yes. Private task FRP .sync/frp_tcp; shared FRP unchanged. Four-card historical auth works, actual hardware 4 RTX6000Ada; retain two-card prepared runtime. Project cache hfhub combines read-only core links and new safety weights. Shared source/env/cache unchanged. No secrets in Git.

Core construction r2 passed with no missing/unexpected keys, 2.059B params, 28 blocks, bf16 GPU. Full forward and scientific results remain unproven. Budget used before F1 is 0.067475 h, including all imports/loading/failures; authoritative budget is remote reports/budget.json, written after each arm. Last local full CPU suite 27 passed. Safety probe and supervisor extensions deployed at 06656fc.

Runtime adaptations: missing model directories copied from pinned NVIDIA source, hash manifest; source registration adapter skips unrelated 14B user-training example registration only. Identical both arms. F1 uses eager execution and matched offloading/guardrails; compare local results, not paper throughput. No scalar/shrink prototype installed in F1.

Next: reconcile F1 results and budget, fix genuine runtime failures without weakening the protocol, review all complete videos, then size F2/W1 from measured costs per original plans. W1 real-model shadow runner remains unimplemented. No scientific speed/quality claim until paired evidence. Commit/push each meaningful change; keep weights/videos/tensors/secrets out of Git.
