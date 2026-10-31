# Endpoint runner CPU original-handle handoff

This validates the separately approved runner's metadata boundary and loaded-model collection using a tiny CPU model. It is not a production GPU dispatch or complete card acceptance.

- Source: `f114f55340dc03bdd01dbf2af0c37fada69485df`.
- Host: two_card only.
- Original stage: `/data20t/gaokuangda/worldcache_workspace/.sync/cara-S-endpoint-runner-CPU-a6000-r1-20261031`.
- Container: `cara-S-endpoint-runner-CPU-a6000-r1-20261031-cpu`.
- Registration SHA256: `f563a53da317b2f9900a87efcd6101ad79ed9ac48875fcf8ecef8da38b60ea1d`.
- Original launch: `reports/cara_s_endpoint_runner_CPU_prepare_r1_20261031.json`.
- Saved live observation: `reports/cara_s_endpoint_runner_CPU_capture_r1_20261031.json`; historical snapshot only.
- Bound: CPU26,1core,4GiB/no extra swap,network none,readonly root,GPU hidden;1200 seconds work plus60 exit margin.

Recover only the original stage with `scripts/cara_s_endpoint_runner_cpu_r1.py capture --source-revision f114f55340dc03bdd01dbf2af0c37fada69485df --output <fresh receipt>`. UNKNOWN means recover, never prepare again or restart this container.

Require exited0/no OOM and complete proof:14 metadata controls, both flows/full32 and alias25 (114 complete tiny paths),8 pre-sampling refusal controls, request storage/reset/model-parameter/precision checks, final restoration and read-only recovery without replay. The real GPU context/model load/entry/once-dispatch and whole card remain unaccepted. The original budget policy is not bound.

Only then apply `scripts/accept_cara_s_endpoint_runner_cpu_r1.py` to the original launch and terminal capture, run independent acceptance controls, and update canonical component readiness. No experiment output is read by this CPU stage; GPU and central budget submissions are zero.

The original14GPUh successor remains separate and unchanged:23:16 half check, next-day06:01 terminal check,06:45:04 hard cutoff. Never change its source, controls, handles or reservation to test this new runner.
