# CARA sparse refresh P probe R1 — preregistration

Date: 2026-11-05. Design: [design.md](design.md). Status: **ZERO_GPU_AMENDMENT_PENDING_SCOPE_DECISION**. The current instruction authorizes CPU amendments only: no GPU jobs, remote preparation, ledger reservation, or routines. Keep all three arms and four inputs, current hard **1.0 GPUh total**, and confirm10 priority. Dropping b0, dropping one input, or raising the limit to1.3 remains undecided.

## Provisional amendment — user has not commented on teammate analysis

Source: `zero_gpu_notes/zero_gpu.md` (with its JSON and DP script). **PROVISIONAL:** (a) sync also installs a same-age approximate uncond A-calibrator anchor; (b) S1 requires both c_P<=0.5*D and amplitude kappa<0.45. These are implemented for CPU review, not accepted GPU findings or execution authority. The unchanged three-arm design remains the canonical manifest; quote alternatives do not select a scope.

## Contamination check

**Confirmed: yes for the working residual cache.** The local pinned runtime `.sync/read-write-pinned-runtime-r1/cosmos_predict2/_src/predict2/inference/worldcache_utils.py`, SHA256 `b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903`, computes `residual_x = x_B_T_H_W_D - ori_x` at **528** and writes `self.residual_cache[current_idx] = residual_x` at **530**. This write is unconditional *within the full/non-skipped path* (the `else` at 498), rather than on every net call. A skipped path reads the cache at **398**, without this write. Full calls also update probe caches, working state and history windows at **532–547**.

At baseline commit `5e762e38`, `src/wcomr/cara_f19_speed190_sampling_r1.py:92–97` makes the P unconditional branch a skipped C; **107** updates the output delta only on true DD; **117** replaces its output by `c-delta`. `SpeedOwner` **149–160** applies `light_source` to `WC_PATH` before compiling collection. The CPU check applies that exact transform to the hash-checked source and proves the residual assignment AST survives unchanged; it executes six complete36 video-mask paths plus four amended A-step fixtures. In the current SpeedReadout source the corresponding hooks are `hidden` at **101–108**, `remember_dd` at **90–91**, `partial_result` at **93–94**, and compiler binding at **161–172**. Historical F19 positions and its age<=2 default remain unchanged.

Therefore a raw P writes the cond residual at p while uncond retains its last DD residual: subsequent light C reads different-birth residuals. The fixture confirms raw births `[29,26]`, `[32,26]`; sync births `[29,29]`, `[32,32]`, including subsequent C reads at30/33. Equal-cost c has sources19 and ages3/5. Delta and residual delta retain object identity across P; only a true DD refreshes them.

**Nuance and provisional correction:** A uses the latest calibrator anchor as well as the working residual cache (`cfg_guided_w1_deployment.py:105–123`); original raw P refreshes only the cond anchor. The initial registration synced only `residual_cache[1]`. The amendment now also appends an explicitly synthetic uncond anchor at p, with `probe_u_hat=probe_c(p)-(probe_c_DD-probe_u_DD)` and `residual_u_hat=r_c(p)-Delta_r_DD`. Both branch-difference tensors are captured only at true DD. The synthetic anchor is not passed to `observe_full`, so no synthetic P observation trains its regression. Before the next real uncond D, restore the last real-DD anchor as the regression predecessor. Receipts distinguish the synthetic anchor from the true-DD delta source. CPU A30/A33 fixtures confirm same-age latest anchors under sync and mixed ages under raw.

WC interpolation windows and WC probe caches are still not synchronized; general A/interpolated-C state equivalence is not claimed. Both video layouts remain D/C/P with light C, disabling WC interpolation/flow. Same-age anchors establish the amended mechanism in CPU code, not its endpoint benefit or a unique explanation of historical F19 failure.

**B1 post-P data: absent; gap retained.** The saved B1 manifest (`reports/cara_f19_zero_gpu_b1_manifest_readonly_r6_20261103.json`, original manifest SHA256 `5487f8db32d45a5d0f3304333bf362d9d6ec46fb3181c735d7267b78a6e398fa`) has 12 states at22/23/25/33/34/35 on the original Shared25-C parent and20 unique anchors. `src/wcomr/innovation_gain_assets_r1.py:62–70` drops the full pre-pair checkpoint, retains its identity only, and declares serialized resume unsupported. `src/wcomr/cara_f19_saved_tensor_r2.py:76–77` reads same-parent shadow-DD and C/A outputs; the saved-tensor delta-hold comparison mixes these outputs offline. There is no intervention-P continuation with both residuals and next-state teacher. Existing adjacent original-parent teachers cannot stand in for that continuation. No recovery collection, extra B1 experiment, or CPU teacher reconstruction is added.

## Frozen operations and masks

- P_delta-sync: cond real full net; output `(c, c-delta_DD)`; write `r_u = r_c - (r_c_DD-r_u_DD)` and provisionally append the same-age synthetic uncond A anchor defined above. Output, full-residual and probe differences refresh only on true DD, never on P/C. Max delta age6 is exclusive to the opt-in probe subclass. Historical F19 defaults are untouched.
- P_delta-raw/b0: identical output with no residual write-back.
- P_k: first k=14/20 of28 blocks execute on each branch; remaining layers add their latest-D per-layer residuals. Only D updates layer anchors. S1 disposable local state only, no videos. First-k selection fixes the unspecified subset in advance.
- R18C: `DDDDDDDDDDDDCDCDCCDCCDCCCDCCCCCCCCCD` (18D/18C).
- b and b0: P29/P32 replace C;18 true DD,16C,2P, delta from26.
- c: replace D22 with P22 and C24 with P24;17 true DD,17C,2P, delta from19. At the provisional0.5 P bound the quoted request cost equals R18C; measured T_DD still decides the time criterion.

All masks use one-based indices. The grammar represents P as D to enter the full path; the sampling owner selects DC and labels the executed action P. No post-hoc selection, tuning, reruns, protected inputs, or new Native/R18C videos/scores.

## S1 and automatic S2 gate

One exposed O1 input, seed0, R18C parent at step29 (true DD26, delta age3). Five modes D/C/P_sync/P14/P20, each one warmup plus three timed evaluations from the identical state, CUDA-synchronized single-pair timing, guided FP64-reduction MSE versus same-state D. Layer anchors must be collected on the original parent's D steps. Restore solver, readout, both branch caches and layer anchors before each local intervention; shadow truth never writes the deployed parent.

At30, compare raw and sync C error, each against a D teacher at that continuation's own identical solver state. For the sync kappa estimate, additionally run the no-P C control at the **same sync-continuation state**, restoring the latest-DD caches/anchors; use the same D teacher for both C errors. The raw continuation is reported separately. No S1 videos.

**PROVISIONAL gate:** median timed P_sync cost / median timed D cost <=0.5 **AND** kappa<0.45; equality passes timing and fails kappa. Kappa uses the teammate's amplitude convention, not a squared-error ratio or its LPIPS gamma transform. With d=26,p=29,t=30, freeze `cum` to the same M0A Native-drift coordinate as `zero_gpu_notes/dp_p.py`; `lambda=(cum[t]-cum[p])/(cum[t]-cum[d])`, `kappa=(sqrt(MSE_C_sync/MSE_C_noP)-lambda)/(1-lambda)`. This comes from amplitude model `C_sync/C_noP=lambda+kappa*(1-lambda)`. Do not clip negative estimates or refit drift to these outcomes. Timing includes the amended sync/anchor work. Both thresholds must pass before S2.

The callable runtime decision is `wcomr.cara_sparse_refresh_probe_r1.s1_gate`, registered in the manifest and also used by postprocessing to recompute the decision from measurements. CPU fixtures cover timing equality, timing failure, strict kappa boundary and amplitude conversion. Failure means release without S2. P_k is locally closed if k20 MSE>0.5*C MSE or either k timing ratio differs from k/28 by>10% (relative deviation). No real S1 timing/error exists. The GPU collector/ops stage remains **unprepared**; a tested gate function is not a deployed job.

## S2 and analysis

O1/O3/N1/N3 x b/b0/c =12 new videos, seed0. O1/O3/N1/N3 identities, Native descriptors and four R18C score/time rows are frozen in manifest.json from AVSLC/G17. LPIPS-Alex0.1 versus the same-seed Native at original432x768,16fps, all93 frames, with paired per-input differences. Score new videos on CPU only after terminal release and unique settlement. Do not regenerate or rescore Native/R18C. Cross-run R18C timing is explicitly a reused reference.

Facts first: per-input and mean delta-Alex/delta-T_DD for each arm; sync-minus-raw; S1 cost/errors/kappa. Go requires the provisional two-condition S1 gate and either (b) lower mean Alex, >=3/4 improved, and gain>=0.0044 Alex per added second, or (c) mean time<=R18C, >=3/4 improved and mean Alex no worse. If b and b0 both have worse mean Alex than R18C, close CFG-branch P. These are development gates, not statistical confirmation. No outcomes exist at registration. Changing the input count or arms would also require its own fixed analysis denominator; option quotes do not alter this four-input rule.

## Quote, launch and lifecycle

Rounded requested formula, provisional P bound: `70.734852 + 6.772260*nD + 0.993956*nA + 0*nLightC + (0.5*6.772260)*nP` seconds. b/b0=199.407792s each, c=192.635532s; four of each sum2365.804464s=**0.657167907GPUh**. S1 remains540s=**0.15GPUh**, unmeasured. Preserve the previous conservative accounting: add the full S1 allowance to common600s load+600s release, without subtracting the S1/load overlap. Center=`(1.1*S2_seconds+1740)/3600`; range=`([0.9,1.2]*S2_seconds+1740)/3600`.

| Quote-only scope | S2 videos | Total parent/video requests | Center GPUh | Range GPUh |
|---|---:|---:|---:|---:|
| Full b/b0/c x4 inputs |12|13|1.206218031|1.074784449–1.271934821|
| Drop b0; b/c x4 |8|9|0.962497396|0.875376657–1.006057765|
| Drop one input; b/b0/c x3 |9|10|1.025496856|0.926921670–1.074784449|

All three exceed1.0 at the upper bound; full scope fits1.3 on quote alone. No option is selected, no input is dropped, and the manifest hard limit remains1.0. Exact machine values are in `quote_options.json`. `prepare.py --quote-option {full_3_arms,drop_b0,drop_one_input} --hard-gpuh 1.3` prints a comparison without changing the canonical manifest or writing a scope choice. Even zero S1 still gives full-scope center1.056218031/upper1.121934821. The extra no-P C control is covered by the unchanged unmeasured S1 allowance, not asserted to have been timed. **No remote admission or ledger operation is authorized in this amendment.**

For any future separately authorized registration: reuse sensitivity/ops.py with --route relay (`~/.local/bin/intranet-ssh two-card`) and its then-current idle UUID binding. Keep50GiB host/90C/4GiB disk gates, real exclusivity, mainline priority, old16.5 and unique terminal settlement. Scope, per-run reservation and times must follow the user's eventual decision; this amendment selects none. Only externally arranged halfway/final checks; no routines, scheduler, heartbeat or cron. No lifecycle reference overrides the current zero-GPU instruction.

## CPU verification and scope

`cpu_check.py`/`cpu_check.json`: ten full36 pinned WC/RF/UniPC paths: six unchanged video masks plus four CPU-only A30/A33 sync/raw paths (flow off/on). Check actual residual and synthetic probe/residual anchor values, next-C births and next-A anchor reads, no synthetic uncond regression update, restoration of the real-DD predecessor, and unchanged DD-only differences. Also retain two28-block P14/P20 fixtures and synthetic analysis with the shared strict two-condition S1 gate. CUDA not initialized, no weights loaded, no GPU or ledger operation. Existing four SpeedSampling tests pass. These are local checks, not Linux production or GPU acceptance; no collector/ops launch stage is deployed. No confirm10, shared requests/runner, or sensitivity ops file is edited by this amendment.
