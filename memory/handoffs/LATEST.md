# Latest — r3 Native terminal, WorldCache live

Native r3 attempted all4:3accepted (AV/common/robot),1VIDEO_REJECTED (physics); exit0 means outcomes recorded, not whole-batch pass. Supervisor measured1322.461758s. Terminal Native receipt is reports/f1_smoke_r3_native.json. Settled budget now0.8406482060750325/4GPUh, with ongoing WC cost additional.

Supervisor2431971 is still live; current WorldCache timeout child2435496 was verified live after fresh admission. Remote outputs/f1-smoke-r3/worldcache. Snapshot reports/f1_smoke_r3_worldcache_start.json is NOT terminal. No paired ratios yet. Inspect same process and receipts; do not restart or change deployed source57c8660. Local W1 preparation has not been deployed.

## Earlier snapshots (superseded for live status)

# Latest — F1 r3 live, inspect before any restart

R3 supervisor2431971 and initial Native timeout child2431976 launched after fresh admission (GPU1 24MiB, no compute apps). Remote outputs/f1-smoke-r3, source57c8660. 32 local tests, 11 Linux CPU/fake-GPU tests pass; source archive hash matched. Outcome protocol v1 uses official keep_going, records rejects without saving rejected outputs, attempts all frozen cases; same model/sampler/WC settings. Charged BEFORE launch0.4732977178361681/4GPUh; current in-flight cost is additional and not yet settled. Read reports/f1_smoke_r3_launch_20260930.json. Do not alter deployed source during run.

## Prior r2 evidence and protocol context

User chose current-code technical comparison first on2026-09-30. No protocol decision remains pending. Four Native/WC pairs, same frozen inputs/seed/93frames/432x768, UniPC/Karras35requested36actual72CFGcalls. Preserve original WC70-call horizon and record counter resets; not paperEuler reproduction. No prototype installed in F1.

F1 r2 deployed source4814657 with matching archive SHA e6229786e3ffcf1152cbd04dc3ab298ebb480902b278b61d84abed6a4c91bdb2. Local29tests pass, Linux8measurement/protocol/supervisor tests pass. Runner validates exact schedule, source hash, actual counts, and persists diagnostics before assertions. Per-call trace measures actual deep execution and WC counters identically in both arms.

TERMINAL remote root /home/gaokuangda/data/gkd/worldcache_omr, output outputs/f1-smoke-r2. Supervisor2427723 FAILED; Native timeout child2427728 exit1 after1042.542395s. Two Native samples completed; physics_001 rejected by video guardrail. No WC arm. Preserve failure denominator and inspect continuation handling; no safety bypass. Local terminal receipts: reports/f1_smoke_r2_supervisor.json and reports/f1_smoke_r2_native.json.

Budget now0.4732977178361681/4GPUh; remote reports/budget.json authoritative. R1 partial output is not reused for paired timing. No paired speed/quality result, no full-video quality review yet.

Access: two-card TCP SSH localhost33621 usergaokuangda, identity ~/.ssh/id_ed25519, HostKeyAlias=[localhost]:33620, StrictHostKeyChecking=yes. Task FRP .sync/frp_tcp; do not duplicate/shared FRP changes. Four-card login recovered (actual4RTX6000Ada), prepared two-card used. Runtime isolated; shared environment/source/cache unchanged. Projecthfhub links core caches read-only and holds all new safety assets.

All assets hash-verified, core load and full safety-pipeline compatibility passed. Guardrail access nowHTTP200. No more readiness probes needed. Currentcore adaptation: missing model dirs supplied from pinnedNVIDIA source, exact-hash registration adapter skips unrelated14B training example. Botharms share it, eager and matched offloading retained.

Latest user request: integrate latest discussion into current plans. Both plans now v1.1. Add W1-D downstream error diagnostics, non-GPU L0 audit, L1 Wan5B native/CFG-only/four-step+CFG baseline only after F1 and reserving F2/W1 budget (up to2GPUh FROM existing4h cap); J6/X3/J5-P conditional later. Read source manifest and research/09_NEXT_ACTIONS.md. No GPU job launched by this plan edit. User requests every meaningful change pushed to private GitHub; exclude weights/videos/tensors/secrets.

Cross-device entry: user requested a PhysCache-style project experiment document. `EXPERIMENT_REPORT.md` now provides the stable Chinese overview, result/evidence tables, failure history, synchronization protocol and next-dialogue prompt. Read/update it with the queue and handoff. Documentation-only update; no new runtime observation or GPU launch.

Outcome continuation prepared: r2 PIDs verified absent. Official inference keep_going returns no video for a rejected sample; new observer records text/video decisions unchanged, keeps failure denominator and permits attempting remaining original cases. Unknown errors still abort. Fresh r3 planned for both arms with same sampler/source/model. 32 local CPU tests pass. Inspect new launch receipt before any further launch; this note alone is not a launch.

Read-only continuation observation at Unix1790761244.9133024: supervisor2431971 and child2431976 live, Native GENERATING first AV sample, model load74.685959s, zero completed outcomes. New local summary CLI/tests are not deployed into the running job. After terminal receipts, archive both arms and supervisor under reports/f1_smoke_r3_{native,worldcache,supervisor}.json and run scripts/summarize_f1.py as documented in EXPERIMENT_REPORT.md. Summary is receipt evidence only; artifact integrity, GPU exclusivity and full-video review remain separate.

Latest verified r3 progress: first Native AV accepted, next common scene generating. First video copied to ignored reports/private/r3/native-av.mp4 and hash/full93-frame decode verified locally (receipt reports/f1_smoke_r3_first_native_decode.json). E2E314.462688s/denoise256.631392s;72full/0skip. This is not a paired speed or full-video quality result. Running server source remains unchanged.

W1-D preparation is local only: src/wcomr/shadow_metrics.py scores distinct residual/velocity errors and explicit-axis groups without model/cache access. Four CPU tests cover ranking reversal under an anisotropic synthetic map, read-only/RNG invariance, zero-reference and invalid values. This is not a real shadow runner or a WorldCache quality result. Do not deploy during F1.

W1 local preparation advanced: shadow_forward.py implements hash-gated sparse same-call deep-tail truth for official/scalar/shrink. begin_request(identity) mandatory; direct deep blocks+head only, RNG/buffer restoration; measurement.py ignores shadow-active hooks.48 local tests pass including pinned-forward toy output/cache/anchor parity and random/buffer restoration. Not deployed to F1 and not real-model validated. Need a bounded W1 runner plus real-model output parity/cost gate before experiments. Latest live r3 observation: Native two accepted, physics generating; retain original process identity.

Latest live progression: Native r3 physics_001 was VIDEO_REJECTED (72full/0skip), no physics mp4 exists, and original robot_000 now generating. Explicit evidence: reports/f1_smoke_r3_rejection_continuation.json (timestamp, source receipt hash and live ps included). Two Native accepted plus one rejected; not a whole-batch pass. Keep same supervisor2431971; WorldCache will follow only when Native arm exits successfully with all outcomes recorded.
