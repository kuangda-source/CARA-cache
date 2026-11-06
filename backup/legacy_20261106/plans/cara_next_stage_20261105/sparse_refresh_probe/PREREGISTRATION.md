# CARA sparse refresh P probe R1 — preregistration

Date: 2026-11-05. Design: [design.md](design.md). Status: **USER_APPROVED_PENDING_PRODUCTION_CPU_AND_FRESH_ADMISSION**. Latest user approval: **「P 探针硬限放到 1.05 GPUh，设计不动，空闲卡上跑」**. Selected scope is four inputs x two sync arms b/c, S2=8 videos, with raw comparison retained only in S1. Launch and its1.05 GPUh reservation are authorized only when quote center AND upper are <=1.05, production CPU acceptance passes, and the GPU other than confirm10 is freshly idle; confirm10 has priority. Exact upper quote1.006057765333 GPUh is within the new limit. No routines.

## Confirmed design amendment

Source: `zero_gpu_notes/zero_gpu.md` (with its JSON and DP script). **CONFIRMED:** (a) sync also installs a same-age approximate uncond A-calibrator anchor; (b) S1 requires both c_P<=0.5*D and amplitude kappa<0.45. The user confirmed these design choices; GPU timing and quality remain unmeasured. The user's new scope decision selects b/c on all four inputs; old alternative-scope quotes are removed.

## Contamination check

**Confirmed: yes for the working residual cache.** The local pinned runtime `.sync/read-write-pinned-runtime-r1/cosmos_predict2/_src/predict2/inference/worldcache_utils.py`, SHA256 `b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903`, computes `residual_x = x_B_T_H_W_D - ori_x` at **528** and writes `self.residual_cache[current_idx] = residual_x` at **530**. This write is unconditional *within the full/non-skipped path* (the `else` at 498), rather than on every net call. A skipped path reads the cache at **398**, without this write. Full calls also update probe caches, working state and history windows at **532–547**.

At baseline commit `5e762e38`, `src/wcomr/cara_f19_speed190_sampling_r1.py:92–97` makes the P unconditional branch a skipped C; **107** updates the output delta only on true DD; **117** replaces its output by `c-delta`. `SpeedOwner` **149–160** applies `light_source` to `WC_PATH` before compiling collection. The CPU check applies that exact transform to the hash-checked source and proves the residual assignment AST survives unchanged; it executes four complete36 b/c paths plus two S1-only raw paths and four amended A-step fixtures. In the current SpeedReadout source the corresponding hooks are `hidden` at **101–108**, `remember_dd` at **90–91**, `partial_result` at **93–94**, and compiler binding at **161–172**. Historical F19 positions and its age<=2 default remain unchanged.

Therefore a raw P writes the cond residual at p while uncond retains its last DD residual: subsequent light C reads different-birth residuals. The fixture confirms raw births `[29,26]`, `[32,26]`; sync births `[29,29]`, `[32,32]`, including subsequent C reads at30/33. Equal-cost c has sources19 and ages3/5. Delta and residual delta retain object identity across P; only a true DD refreshes them.

**Nuance and confirmed correction:** A uses the latest calibrator anchor as well as the working residual cache (`cfg_guided_w1_deployment.py:105–123`); original raw P refreshes only the cond anchor. The initial registration synced only `residual_cache[1]`. The amendment now also appends an explicitly synthetic uncond anchor at p, with `probe_u_hat=probe_c(p)-(probe_c_DD-probe_u_DD)` and `residual_u_hat=r_c(p)-Delta_r_DD`. Both branch-difference tensors are captured only at true DD. The synthetic anchor is not passed to `observe_full`, so no synthetic P observation trains its regression. Before the next real uncond D, restore the last real-DD anchor as the regression predecessor. Receipts distinguish the synthetic anchor from the true-DD delta source. CPU A30/A33 fixtures confirm same-age latest anchors under sync and mixed ages under raw.

WC interpolation windows and WC probe caches are still not synchronized; general A/interpolated-C state equivalence is not claimed. Both video layouts remain D/C/P with light C, disabling WC interpolation/flow. Same-age anchors establish the amended mechanism in CPU code, not its endpoint benefit or a unique explanation of historical F19 failure.

**B1 post-P data: absent; gap retained.** The saved B1 manifest (`reports/cara_f19_zero_gpu_b1_manifest_readonly_r6_20261103.json`, original manifest SHA256 `5487f8db32d45a5d0f3304333bf362d9d6ec46fb3181c735d7267b78a6e398fa`) has 12 states at22/23/25/33/34/35 on the original Shared25-C parent and20 unique anchors. `src/wcomr/innovation_gain_assets_r1.py:62–70` drops the full pre-pair checkpoint, retains its identity only, and declares serialized resume unsupported. `src/wcomr/cara_f19_saved_tensor_r2.py:76–77` reads same-parent shadow-DD and C/A outputs; the saved-tensor delta-hold comparison mixes these outputs offline. There is no intervention-P continuation with both residuals and next-state teacher. Existing adjacent original-parent teachers cannot stand in for that continuation. No recovery collection, extra B1 experiment, or CPU teacher reconstruction is added.

## Frozen operations and masks

- P_delta-sync: cond real full net; output `(c, c-delta_DD)`; write `r_u = r_c - (r_c_DD-r_u_DD)` and append the same-age synthetic uncond A anchor defined above. Output, full-residual and probe differences refresh only on true DD, never on P/C. Max delta age6 is exclusive to the opt-in probe subclass. Historical F19 defaults are untouched.
- P_delta-raw: identical output with no residual or calibrator-anchor write-back; S1 local comparison only, no S2 video arm.
- P_k: first k=14/20 of28 blocks execute on each branch; remaining layers add their latest-D per-layer residuals. Only D updates layer anchors. S1 disposable local state only, no videos. First-k selection fixes the unspecified subset in advance.
- R18C: `DDDDDDDDDDDDCDCDCCDCCDCCCDCCCCCCCCCD` (18D/18C).
- b: P29/P32 replace C;18 true DD,16C,2P, delta from26; sync enabled.
- c: replace D22 with P22 and C24 with P24;17 true DD,17C,2P, delta from19. At the confirmed0.5 P bound the quoted request cost equals R18C; measured T_DD still decides the time criterion.

All masks use one-based indices. The grammar represents P as D to enter the full path; the sampling owner selects DC and labels the executed action P. No post-hoc selection, tuning, reruns, protected inputs, or new Native/R18C videos/scores.

## S1 and automatic S2 gate

One exposed O1 input, seed0, R18C parent at step29 (true DD26, delta age3). Five modes D/C/P_sync/P14/P20, each one warmup plus three timed evaluations from the identical state, CUDA-synchronized single-pair timing, guided FP64-reduction MSE versus same-state D. Layer anchors must be collected on the original parent's D steps. Restore solver, readout, both branch caches and layer anchors before each local intervention; shadow truth never writes the deployed parent.

At30, compare raw and sync C error, each against a D teacher at that continuation's own identical solver state. For the sync kappa estimate, additionally run the no-P C control at the **same sync-continuation state**, restoring the latest-DD caches/anchors; use the same D teacher for both C errors. The raw continuation is reported separately. No S1 videos.

**CONFIRMED gate:** median timed P_sync cost / median timed D cost <=0.5 **AND** kappa<0.45; equality passes timing and fails kappa. Kappa uses the teammate's amplitude convention, not a squared-error ratio or its LPIPS gamma transform. With d=26,p=29,t=30, freeze `cum` to the same M0A Native-drift coordinate as `zero_gpu_notes/dp_p.py`; `lambda=(cum[t]-cum[p])/(cum[t]-cum[d])`, `kappa=(sqrt(MSE_C_sync/MSE_C_noP)-lambda)/(1-lambda)`. This comes from amplitude model `C_sync/C_noP=lambda+kappa*(1-lambda)`. Do not clip negative estimates or refit drift to these outcomes. Timing includes the amended sync/anchor work. Both thresholds must pass before S2.

The callable runtime decision is `wcomr.cara_sparse_refresh_probe_r1.s1_gate`, registered in the manifest and also used by postprocessing to recompute the decision from measurements. CPU fixtures cover timing equality, timing failure, strict kappa boundary and amplitude conversion. Failure means release without S2. P_k is locally closed if k20 MSE>0.5*C MSE or either k timing ratio differs from k/28 by>10% (relative deviation). No real S1 timing/error exists. The collector and lifecycle entry are implemented in this probe directory. They require deployment and GPU-hidden production CPU acceptance before dispatch; a passing tiny fixture is not GPU acceptance.

## S2 and analysis

O1/O3/N1/N3 x {b,c} =8 new videos, seed0. O1/O3/N1/N3 identities, Native descriptors and four R18C score/time rows are frozen in manifest.json from AVSLC/G17. LPIPS-Alex0.1 versus the same-seed Native at original432x768,16fps, all93 frames, with paired per-input differences. Score new videos on CPU only after terminal release and unique settlement. Do not regenerate or rescore Native/R18C. Cross-run R18C timing is explicitly a reused reference.

Facts first: per-input and mean delta-Alex/delta-T_DD for b/c, plus local S1 sync/raw costs/errors/kappa. Go requires the confirmed two-condition S1 gate and either (b) lower mean Alex, >=3/4 improved, and gain>=0.0044 Alex per added second, or (c) mean time<=R18C, >=3/4 improved and mean Alex no worse. Removing the raw endpoint arm makes the original paired-sync/raw endpoint closure criterion unevaluable; no replacement closure claim is introduced. S1 raw comparison is not an endpoint LPIPS comparison. These are development gates, not statistical confirmation. No outcomes exist at registration.

## Quote, launch and lifecycle

Exact decimal arithmetic on the requested coefficients, confirmed P upper bound: `70.734852 + 6.772260*nD + 0.993956*nA + 0*nLightC + (0.5*6.772260)*nP` seconds. b=199.407792s, c=192.635532s; four of each sum**1568.173296s=0.435603693333GPUh**. S1 remains540s=**0.15GPUh**, unmeasured. Preserve the established quote accounting: full S1 allowance plus common600s load+600s release, without subtracting the S1/load overlap. Center=`(1.1*S2_seconds+1740)/3600`; range=`([0.9,1.2]*S2_seconds+1740)/3600`.

| Selected scope | S2 videos | Total parent/video requests | Center GPUh | Range GPUh |
|---|---:|---:|---:|---:|
| b/c x4 inputs |8|9|0.962497396|0.875376657333–1.006057765333|

Center is exactly**3464.9906256s**; range exactly**[3151.3559664,3621.8079552]s**. Hard1.05GPUh=3780s. The upper quote is below the hard limit by exactly**158.1920448s**. Decimal source totals are saved in quote.json. S1 also has20 local evaluations and the step30 comparisons; the extra no-P C control remains within the unchanged unmeasured S1 allowance, not a measured cost claim. **The quote now passes.** Commit/push before any GPU execution; next require affected-path production CPU acceptance and fresh capacity/UUID admission. No other scope option is selected.

Conditional lifecycle: only if both quote bounds pass may sensitivity/ops.py --route relay (`~/.local/bin/intranet-ssh two-card`) read the live GPUs and confirm10's exact UUID, selecting only the other idle UUID. Guardian50GiB host/90C/4GiB disk gates and actual exclusivity remain unchanged. Record the user's approval above, reserve1.05 only at actual launch, preserve old16.5 and settle actual once at the end. One session S1->gate->S2; only externally arranged halfway/final checks, no routines. Use only the card other than confirm10, and recheck host memory, disk, GPU processes and locks immediately before reservation/dispatch. No confirm10 path is edited.

## CPU verification and scope

`cpu_check.py`/`cpu_check.json`: ten full36 pinned WC/RF/UniPC paths: four b/c video-mask paths, two S1-only raw fixtures and four CPU-only A30/A33 sync/raw paths (flow off/on). Check actual residual and synthetic probe/residual anchor values, next-C births and next-A anchor reads, no synthetic uncond regression update, restoration of the real-DD predecessor, and unchanged DD-only differences. Retain two28-block P14/P20 fixtures and synthetic analysis for exactly8 S2 pairs with the shared strict two-condition S1 gate. CUDA not initialized, no weights loaded, no GPU or ledger operation. Existing four SpeedSampling tests pass. These are local checks, not Linux production or GPU acceptance; collector/ops readiness and its frozen source receipt are recorded in RUN_HANDOFF.md. No confirm10, shared requests/runner, or sensitivity ops file is edited.

## Admission result

The 2026-11-05T22:36:00.092395+08:00 read-only precheck found the non-confirm10 GPU idle, but host MemAvailable=30367076KiB (28.960300GiB), below the unchanged50GiB admission gate. Receipt: `reports/cara_sparse_refresh_probe_r1_20261105/precheck.json`. No reservation or launch followed that observation; later source-only deployment is recorded separately in RUN_HANDOFF.md. Real timing/quality remain unmeasured.

## Data-collection entry

`runner.py` reuses the sensitivity runner loading and admitted handoff validation, binding its collector to `collector.py`. S1 runs one guarded O1/R18C prefix through28, then20 same-state local evaluations at29 (five modes x one warmup/three timed), followed by the registered raw/sync/no-P C30 comparisons. The solver update uses the pinned sampler's extra outer batch axis; raw/sync P29 velocities and resulting solver states must be exactly equal before sharing D30. Parent cache storage is retained read-only with version checks, mutable topology/buffers/solver/RNG are restored outside timings, and only layers14..27 are cached for P_k to avoid storing unused first14 residuals. No S1 video or decoder runs.

The job writes `s1.json`, evaluates the unchanged dual gate, and returns normally with `collection.json.status=S1_GATE_STOP` and all8 S2 rows NOT_REACHED if it fails. On pass it calls the existing full-request b/c routes, writing8 new videos/latents and preserving the Native/R18C references. The allocation guardian owns one session and one final wall bill in either branch. Gate-stop is not a successful S2 endpoint result and must not be rescored or replayed.

`runtime_cpu.py` executes the real pinned sampler/RF/WC/UniPC with a tiny28-block network, tests both gate branches for flow off/on, and checks all8 S2 masks on each pass. Gate outcomes are explicitly forced only in this CPU fixture after real local measurements, because CPU cost ratios are not GPU admission. It also checks that the launch command rejects49GiB before creating authority, reserving, or dispatching. `linux_cpu.py` adds actual production imports with CUDA hidden and lazy initialization/downloads forbidden.
