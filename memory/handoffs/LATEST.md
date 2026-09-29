# Latest handoff — autonomous F0/F1 continuation

The user asks for autonomous iteration per the original long-term plan, pausing only at major blockers/decisions. Preserve that scope; F0 preparation is not goal completion. No training or full benchmark is implied by this first-batch scope.

Private repository is synchronized after meaningful changes. Both server authentication paths are known: two-card uses its SSH key; four-card uses the historical local automatic authentication, with metadata only in ignored configs/hosts.local.json. Never print/store credentials in Git or ask again for a server password. FRP remains intermittent; do not duplicate the shared tunnel.

Current scientific status: no generated video or quality/speedup result. One earlier GPU-visible import passed (about 45 seconds, 0.012466 GPUh charged). 22 CPU tests pass. Actual Linux Cosmos config validation accepted the four frozen inputs and showed only output_dir/cache-enabled differences. Prepared F1 runner/supervisor is NOT_RUN on the real model. See research/04_F1_PROTOCOL.md.

Blocking evidence: reports/guardrail_official_auth_20260929.json confirms existing server HF credentials get HTTP 403 from the official Guardrail1 endpoint. Earlier mirror error was not the entire cause. User has already been asked for authorized weights or server-side account access; no need to repeat credential requests. Do not disable guardrails to evade this dependency.

Public Qwen/SigLIP acquisition is separate and may have a durable job under /home/gaokuangda/data/gkd/worldcache_omr/receipts/public-download-{launch,child,exit}.json plus public-download.json and public-download.log. Inspect live PID and terminal receipt before retrying; connection timeouts do not prove stop. It does not use GPUs.

Next: reconcile public acquisition, finish authorized safety assets when available, verify full model loading, then run matched Native/WC four-scene smoke under the 4-GPU-hour remaining budget. Continue to F2/W1 based on measured cost and evidence; don't expand to training or complex combinations without the plan's gates. No scientific result can be claimed from synthetic tests or entry-point imports.

Live acquisition identity: two-card supervisor 2361014 / downloader 2361016, public-download receipt RUNNING on Qwen as last observed. Use project-scoped TCP endpoint in ignored configs/hosts.local.json, preserving the existing SSH host-key alias. The local TCP frpc identity/config is under ignored .sync/frp_tcp, with private permissions. Shared FRP is unchanged. Do not duplicate either active acquisition or task tunnel; verify PID/cmdline first.

Deployment: source commit 08560c9 has been copied to the two-card project, archive hash matched, Linux script compilation passed, and 17 selected CPU tests passed. No need to redeploy unchanged code or rerun CPU tests; next useful work is reconciling the live public download and resolving official Guardrail access.
