# Latest — W1-S1 implementation ready for deployment gate

Same-state3candidate diagnostics implemented.58localCPUtests pass; protocol manifests/w1_same_state_protocol.json freezes4engineeringcalls anddefaults. check_w1_parity.py --same-state does newversionoff/on invariance; supervise_f1.py --w1-same-state enforcesonejob/900s, globalprojectlock/admission/conflictstop/budget. Next verify LinuxCPUtests andmatchingarchive under lock, then freshlyadmitGPU1 andlaunch w1-s1-r1 once. NOT_GPU_RUN atthissnapshot. Priorbudget1.245197206/4h; needremote recheck. Do not rerun F1/W1-P0. No humanannotation gate.

## Prior recovery snapshots

# Latest — W1-P0 terminal verified; W1-S1 preparation next

2026-09-30 18:52 北京时间实时恢复核验。GitHub/local 源码恢复基点 `75c66bd`，运行部署源为 `d98f447`。W1-P0 supervisor2439296 / timeout2439301已退出，exit0，无 stop reason。原始回执已取回，所有7项checks通过；72次输出、38full/34skip、trace、最终缓存和视频哈希严格一致，4个诊断点数值有限。两份远端视频重新哈希匹配。结果仅限官方WC、单个AV工程样本，不是候选收益。

累计1.2451972062057919/4GPUh，剩余2.754802793794208h。共享监督锁观察时可获取，无项目生成脚本活跃；GPU1 UUID GPU-cebf7119-cf03-23b9-e192-cd196332b704，24MiB/no compute apps。提交前重核，不视为持续资源保留。数据盘约677GiB可用，根盘约13GiB可用，新增文件用数据盘。

继续使用既有终端侧FRPC项目visitor后SSH，私有连接信息在ignored configs/hosts.local.json。本次已实际登录，不需重复建隧道或索取凭证。共享FRP不改动。另一台历史称四卡A6000的机器实际为RTX6000Ada，本次未重核，当前无需切换服务器。

下一任务：research/13_W1_S1_PREPARATION.md，状态PREPARED_NOT_IMPLEMENTED_NOT_RUN。实现官方同一轨迹的三近似器独立评分；现有scalar/shrink forward会改变部署，不能直接用于同状态三臂。先CPU因果性及状态检查，再新版本实机无扰动验收，准备<=900s/0.25GPUh有监督任务；本次恢复没有新增GPU运行。人工语义标注不是W1门槛。报告research/12_W1_P0_TERMINAL_RESULTS.md和reports/w1_p0_r1_{summary,recovery_audit}.json为此次结果依据。

F1 r3仍为终态：Native3接受/1拒绝，WC4接受；三组E2E比1.476–1.602。暂无新方法正结果或质量等价结论。仅继续WorldCache主线，不扩预算/训练/付费评分。代码、回执和总文档须同步GitHub，视频及秘密不入Git。

## Historical handoff snapshots (superseded by the terminal recovery above)

# Latest — W1-P0 r1 running; F1 terminal retained

Official shadow off/on parity gate launched once in outputs/w1-p0-r1, source d98f447, verified supervisor2439296 / timeout child2439301. Fresh GPU1 admission24MiB/no compute apps. Local49tests andLinux13CPU/fake-GPU tests pass; source archive hash matches. Hard bound900s, charged to original4GPUh cap. Settled BEFORE gate1.09256762723128h; in-flight cost extra. Check reports/w1_p0_r1_launch_20260930.json and live process/terminal receipt before any action. Do not modify deployed source during run.

Gate compares sameAV/seed officialWC off/on:72output hashes, deployment counts/trace, finalcache and video hashes; selectedshadowcalls15,16,37,38. A pass would validate only this engineering sample/official path, not scalar/shrink candidates or quality. Full-video review of F1 remains pending. No second expensive job.

## Prior context (historical process status)

# Latest — F1 r3 terminal, paired timing available, quality pending

Supervisor and both children verified absent; GPU1 released (24MiB, no compute apps). Both arms exit0: Native3accepted/1VIDEO_REJECTED(physics), WC4accepted. All4cases attempted per arm. Seven accepted videos locally hash/full93-frame decode pass; full-video quality review still pending.

All terminal receipts now reports/f1_smoke_r3_{native,worldcache,supervisor}.json. summarize_f1.py passed matched actual setup/input/protocol checks; reports/f1_smoke_r3_summary.json has3accepted pairs. E2E ratios AV1.475529(cold),common1.601593,robot~1.600; no aggregate/no quality-equivalent claim. Execution monitor audit reports/f1_smoke_r3_execution_audit.json. Cost1.09256762723128/4GPUh settled, remaining2.90743237276872h; no live task.

Next: read research/11_F1_R3_TECHNICAL_RESULTS.md; review complete videos; build bounded W1 parity runner, then real-model diagnostics off/on invariance, state/VRAM/cost gate before CAL experiments. Local shadow prototype/tests not yet deployed or CUDA validated. Do not rerun F1 from stale earlier notes. Keep exact approved sampler72calls/WC70horizon. No direction switch or training now.

## Historical snapshots (not current process status)

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

Latest WC observation: firstAV accepted; common now generating, supervisor2431971/child2435496 verified live. FirstAV72calls/38full/34skip, counter reset atcall71 matches frozen policy. Actualsetup/provenance compared with Native and matched. E2E213.118537s/denoise152.435226s are raw single-sample observations, no whole-batch/quality-equivalent speed claim. Snapshot reports/f1_smoke_r3_worldcache_first_snapshot.json is NOT terminal. All3accepted Native videos locally hash/full-decode pass (native_integrity receipt).

W1-P0 ready to deploy: check_w1_parity.py runs original officialWC forward then shadow instrumented same model/seed AV, calls15/16/37/38, compares72output hashes, counts/trace, final cache hash and video hash. --w1-parity supervisor launches one bounded900s task, charged to originalbudget.49CPUtests pass. No GPU launch implied by this note; inspect any w1-p0-r1 launch receipt before acting. Full-video quality remains pending, no candidate efficacy test yet.

Review UI deliverable: ignored reports/private/r3/review.html generated by scripts/build_f1_review.py; local server127.0.0.1:8765 (execsession39197), IAB tab2 marked deliverable. All7videos ready/duration5.8125/noerrors;firstpair playback ended, no quality fields filled. User/nextagent can replay full videos and export observations. This is explicitly nonblind engineering review, not final quality evidence. If server exits, reopen local HTML or serve that directory locally. W1-P0 latest live check still off pass generating32/36, no completedruns/errors yet.

LATEST USER SCOPE CORRECTION: Manual semantic review is NOT an F1/W1 gate. Original F1 covers generation/spec/cache/VRAM/time; final-quality human comparison appears later in plan section4.4. Prior repeated full-video-review-pending notes are a quality-claim limitation, not a blocker. Do not require user annotation or recreate PhysCache evaluation workflow. Continue running W1-P0 and numerical diagnostics; the review page is optional. No stop/restart of current job implied.
