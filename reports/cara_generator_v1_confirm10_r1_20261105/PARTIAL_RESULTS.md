# confirm10: failed, settled; INCOMPLETE / PARTIAL results

run_id: cara-generator-v1-confirm10-r1-20261105; launch_id: fe91fe0468944be18b8c0950c33e092b

21/51 requests complete: one warm plus20 formal, covering C01-C04 only (all av). Native36 + all four candidate/control arms are complete for these4 inputs. Exactly16 full93-frame LPIPS-Alex pairs were scored on CPU once. The original10-prompt primary endpoint is NOT EVALUABLE; no full-run PASS or n=4 noninferiority/significance test.

## Frozen predictions first (no refit)

|arm|frozen mean ratio/F17|partial mean paired ratio|absolute error of mean|prompt MAE|
|---|---:|---:|---:|---:|
|R16C|0.932|0.944610|0.012610|0.027322|
|R18C|0.825|0.657741|0.167259|0.167259|
|R21C|0.652|0.450639|0.201361|0.201361|

Ratios are the mean of per-prompt ratios, not the ratio of grand means. Predictions are the frozen old-four mean ratios transferred unchanged to these new prompts. Four driving inputs do not represent the full ten-input cohort.

## Partial effects and timing

|arm|mean Alex vs same-seed Native36|mean T_DD(s)|
|---|---:|---:|
|F17_A2_LIGHT_C|0.242863|131.587780|
|R18C|0.157819|130.215855|
|R16C|0.228645|116.449585|
|R21C|0.107556|150.861645|
|NATIVE35|0.000000|252.614180|

|contrast|mean paired delta Alex|descriptive bootstrap95% CI|improved/4|
|---|---:|---|---:|
|R18C - F17|-0.085044|[-0.102794, -0.057336]|4/4|
|R16C - F17|-0.014218|[-0.022106, -0.007031]|4/4|
|R21C - F17|-0.135306|[-0.164050, -0.099059]|4/4|

Prompt bootstrap: {'unit': 'prompt', 'replicates': 100000, 'seed': 20261105, 'interval': 'linear percentile95'}; descriptive only. All executed masks match the frozen masks. Mean LPIPS monotonic R16C >= R18C >= R21C: True.

|prompt|R18C - F17 Alex|R18C - F17 T_DD(s)|direction|
|---|---:|---:|---|
|av_5da7e548-93f4-4a9f-b59d-418051e7c859|-0.094921|-1.337494|better|
|av_ba7d9ba6-04e5-4d30-a882-e51abe37aa84|-0.095079|-1.439098|better|
|av_2cdc6699-574f-40b7-9b5b-15905c540274|-0.105419|-1.385611|better|
|av_dc14df7f-b671-4d66-a98b-b751d8112e6c|-0.044755|-1.325497|better|

## Failure diagnosis and minimal recommendation

Classification: prompt safety reject. CONFIRM10_022 is R21C / av_snowy_1_0, the snowy-street/SOLNIX prompt. At2026-11-05 23:30:42 Asia/Shanghai, inference.py:112-116 logged "Guardrail blocked text2world generation" and returned before denoising. Only the1729-byte argument JSON exists; no video or latent. The runtime clean wrapper maps an empty output with zero solver steps to TEXT_REJECTED; collect_loaded:80 intentionally stops on non-COMPLETE. Container exit1/OOMKilled=false, runner exit1. This is not OOM, timeout, NaN, insufficient frames or missing input assets.
The exact safety category/token was not logged; SOLNIX, McDonalds or snow cannot be identified as the trigger from this evidence. The collection row022 remains a stale RUNNING intent, while the collection is FAILED_NO_RETRY and the process/container ended. Raw collection bytes were preserved unchanged.
Minimal recommendation: keep guardrails and frozen prompts/masks/seeds. Record the returned rejection status/reason on the row before the existing stop. Before any new run, obtain user/idea approval for prospective refusal/cohort handling; do not blindly retry022 or silently replace/drop its prompt. All five C05 arms share that prompt and could be blocked. No runner, sampling or guardrail code was changed here.

## Financial/resource closure

Original GPU/container ended at 2026-11-05T23:30:54+08:00; the00:14 check discovered an earlier terminal. Original processes ended and both locks are free. GPU-cebf7119-cf03-23b9-e192-cd196332b704 was observed Default,24MiB,0% with no compute apps. No GPU work was launched or resumed.
Unique settlement seq104: 1.331388694769962GPUh /4792.999301s. Baseline231.1691439833172 + actual = **232.50053267808718GPUh**. The4.1 reservation is removed; unspent2.768611305230038GPUh released. Reserved total16.5 is the unchanged old16.5. Legacy cap250/available0.9994673219128174 remain compatibility accounting under the standing no-cumulative-cap policy.
The server central-settlement.json was recorded, and final status reports central_settlement_pending=false. Original billing bytes and failed exit remain unchanged. The authorized partial scorer checks actual financial/resource release; it does not change or pass the full-run acceptance gates.
CPU scorer exited0/OOMKilled=false at2026-11-05T16:47:34.346298449Z UTC, CUDA_initialized=false;16 pairs each93 original432x768 frames/16fps, same-seed reference, no trimming/resampling. Both cohort-selection/incomplete-inference CPU tests pass.

## Remaining30: quote only

Remaining022-051:6 each Native36/F17/R18C/R16C/R21C,30 formal +0warm. Same CAL35 coefficients and+10%,600s load+600s release. Request sum6570.107400s; center **2.340866150GPUh**, range **1.975860183-2.523369133GPUh**, recommended hard **2.6GPUh**, wall center **2h20m27s**. This is a conservative full-request quote including022, not authority to replay the settled run. Existing21 output artifacts (20formal+1warm) remain in place for future hash-bound reuse. Native-k18 is not included.
The quote does not solve the C05 safety refusal; unchanged blind continuation may stop again. Any approved continuation must be a NEW run after protocol decision. No continuation manifest/stage/provision/reservation or GPU dispatch was created.

## Files

terminal_status.json, final_status.json, terminal.json, release.json, central_settlement.json, central_after_status.json: closure.
collection.json and output_inventory.json: all21 original output paths/sizes/hashes; files remain on the original16GiB loop56 volume.
failed_request_evidence.json and failure_diagnosis.json: exact logs/arguments and code locations.
partial_scores.json, partial_analysis.json, partial_score_launch.json, partial_score_terminal.json, partial_analysis_receipt.json: the single authorized CPU instance and results.
remaining_quote.json: all30 IDs, prices, range and no-execution authority. partial_postprocess.py and test_partial_postprocess.py: scoped CPU-only glue/tests. outcome_summary.json: machine-readable closure.
