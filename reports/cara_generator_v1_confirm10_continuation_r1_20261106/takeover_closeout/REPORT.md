# confirm10 continuation: failed after 5/25, settled and released

The continuation stopped on `CONFIRM10_032` (C07, `F17_A2_LIGHT_C`) because the generated video was rejected by the video guardrail after all 36 solver updates. This is distinct from the original C05 text rejection. The row records `VIDEO_REJECTED`, 36 solver steps and 36 guided pairs; collection status remains `FAILED_NO_RETRY`. The exact guardrail category was not logged and is not inferred. No prompt, seed, threshold, frozen layout or collection byte was changed.

Run `cara-generator-v1-confirm10-continuation-r1-20261106`; launch `e6d9ad460313484caa8f10a9b842e387`; source `4a8eb2aa5cc9a9cfc26147928cb36b1755bd8a38`; scope `fbe474f85fbd775d3d0514468cde33a76d4749b8672abbb8b45ac6445c77153d`.

## Completed outputs and scientific scope

Requests 027–031 completed all five arms for C06. Request 032 was rejected; the remaining 19 were not reached. The original C01–C04 outputs and 16 accepted scores remain reusable and unchanged. All original 42 latent/video hashes and all 10 newly accepted latent/video hashes were checked successfully. The copied collection matches source SHA-256 `0357504fde26cabe331820e09a12ccea8bbb9ff6b620ac6ac09c51f136b028b8` exactly.

The registered nine-input / 36-pair endpoint is **NOT_EVALUABLE**. The earlier ten-input endpoint also remains NOT_EVALUABLE. The complete-run score entry requires 25/25 and a successful container exit; both conditions are false. Consequently no score or analyze entry was invoked, no new Alex/LPIPS pair was computed, and no completed-input-only denominator was substituted. Five input groups now have full output arms (C01–C04 and C06), but only the previously accepted four groups have accepted LPIPS scores.

C06 timing only (not a new quality conclusion):

|arm|T_DD seconds|
|---|---:|
|NATIVE35|253.523385038|
|F17_A2_LIGHT_C|131.881076312|
|R18C|130.056056558|
|R16C|116.338662333|
|R21C|150.770512008|

## Resource and financial closure

Guardian wall interval: 2026-11-06 11:57:26.494804 to 12:21:57.477274 Asia/Shanghai, **1470.982455868274 seconds / 0.4086062377411872 GPUh**. Original container exited 1, `OOMKilled=false`; all original guardian/CLI/supervisor/runner processes ended. The selected A6000 is Default, 24 MiB, no compute process; both original locks are free. Financial/resource closure is accepted independently of scientific success.

Central reserve seq107 was settled exactly once by **seq108**, `SETTLE_ACTUAL_ADDITIVELY`. Unused reservation **1.791393762258813 GPUh** was released. Cumulative actual is **233.0136058102971 GPUh**, remaining reserved **16.5 GPUh** is the unchanged legacy liability. The legacy cap/available fields are compatibility values under the existing running-total policy, not a new budget authority. The exact same settlement receipt was mirrored to the original stage; final read-only status confirms `central_settlement_pending=false`.

## Follow-up boundary

No GPU was dispatched, restarted or reserved by takeover; no k18, P probe, score CPU, routine or monitor was started. PR3 and PR4 remain unmerged and were not approved. PR3's complete-run scoring wiring is unnecessary for this failed collection and was not used to bypass its acceptance gates.

Further scientific execution is paused pending prospective handling of the new C07 video rejection and any new-run scope and quote. Do not silently drop or replace C07, shrink the nine-input denominator, retry rejected samples, lower guardrails or continue the settled run. Existing outputs remain retained.

Evidence: [terminal capture](terminal_capture.json), [unique settlement](central_settlement.json), [release audit](release.json), [final status](final_status.json), [original-byte collection](collection.json), [failure evidence](failure_evidence.json), [outcome and hash inventory](outcome_summary.json).
