# Endpoint runner CPU original-handle handoff

## R4 complete: original terminal accepted; do not replay

- Source: `835032f6a7cf3118cbb3b33755a97706ec70a564` (published and remote ref verified).
- Host: two_card only.
- Stage: `/data20t/gaokuangda/worldcache_workspace/.sync/cara-S-endpoint-runner-CPU-a6000-r4-20261031`.
- Successful prepare receipt: `reports/cara_s_endpoint_runner_CPU_prepare_r4_20261031.json`. Original container `cara-S-endpoint-runner-CPU-a6000-r4-20261031-cpu`, launch PID 2592944, start 1793457169.54083; registration SHA `bad26b4df0aefe9b0dac64d633f5db186f458c46d533ffce0def052ff4e638d5`.
- Recover only with `scripts/cara_s_endpoint_runner_cpu_r4.py capture --source-revision 835032f6a7cf3118cbb3b33755a97706ec70a564 --output <fresh receipt>`; never repeat prepare on uncertainty.
- Bounds remain CPU26,1core,4GiB/no extra swap,network none,readonly root,GPU hidden;1200 seconds work plus60 exit margin.

## R3 retained original terminal failure

Source `c428502f6dbbc4690e55de828bcd7804e9be96f4`, original R3 stage/container, registration `b18619857105e8c26328a0efeee30975e0778219619993dc2c631f39cc6354ac`. Original `reports/cara_s_endpoint_runner_CPU_capture_r6_20261031.json` proves exited1/no OOM/Pid0, 22:26:00–22:28:53. Both first-flow complete collections returned; outer fixture then rejected the modified pre-initialization class/forward. R4 restores the outer fixture's original class/forward in its own finally block. Per-request production state restoration assertions remain intact; production sources are unchanged. Preserve the failed stage; no restart/replay.

## R2 transport attempt: original absence verified

Original source `cd21e31c71ba29c1a524bc921f598b065b416848`, stage `cara-S-endpoint-runner-CPU-a6000-r2-20261031`. The prepare and first capture timed out. Subsequent authenticated capture found missing registration; the separate read-only `reports/cara_s_endpoint_runner_CPU_absence_r1_20261031.json` verifies no stage, no exact container and no matching process. R3 was submitted only after that evidence. Preserve all R2 transport receipts; no R2 container was restarted.

## Retained R1 terminal failure

Original source `f114f55340dc03bdd01dbf2af0c37fada69485df`, stage `cara-S-endpoint-runner-CPU-a6000-r1-20261031`, launch `reports/cara_s_endpoint_runner_CPU_prepare_r1_20261031.json`, terminal `reports/cara_s_endpoint_runner_CPU_capture_r2_20261031.json`. Original container exited1/Pid0/no OOM. The first32 collection returned but the test compared restored methods against pre-initialization methods. R2 changes only that test to observe the registered WorldCache setup boundary; production runner source is unchanged. Do not replay R1.

## Accepted scope

Original R4 exited0/Pid0/no OOM at22:38:10; work318.838788 seconds. `reports/cara_s_endpoint_runner_CPU_capture_r9_20261031.json` and `reports/cara_s_endpoint_runner_CPU_accepted_r1_20261031.json` bind the complete114 paths,8 refusals,14 metadata controls. Independent12 acceptance controls and14 local binding controls passed. No further capture is needed merely to refresh documentation.


This validates the separate runner's metadata boundary and loaded-model collection using a tiny CPU model. Require original exited0/no OOM and complete proof:14 metadata controls, both flows/full32 and alias25 (114 complete tiny paths),8 pre-sampling refusal controls, storage/reset/model-parameter/precision checks, final restoration and read-only recovery without replay. The actual GPU context/model load/whole entry/once-dispatch and whole card remain unaccepted. The original budget policy is not bound.

The original R4 prepare and terminal capture were accepted by `scripts/accept_cara_s_endpoint_runner_cpu_r1.py`; canonical component readiness records this bounded acceptance. Inner test authority/freeze records are temporary metadata fixtures, never real execution authority. No original experiment output is read; GPU and central budget submissions are zero.

The original14GPUh successor remains separate:23:16 half check, next-day06:01 terminal check,06:45:04 hard cutoff. Do not change its source, configuration, handles or reservation for this CPU work.
