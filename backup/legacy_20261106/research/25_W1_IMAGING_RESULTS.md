# W1 automated imaging dimension result

2026-10-01: IMAGING_DIMENSION_COMPLETE_OVERALL_QUALITY_UNASSESSED.

| Scene | WC MUSIQ /100 | Scalar MUSIQ /100 | Candidate minus WC |
|---|---:|---:|---:|
| av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | 0.419033 | 0.403538 | -0.015494 |
| common_sense_6487f37f-ef57-49ca-afdc-d898922b5191 | 0.724492 | 0.746897 | +0.022404 |
| human_199 | 0.760046 | 0.767669 | +0.007623 |
| industry_084 | 0.631729 | 0.744464 | +0.112735 |
| misc_13398218_3840_2160_60fps | 0.671405 | 0.644889 | -0.026516 |
| physics_045 | 0.741518 | 0.724559 | -0.016959 |
| robot_054 | No unpaired score | VIDEO_REJECTED | NA, original8 denominator retained |
| av_51b45829-502e-4143-9c32-c026bd6ab191 | 0.526389 | 0.472376 | -0.054014 |

All original8 attempted,7 accepted pairs scored with all93 frames each,3 higher/4 lower. Equal-scene normalized mean delta +0.004254295 (raw MUSIQ +0.425429518). Industry delta +0.112735335 is large; other results mixed. No prespecified noninferiority bound, significance or independent confirmation. Robot rejection is retained and has no imputed score.

Checkpoint/pyiqa0.1.10/source/input/video hashes bound; longer512 preprocessing matches official torchvision Resize exactly on4 geometries, microbatch1, explicit model.eval/inference_mode. This is one controlled imaging dimension, not complete pinned benchmark/Joint reproduction. Semantic/physical quality, action completion and clean speed remain unassessed. Temporal RGB change and MUSIQ cannot establish motion collapse or better physics. No W2 expansion.

Supervisor2477084/timeout2477091/runner2477093 absent,exit0/no stop reason,lock available,GPU1 released24MiB/noapps;9 monitor samples,no observed foreign compute,peak586MiB. All source and15 accepted input videos rehashed;frame scores/means/paired differences/coverage independently recomputed. Wall 44.552937s = 0.012375816GPUh;settled3.612360697322422/4,remaining0.387639302677578h,no live GPU task.

[Runner](../reports/w1_imaging_r1_runner.json), [supervisor](../reports/w1_imaging_r1_supervisor.json), [audit](../reports/w1_imaging_r1_audit.json), [recomputed summary](../reports/w1_imaging_r1_summary.json), [protocol](../manifests/w1_imaging_protocol.json), [budget](../reports/budget.json).

Next resource preparation: pinned public Qwen3-VL2B revision89644892e4d85e24eaac8bacfd4f463576704203, approximately3.974GiB, CPU download to project-local hfhub, cap1200s. All42 original VQA questions already retrieved. Development judge only; not paper235B or independent confirmation. Actual load/video preparation and new bounded GPU admission required before scoring;no budget extension,paid API or human evaluation.
