# Latest handoff — core loading passed; safety access still blocks F1

User objective: iterate autonomously per the original long-term plan, stopping only at major decisions/blockers. F0 preparation is not completion of the research goal. Last turn was progress: core-model load failure diagnosed/fixed, actual loading verified, and public acquisition advanced.

Private GitHub repository must stay synchronized. Four-card historical authentication is recovered; don't ask for a password again. Prefer prepared two-card server via the project-scoped TCP endpoint in ignored configs/hosts.local.json. Local frpc identity/config is in ignored .sync/frp_tcp with private permissions; shared FRP unchanged. Verify that process before duplicating it. No credentials in Git.

Current evidence: core loading r2 exited 0, 113.16 seconds. Tokenizer 194 keys, Reason1 729 keys, DiT 689 keys, no missing/unexpected keys. Network 2.059B params, 28 blocks, bf16 GPU, ~23.423 GiB torch peak. Core processes have exited. Total charged GPU time 0.055297 h / 4 h first-batch cap. No forward/generation, complete safety-pipeline validation, or quality/speedup result.

Runtime adaptations: missing model directories supplied from pinned NVIDIA source; src/wcomr/runtime_config.py skips only unrelated example-training registration, which otherwise requests an unused 14B checkpoint. Exact hash/model checks; selected official core experiment preserved. Both F1 arms apply same adapter. 25-test run passed plus 2 later integrity tests; previous 17-test Linux subset passed. F1 scripts are deployed; --probe-only uses the same bounded supervisor for load probes. Do not repeat unchanged core-load probes.

Major blocker: existing server HF login receives official Guardrail1 HTTP 403. User already asked for authorized weights/access. Do not disable safety filters or retry unchanged access indefinitely.

Public Qwen3Guard is downloaded: 7 files verified against official pinned metadata, offline config/tokenizer pass with transformers 4.57.1. A bounded CPU load/forward check now passes (reports/qwen_forward_20260929.json): benign text returns Safety: Safe, 12.03s, no GPU. This is component compatibility only, not full safety-pipeline or classification-quality validation. Public acquisition r1 ended with exit 124 after 1200s while SigLIP was partial; old PIDs confirmed absent. SigLIP alone resumed in the same cache with a 3600s bound, supervisor 2364279. Inspect receipts/siglip-resume-r1-{launch,child,exit}.json, siglip-resume-r1.json and log under the remote project. Confirm live PID/command or terminal exit before retrying. No GPU used for downloads.

Project hfhub has read-only-use links to the existing core model caches, validated by same-directory identity. Full F1 should set HF_HUB_CACHE=/home/gaokuangda/data/gkd/worldcache_omr/hfhub and remain offline after assets are ready.

Next: finish/verify SigLIP; obtain authorized Guardrail1 assets; validate complete safety pipeline; run matched Native/WC four-scene smoke under remaining budget. Then proceed to F2/W1 using measured cost/evidence and original plan. No training/full benchmark escalation merely because infrastructure is ready.
