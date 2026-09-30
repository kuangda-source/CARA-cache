## 最新核验 — 2026-09-30：局部解码策略复现通过，CAL已冻结

源33f080b decoder-policy-r1两个fresh进程均exit0；72net/trace/cache/latent匹配旧官方参考。decoder实际参数/buffers/normalization及运行设置相同；cuDNN benchmark=false/deterministic=true只在decode内部、TF32保持原值、离开后恢复；decode/guardrail/save/MP4/全部93帧RGB与PTS严格相同。结论LOCAL_DECODE_POLICY_REPRODUCTION_PASS，仅本工程样本/所测策略，不是独立根因证明、质量、新方法或干净耗时收益。

最新审计：supervisor2456556、child2456561/2457589、runner2456563/2457591均退出；锁可用，GPU1 24MiB/noapps，无在途任务。预算1.9977743149465987/4h，剩余2.0022256850534013。旧scalar/shrink四点NO_GAIN_IN_SCOPE不变。详见research/19_DECODER_POLICY_RESULTS.md和reports/decoder_policy_r1*.json。

官方基准1044条reference_video/image_name元数据全部连接固定prompt，0缺失/不符；reference+TFIDF0.85形成1043组，原recording/session独立性未证。CAL24及首批8在新生成前按固定hash/配额冻结，排除4工程组；DEV/CONF未冻结。见manifests/cal_v1.json。下一轮research/20_CAL_AND_W1D_PREPARATION.md：CAL前8稀疏同状态/布局明确的时间空间通道诊断，三公式冻结、所有路径共用新解码策略、off/on验证、安全拒绝保留分母。提议单batch6000秒/1.666667h，从现有余额扣除，尚未实现/启动；提交前重核资源/锁/预算/源码。不要补人评或追加GPU预算。

## 以下为历史记录

## 最新核验 — 2026-09-30：差异已定位decode输出

同源fa042d3 stage-r2两新进程均exit0，净监督634.230530秒。72net输出/cache/trace/采样/runtime identity相同，sample与decode输入hash相同，decode_output首先不同。两个guardrail各自输入输出相同；93帧完整RGB全部hash不同、时间戳相同。根因仍UNKNOWN，decoder实际权重/状态hash和局部确定性策略待验。见research/17_DECODE_INTERVAL_RESULTS.md及18_DECODER_POLICY_GATE.md。

最新终态审计：supervisor2453240及两child2453245/2454606与runner2453247/2454608均退出；锁可用，GPU1 24MiB/noapps，无在途任务。预算1.82321776939763/4h、剩余2.17678223060237。r1输出目录问题导致首见证成功而第二child显式取消，原失败/费用保留，勿误写两进程通过。下一轮卡PREPARED_NOT_IMPLEMENTED_NOT_RUN，不能当运行许可或实时准入；提交重核预算/锁/GPU，保护共享源码。数值候选仍NO_GAIN_IN_SCOPE，不推进闭环/不要求人评。

## 以下为历史记录

# Current state — 2026-09-29

Earlier sections below include historical observations; the final reviewed section and current receipts supersede them.

## Scientific status

No GPU-generated sample or measured quality/time result from this project yet. Continue WorldCache F0/F1, conditional on the remaining safety assets and full forward readiness. Core construction and weight loading have passed. OMR resource availability is not established; the project page release section still says Coming soon.

## Implemented and checked

- Pinned official WorldCache commit and cache-module SHA256.
- Pure residual calibrator: only earlier true full-compute anchors; request/model/CFG isolation; finite and shape fallback; bounded scalar coefficient; actual-anchor-gap shrinkage.
- Narrow source hook preserves the official decision/warp path and injects only the approximate residual. CPU toy tests include reset, branch isolation, and all-full behavior.
- Stateless shadow scorer exists. A real-model shadow forward/trace runner is NOT implemented; therefore no fixed-schedule shadow claim.
- 25 CPU tests passed on macOS Python 3.9 / torch 2.8.0. Separately, the complete Linux inference entry point imported successfully with one GPU visible; no model instantiation or video generation yet. See reports/linux_import_gpu*.json.

## Resources / dependencies

- Two-card server: 2 A6000 49140 MiB, driver 570.133.20. Observed VRAM 336/24 MiB and no compute apps. Must recheck immediately before launch.
- Data disk approximately 682 GiB free; root only 13 GiB free. New files and any downloads must use data disk.
- Existing Cosmos checkout has torch 2.7.1+cu128 in its venv and cached Predict2.5-2B post-trained checkpoint, tokenizer, Reason1-7B. Preserve shared checkout, environment and caches.
- Existing checkout is a locally modified research version; it cannot be assumed to be the official baseline.
- Four-card SSH recovered using the historical local authentication path. Fresh BatchMode key-only login had incorrectly excluded that path. Actual hardware is RTX 6000 Ada, not A6000; GPUs 2/3 were idle, 0/1 occupied. Driver 550.67 and glibc 2.31; retain the existing two-card runtime as current F1 candidate. FRP is already running; do not launch a duplicate shared tunnel.
- Pinned WorldCache tree lacks model source directories referenced by its inference configuration. Need a separately pinned, documented source completion shared across both baseline paths. Do not silently substitute the locally modified model.
- Guardrail1 cache snapshot currently contains only README; inspect complete safety dependencies before inference. No safety/access bypass.

## First-batch scope

User explicitly authorized the two/four A6000 resources. Start with F0 and four-scene, one-seed Native/official-WC technical smoke. One expensive job at a time, at most 4 GPU hours including failure/loading. Recheck UUID/VRAM/processes and retain PID, log, outputs and exit status. F2/W1 GPU scope follows measured F1 cost. No training or paid evaluation.

## Linux runtime probe update

Missing model directories were copied into an isolated candidate runtime from pinned NVIDIA revision a2c298b0a3df3778b973fe65e9e58877b292d8a7. No existing WorldCache source file was overwritten. Complete directory/file hashes are in manifests/runtime_completion.json. This source completion is a documented adaptation, not an untouched official checkout.

Initial use of installed cosmos-cuda 1.3.1 failed against source cosmos-oss 1.4.0. Using both workspace source packages at 1.4.0 resolved that mismatch. CPU-only import then failed because Triton requires an active CUDA driver. After fresh admission (GPU 1: 24 MiB, zero compute processes), a bounded GPU-visible import passed with exit 0. Supervisor wall time 44.876 seconds, charged 0.012466 GPU hours conservatively. GPU video jobs remain zero.

Read-only reuse of the existing Python environment remains a compatibility candidate: torch 2.7.1+cu128 differs from upstream's 2.7.0 lock, glibc is 2.31 rather than documented >=2.35. Import success does not prove model-load or numerical/latency equivalence. Full assets and model loading are still gates.

Direct Hugging Face and the old forwarded proxy endpoint both failed a bounded connection test. A task-scoped SSH proxy is being checked for asset acquisition. Missing safety assets are not disabled.

## Historical first acquisition failure (superseded by official access check below)

Auxiliary download reached the mirror but failed with GatedRepoError HTTP 403 for a Cosmos-Guardrail1 blocklist file. Durable receipt: reports/auxiliary_download_20260929.json. No auxiliary snapshot completed; download exited. This establishes failure of the attempted access path, not a universal claim about the user's account permissions. Official authenticated access is not yet verified. No GPU generation is running.

Asked for an already authorized Guardrail1 directory or authorized HF login on the server. Do not remove the guardrails to evade this dependency. Downloader now defaults to anonymous requests and permits explicit authenticated access only to https://huggingface.co. No token should be pasted into chat or Git. Public Qwen/SigLIP acquisition remains pending, as the first required dependency failed.

## Four-card authentication recovery

Historical session evidence identified an automated interactive authentication path. Reusing it established a live SSH session; the user did not need to provide a password. No credentials were printed or stored in Git. A live multiplexed connection is temporary, so a later missing control socket is not evidence that authentication requires new user input. See reports/four_card_recovery_20260929.json. Guardrail1 access remains the only known external asset blocker for the current two-card F1 candidate.

## Autonomous continuation — authenticated access and F1 execution tooling

The previous turn made progress by restoring four-card authentication and obtaining a fresh GPU inventory. This continuation verified the actual existing two-card HF login against the official huggingface.co endpoint; access to the Guardrail1 blocklist file still returns HTTP 403 GatedRepo. This supersedes the earlier uncertainty about a mirror-only failure. No credential was logged or saved locally. Receipt: reports/guardrail_official_auth_20260929.json. Human action is needed to authorize that account/model or provide an authorized asset path.

Independent progress: F1 case-set runner, bounded serial supervisor, matched eager/offload profile, stage timers, independent full/skip counters, output format/hash receipts, and process/budget handling are implemented. 22 CPU tests pass, including real subprocess tests for serial execution/accounting, budget stop and duplicate-lock rejection. Fake GPU executable tests do not constitute GPU supervision validation. On Linux, the actual Cosmos configuration classes accept all four inputs and confirm only output_dir and worldcache_enabled differ between arms. Whole runner/model load/generation remain NOT_RUN.

Public Qwen/SigLIP acquisition is being attempted separately from gated Guardrail1. Inspect the durable public-download launch/child/exit records on the two-card server before retrying or reporting completion. No additional GPU hours consumed.

## Resource acquisition continuation

A separate, project-scoped TCP visitor was established with a different local port, using the existing server authorization and verified host key. Original shared FRP and other visitors were not stopped or changed. Its config is private, mode 0600, outside Git; local metadata is in ignored configs/hosts.local.json. Several live SSH operations now succeed through it. This is observed connectivity recovery, not a long-term stability guarantee.

After confirming the previous public-download launch/child/exit files were all absent, the public-only acquisition was started once. Supervisor PID 2361014 and downloader PID 2361016 were verified live; receipt reports RUNNING on Qwen3Guard. It is bounded to 1200 seconds and uses no GPU. Guardrail1 was excluded only from this acquisition queue because it is separately blocked; it remains required by the inference runner. Inspect current receipts rather than relying on this snapshot.

F1 source snapshot 08560c9 was deployed to the two-card project directory, with matching local/remote archive SHA256. Scripts compile on Linux and the 17 selected calibration/measurement/subprocess tests pass in its torch 2.7.1 environment. They use no GPU; the supervisor tests substitute nvidia-smi and timeout. This is not a real-model run. See reports/f1_deployment_20260929.json.

Load-only progress: core probe r1 terminated with exit 1 after 41.03 process seconds, before any parameter-loading call. It exposed an unrelated 14B training-example checkpoint download during config registration. GPU budget is now 0.023864 hours before r2, still no generated video. A hash-checked registration adapter was tested and deployed identically for both F1 arms; load-only r2 supervisor 2362849 is now running. It has a 420-second upper bound and never generates. Inspect its actual terminal receipt before another probe.

## Reviewed core-model loading and public assets

R2 exited 0 after 113.16 supervised process seconds. The tokenizer (194 keys), Reason1 encoder (729 keys) and MinimalV1LVGDiT (689 keys) state loads all returned zero missing and unexpected keys. The 2,059,174,912-parameter, 28-block network resides in bfloat16 on the admitted GPU. Torch peak allocated memory was 23.423 GiB. This validates construction/weight compatibility, not forward kernels, complete safety pipeline, video generation or a scientific quality-time result. Core probe processes have exited and the GPU was released. Total charged GPU time is 0.055297 hours.

Qwen3Guard public files (7 files) match SHA256/Git-blob hashes obtained from the official pinned HF tree. Its offline config/tokenizer are accepted by transformers 4.57.1 and resolve Qwen3ForCausalLM. It has not yet been model-load/inference tested. Two new hash-integrity tests passed in addition to the existing 25-test run.

Public acquisition r1 hit its independent 1200-second deadline (exit 124) while SigLIP was incomplete. Both old processes were confirmed absent. Only SigLIP was resumed with the same cache and a 3600-second bound; supervisor PID 2364279. No repeated download of the verified Qwen snapshot. Guardrail1 remains required and blocked by official authenticated HTTP 403.

The project HF cache now links the existing immutable core model directories; same-directory identity was checked. Shared cache contents and credentials were not modified. Set HF_HUB_CACHE to the project hfhub for full F1 so newly acquired safety assets and existing core checkpoints resolve together.

## Public Qwen component forward check

The pinned Qwen3Guard component completed offline CPU loading and deterministic generation in 12.03s on the existing Linux environment. A benign red-ball prompt produced `Safety: Safe / Categories: None`. No GPU was visible or used. Receipt: reports/qwen_forward_20260929.json. This establishes component load/forward compatibility only; Guardrail1 access still blocks full safety-pipeline validation and F1 generation. SigLIP supervisor 2364279 was verified live, with 2,527,068,160 bytes downloaded at the latest observation.

## Public dependencies ready; external access blocks F1

SigLIP resume ended with exit 0 after 1451.57s. All 7 files match the official pinned metadata. CPU loading and image encoding passed in 8.60s with finite nonzero features [1,1152]. Both public safety components are now locally usable, but this does not validate the complete safety pipeline. The final official authenticated Guardrail1 check at 09:47:50 UTC still returned 403 GatedRepo. This same blocker has persisted for more than three goal turns; with independent asset work complete, the goal is blocked pending authorized weights/access. No video has been generated, no scientific claim is established, and GPU cost remains 0.055297 h.

## Guardrail access restored and F1 launched

User granted model access. Server-token official HEAD returned HTTP 200. All 81 Guardrail files passed official pinned hashes. Full text/video/face safety compatibility probe exited 0 in 43.84 supervised seconds. F1 smoke r1 launched on admitted GPU1: supervisor 2370231, Native child 2370237. Four scenes per arm, Native then official WC, offline project cache, remaining shared 4h budget. Results and actual videos are pending; the earlier external blocker is resolved.

## F1 scheduler discrepancy (latest)

First Native video passed safety and format validation, but the job failed the CFG-count assertion. Exact hook counts were not saved; native progress log shows36 iterations and CPU schedule probe independently confirms35 requested ->36 actual UniPC/Karras steps. This differs from paper35Euler and WC counter horizon70. GPU is released; cumulative cost0.183703h. One Native-only video, no WC result or quality claim. User protocol decision pending; see research/10_SAMPLER_PROTOCOL_DECISION.md.

## Current-code protocol approved; F1 r2 live —2026-09-30

User selected current-code comparison. Frozen runtime protocol records exact36-point UniPC/Karras time grid,72CFGcalls and unchangedWC70-call horizon. Local29tests/Linux8relevant CPU tests pass; source4814657 deployment hashes match. F1r2 supervisor2427723, initialNative child2427728, admitted GPU1. FourNative thenfourWC, fresh paired outputs; results pending.

## F1 r2 terminal; latest plan v1.1 — 2026-09-30

This supersedes the live snapshot above. Remote supervisor2427723 exited FAILED; Native timeout child2427728 exited1 after1042.542395s. Two Native sample receipts exist; physics_001 was blocked by output video safety. WC did not start. Local copies: reports/f1_smoke_r2_supervisor.json and reports/f1_smoke_r2_native.json. Charged total0.4732977178361681/4GPUh. No complete paired result or visual-quality claim.

The latest discussion and QuantWM attachment are integrated into both maintained plans: W1-D downstream diagnostics, bounded L0/L1 Wan5B baseline, conditional J6/X3/J5-P. Source manifest records paper/README checks, attachment hash and pending adapter validation. Current F1 protocol is unchanged. The plan edit launches no GPU job. Next actions prioritize failure review and completion of the existing comparison before new experiments.

## F1 r3 launched after outcome recording fix — 2026-09-30

R2 PIDs verified absent. Official keep_going=True permits rejection recording without saving rejected outputs; new observation wrapper preserves filter return values and rejects unexplained missing outputs. 32 local tests and11 Linux CPU/fake-GPU tests passed. Source57c8660 archive matched. Supervisor2431971/Native child2431976 verified live on freshly admitted GPU1. outputs/f1-smoke-r3; before-run budget0.4732977178361681/4GPUh. No paired result yet. Do not change running code or restart from stale status.

## R3 first Native artifact integrity verified

AV completed and common started. Local copy matches receipt hash; full93-frame decoding passes,768x432,monotonic0–5.75s timestamps. E2E314.462688s, denoising256.631392s,72full/0skip. See reports/f1_smoke_r3_first_native_decode.json. No paired result or visual-quality conclusion; no source change on the live server.

## R3 rejection continuation verified on real generation

Physics output was rejected with72full/0skip, no rejected mp4 exists, original robot scene started with supervisor/child live. See reports/f1_smoke_r3_rejection_continuation.json. This validates the outcome-continuation implementation, not quality or paired acceleration.

## R3 Native complete; WorldCache live

Native all4attempted,3accepted/1video-rejected; exit0 after1322.461758 supervised seconds. reports/f1_smoke_r3_native.json is terminal. Settled budget0.8406482060750325/4GPUh. Supervisor2431971 now runs verified-live WC child2435496; start snapshot is reports/f1_smoke_r3_worldcache_start.json. No paired result; no changes to running source.

## First real WC output and Native artifact checks

WC firstAV accepted with72calls/38full/34skip; call71counter reset observed. Input, runtime setup and protocol provenance match Native. WC common scene now generating. First-sample raw E2E213.118537s/denoise152.435226s; no complete-batch or quality conclusion. Three accepted Native videos hash-match and fully decode locally.

## R3 terminal closeout

Both arms exited0, supervisor/children absent, GPU released. Native3accepted/1rejected; WC4accepted. Three accepted-pair E2E ratios1.476–1.602 with matched setup;7artifacts hash/full-decode pass, quality review pending. Budget1.09256762723128/4GPUh settled. See research/11_F1_R3_TECHNICAL_RESULTS.md and execution audit. Continue baseline review and bounded W1 parity gate, not another F1 launch.

## W1-P0 parity gate live

Source d98f447 deployed with matching archive.49local/13LinuxCPUtests pass. Supervisor2439296/child2439301 verified live after24MiB/no-app GPU admission; outputs/w1-p0-r1,900s maximum. Settled cost before gate1.09256762723128/4GPUh. No real parity result yet and F1qualityreview remains pending.

## User scope correction

Manual semantic review was prematurely emphasized; it is not required by original F1 smoke scope and must not block W1. Continue parity and numerical diagnostics. Optional review UI is not a prerequisite; quality-equivalence still requires appropriate later evidence.

## W1-P0 terminal recovered; next candidate diagnostic prepared — 2026-09-30

Live FRPC/SSH connection succeeded. W1-P0 r1 exited0; all7parity checks pass on officialWC AV/seed0.72forward hashes,38full/34skip counts/trace,finalcache andvideo hashes match off/on; calls15/16/37/38 finite. Both artifacts independently rehashed remotely. Old PIDs absent, no project generation processes, supervisor lock available; GPU1 24MiB/no compute apps at18:52Beijing. Source files/protocol hashes match local. No new GPU job.

Budget settled1.2451972062057919/4GPUh,remaining2.754802793794208h. reports/w1_p0_r1{,_supervisor,_summary,_recovery_audit}.json archive evidence; research/12_W1_P0_TERMINAL_RESULTS.md separates implementation acceptance from candidate efficacy. Next research/13_W1_S1_PREPARATION.md is PREPARED_NOT_IMPLEMENTED_NOT_RUN: isolated three approximators on the same official state, <=900s proposed from remainingbudget only after implementation/invariance gates. Current scalar/shrink deployment hooks are not a same-state three-arm diagnostic. Manualsemanticreview remains optional, not a W1gate.

## W1-S1 implemented and CPU checked

SameStateProbe retains official deployed output, scores3approximators at fixedcalls, preserves pinnedcandidate-specificwarp and pre/postwarp distinction, resets realfullanchor trackers on request/cycle/model/expert.58localtests pass, including random state preservation, spatialflow matching to actualcandidatefirstskip, expertfallback and boundedserialsupervision. New --w1-same-state mode caps one off/on job900s under remainingbudget. Not yet LinuxCPUchecked/deployed/GPUrun.

W1-S1 r1初始化失败，未生成：启动环境缺少HF_HUB_CACHE，默认offline缓存无Guardrail1 blocklist目录。监督耗时75.011195s/0.020836443GPUh已结算；当前累计1.266033649/4GPUh。已把项目hfhub路径固定到监督器，6项本地真实子进程测试确认缓存环境，准备核验旧进程/锁后运行不同身份r2。保留[失败回执](../reports/w1_s1_r1_failure_summary.json)。

## W1-S1 r2 live after explicit cache fix

Source7e5bc10 archive matched,6LinuxsupervisorCPUchecks passed afterprior19same-statechecks. Previousr1 PIDs absent,lockavailable;GPU1admitted24MiB/noapps. supervisor2444752/child2444757/runner2444759live,actualprojectHF_HUB_CACHEverified,offgenerating. Settled1.266033649h BEFOREr2;inflightadditional. Do notmodifydeployedsource orsubmitsecondjob. Localreceipt-only summarytool preparedwith7tests,notdeployed. Resultsremainpending.

## W1-S1 r2 terminal and initial mechanism decision

Bothmodes exit0,8paritychecks pass; originalPIDsabsent/lockavailable/GPUreleased,artifactsrehashmatch. Fourpoints scalarvelocitysum-MSEratio2.531189803,shrink5.394980328,both2/4improve,nofallback;defaultNO_GAIN_IN_SCOPE. Earlier15/16improve,midtrajectory37/38worsen. See research/14_W1_S1_INITIAL_RESULTS.md. Cost1.4127196775542366/4h settled. Onefixedrevisiondecay0recentfullpairplanned <=900s;notyetlaunched. Noquality/closed-loopgain.

## Recent-full-pair revision live

Source99f554f archivehashmatches,16local/16Linuxchecks pass. FreshGPU1 24MiB/noapps,oldPIDsabsent/lockavailable; supervisor2447006/timeout2447012/runner2447014live,outputs/w1-s1-recent-r1<=900s. Decay0only,shrinkcontrol/sampling/4callsunchanged. Budget1.412719677hBEFORErevision;additionalinflight. Collectcurrentidentity,notstaler2status;nohumanannotationgate.

## Recent-pair terminal; post-model artifact mismatch found

Source99f554f revisionexit0,8checks pass; oldPIDsabsent/lockfree/GPU1released24MiB/noapps,artifactsrehashmatch. Recentvelocitysum-MSEratio2.354245909,shrink5.394980328,both2/4improve: NO_GAIN_IN_SCOPE. Exact72officialoutputs/cache/trace/samplingandall4official+shrinkscoresequalacrossruns;recentvsdefaultscalarvelocityMSEratio0.930094577stillnoadmissionsignal. CrossprocessMP4hashANDall93decodedRGBframesdiffer(MSE31.026577,MAE3.604356); notmetadataonly, firstdifferencesamplingfinal/VAE/guardrail/save/codecstageUNKNOWN. NumericalcontrastscopedMATCHED_DENOISER_ONLY,notvideo/qualityreproduction. Budget1.560151151220004/4hsettled,remaining2.439848848779996. Nextresearch/16_POST_MODEL_REPRODUCTION_GATE.md: readonlystagehashobservationsintwonewprocesses,<=900sproposed,noGPUstartyet. Noadditionalscalarrevisionorhumanannotation.
