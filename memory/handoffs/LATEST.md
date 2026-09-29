# Handoff

Read research current state and next actions. Private repo created and authenticated via Git SSH. Initial upstream README commit af8e4c59e7035b600ec0f1ab0e7d7538d6dc11ae.

Do not restart FRP: user alias frpc_cnct maps to an already-running shared process. Two-card SSH works intermittently, four-card key authentication is unresolved. No GPU workload has been launched by this project.

Continue with isolated Linux runtime import, not more automation scaffolding. Missing model source in WorldCache is the immediate technical blocker. Existing shared Cosmos source includes local research changes; use it only as a read-only reference and dependency asset inventory. Guardrail dependency completeness still needs verification. OMR release is pending.

Update: GPU-visible offline import passed (45 seconds); see reports. No model was loaded and no video generated. Runtime candidate at /home/gaokuangda/data/gkd/worldcache_omr/runtime. Use PYTHONPATH=.:packages/cosmos-oss:packages/cosmos-cuda with the read-only existing .venv; this is not an exact upstream dependency lock. Next bottleneck: missing safety weights and complete model-load validation. Do not repeat the import probe without a new reason.
