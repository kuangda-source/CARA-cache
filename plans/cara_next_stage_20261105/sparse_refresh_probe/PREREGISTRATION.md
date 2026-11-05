# CARA sparse refresh P probe R1 — preregistration

Date: 2026-11-05. Design: [design.md](design.md). Status: **BLOCKED_QUOTE_EXCEEDS_HARD_LIMIT**. No GPU request, remote preparation, reservation, or launch. User authority is idle two-card capacity only, one session for S1 then conditional S2, hard **1.0 GPUh total**, with confirm10 taking priority. The complete requested quote fails before dispatch; no scope reduction or budget increase is inferred.

## Contamination check

**Confirmed: yes for the working residual cache.** The local pinned runtime `.sync/read-write-pinned-runtime-r1/cosmos_predict2/_src/predict2/inference/worldcache_utils.py`, SHA256 `b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903`, computes `residual_x = x_B_T_H_W_D - ori_x` at **528** and writes `self.residual_cache[current_idx] = residual_x` at **530**. This write is unconditional *within the full/non-skipped path* (the `else` at 498), rather than on every net call. A skipped path reads the cache at **398**, without this write. Full calls also update probe caches, working state and history windows at **532–547**.

At baseline commit `5e762e38`, `src/wcomr/cara_f19_speed190_sampling_r1.py:92–97` makes the P unconditional branch a skipped C; **107** updates the output delta only on true DD; **117** replaces its output by `c-delta`. `SpeedOwner` **149–160** applies `light_source` to `WC_PATH` before compiling collection. The CPU check applies that exact transform to the hash-checked source and proves the residual assignment AST survives unchanged; it then executes six complete36 tiny WC/RF/UniPC paths. In the new source the corresponding hooks are `hidden` at **101–108**, `remember_dd` at **90–91**, `partial_result` at **93–94**, and compiler binding at **161–172**. Historical F19 positions and its age<=2 default remain unchanged.

Therefore a raw P writes the cond residual at p while uncond retains its last DD residual: subsequent light C reads different-birth residuals. The fixture confirms raw births `[29,26]`, `[32,26]`; sync births `[29,29]`, `[32,32]`, including subsequent C reads at30/33. Equal-cost c has sources19 and ages3/5. Delta and residual delta retain object identity across P; only a true DD refreshes them.

**Nuance:** A/interpolated C can read the two history windows (`worldcache_utils.py:414–455`), not simply `residual_cache`. Cond-only full calls also make those histories asymmetric. The registered sync writes only `residual_cache[1]`; it does not synchronize the windows, probe state, or true-D calibrator anchors. Both new video layouts contain only D/C/P and use light C, which disables interpolation/flow. This confirms a contamination mechanism, not that it uniquely caused F19's endpoint failure or that sync improves video quality.

**B1 post-P data: absent; gap retained.** The saved B1 manifest (`reports/cara_f19_zero_gpu_b1_manifest_readonly_r6_20261103.json`, original manifest SHA256 `5487f8db32d45a5d0f3304333bf362d9d6ec46fb3181c735d7267b78a6e398fa`) has 12 states at22/23/25/33/34/35 on the original Shared25-C parent and20 unique anchors. `src/wcomr/innovation_gain_assets_r1.py:62–70` drops the full pre-pair checkpoint, retains its identity only, and declares serialized resume unsupported. `src/wcomr/cara_f19_saved_tensor_r2.py:76–77` reads same-parent shadow-DD and C/A outputs; the saved-tensor delta-hold comparison mixes these outputs offline. There is no intervention-P continuation with both residuals and next-state teacher. Existing adjacent original-parent teachers cannot stand in for that continuation. No recovery collection, extra B1 experiment, or CPU teacher reconstruction is added.

## Frozen operations and masks

- P_delta-sync: cond real full net; output `(c, c-delta_DD)`; write `r_u = r_c - (r_c_DD-r_u_DD)` after the pair. Both differences refresh only on true DD, never on P/C. Max delta age6 is exclusive to the opt-in probe subclass.
- P_delta-raw/b0: identical output with no residual write-back.
- P_k: first k=14/20 of28 blocks execute on each branch; remaining layers add their latest-D per-layer residuals. Only D updates layer anchors. S1 disposable local state only, no videos. First-k selection fixes the unspecified subset in advance.
- R18C: `DDDDDDDDDDDDCDCDCCDCCDCCCDCCCCCCCCCD` (18D/18C).
- b and b0: P29/P32 replace C;18 true DD,16C,2P, delta from26.
- c: replace D22 with P22 and C24 with P24;17 true DD,17C,2P, delta from19. "Equal cost" is a hypothesis checked against measured T_DD; at the conservative0.55 P quote it costs0.677226s more than R18C per request.

All masks use one-based indices. The grammar represents P as D to enter the full path; the sampling owner selects DC and labels the executed action P. No post-hoc selection, tuning, reruns, protected inputs, or new Native/R18C videos/scores.

## S1 and automatic S2 gate

One exposed O1 input, seed0, R18C parent at step29 (true DD26, delta age3). Five modes D/C/P_sync/P14/P20, each one warmup plus three timed evaluations from the identical state, CUDA-synchronized single-pair timing, guided FP64-reduction MSE versus same-state D. Layer anchors must be collected on the original parent's D steps. Restore solver, readout, both branch caches and layer anchors before each local intervention; shadow truth never writes the deployed parent.

At30, compare raw and sync C error, each against a D teacher at that continuation's own identical solver state. This avoids calling two different P29 continuations a single same-state teacher. No S1 videos.

The planned job proceeds to S2 only if median timed P_sync cost / median timed D cost <=0.55. Failure releases the single session without S2. P_k is locally closed if k20 MSE>0.5*C MSE or either k timing ratio differs from k/28 by>10% (relative deviation). S1 timings/ratios are unmeasured. The GPU S1 collector and automatic job gate are **not staged or claimed operational**, because the mandatory quote gate already fails.

## S2 and analysis

O1/O3/N1/N3 x b/b0/c =12 new videos, seed0. O1/O3/N1/N3 identities, Native descriptors and four R18C score/time rows are frozen in manifest.json from AVSLC/G17. LPIPS-Alex0.1 versus the same-seed Native at original432x768,16fps, all93 frames, with paired per-input differences. Score new videos on CPU only after terminal release and unique settlement. Do not regenerate or rescore Native/R18C. Cross-run R18C timing is explicitly a reused reference.

Facts first: per-input and mean delta-Alex/delta-T_DD for each arm; sync-minus-raw; S1 cost/errors. Go requires the S1 cost gate and either (b) lower mean Alex, >=3/4 improved, and gain>=0.0044 Alex per added second, or (c) mean time<=R18C, >=3/4 improved and mean Alex no worse. If b and b0 both have worse mean Alex than R18C, close CFG-branch P. These are development gates, not statistical confirmation. No outcomes exist at registration.

## Quote, launch and lifecycle

Rounded requested formula: `70.734852 + 6.772260*nD + 0.993956*nA + 0*nLightC + (0.55*6.772260)*nP` seconds. b/b0=200.085018s each, c=193.312758s; four of each sum2373.931176s=**0.659425327GPUh**. S1 is an explicit design allowance540s=**0.15GPUh**, unmeasured. Add full S1 allowance to the required common600s load+600s release; this conservatively overlaps the design's approximate S1 load allowance. Center `(1.1*S2_seconds+1200+540)/3600`=**1.208701193GPUh**; range `[0.9,1.2]*S2_seconds+1200+540`=**[1.076816127,1.274643725]GPUh**. Hard **1.0GPUh**.13 parent/video requests: one S1 prefix plus12 S2 videos; S1 also has20 local evaluations and the step30 comparison.

Even assigning **zero** cost to all S1 yields center**1.058701193** and upper**1.124643725GPUh**. Thus possible S1/load overlap cannot change refusal. **Launch condition1 fails; stop without remote admission or ledger transaction.** CPU checks pass. Current idle-card condition is deliberately untested after quote refusal; no idle UUID is claimed.

For any admissible future registration: reuse sensitivity/ops.py with --route relay (`~/.local/bin/intranet-ssh two-card`), but bind the live idle GPU UUID rather than inheriting ops.py's historical hardcoded UUID. Keep50GiB host/90C/4GiB disk gates, real exclusivity and mainline priority. Reserve exactly1.0 only at launch, preserve old16.5, settle actual once at terminal. One session S1 then gated S2;600s stop-new-work margin, hard3600s. Only externally arranged halfway/final checks; no routines, scheduler, heartbeat or cron. No launch/settlement instruction here overrides the failed quote.

## CPU verification and scope

`cpu_check.py`/`cpu_check.json`: six full36 pinned WC/RF/UniPC paths (b,b0,c x flow off/on), actual sync write and following-C birth checks, unchanged true-DD deltas, two28-block P14/P20 exact-shape/value/call-count fixtures, synthetic go/no-go analysis. CUDA not initialized, no weights loaded, no GPU or ledger operation. Existing four SpeedSampling tests pass after introducing subclass hooks. These are local implementation checks; no Linux production or GPU timing/quality acceptance is claimed. Sampling hooks and offline scaffold are complete; no runnable S1/ops GPU collector is supplied after the quote refusal.
