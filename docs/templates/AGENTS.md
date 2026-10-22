# CARA-Cache repository rules

## Read and orient

Read [EXPERIMENT_REPORT.md](repo:EXPERIMENT_REPORT.md), [current state](repo:research/02_CURRENT_STATE.md), [next actions](repo:research/09_NEXT_ACTIONS.md), and [handoff](repo:memory/handoffs/LATEST.md). Use the source receipts linked by current state; generated documentation is a timestamped snapshot, not a runtime lock. Historical instructions and completed authorizations remain in [the archive](repo:docs/archive/README.md).

## Execution and evidence

- This repository is WorldCache/CARA-only. OMR work belongs to the separate `omr-experiments` repository. Keep legacy package/project/stage identifiers for compatibility.
- Use the authorized four-card private entry. The user retired the two-card execution route. Do not revive it or touch other users' processes, drivers or jobs. Connection secrets stay outside Git.
- Preserve each registered card's exact inputs, methods, repeats, denominators, scope and whole-cost budget. A completed authorization is not permission to replay a card. Current whole1624 asset authorization is 12 GPUh; it does not authorize a different card.
- Track an active run by its launch receipt, source hash, stage, PID/start ticks, container and GPU UUID. Do not change its source/config. UNKNOWN requires recovering the original handle before any dispatch. Keep original failures and actual costs.
- Before any new dispatch, verify actual production CPU/source/assets/import/runtime, fresh UUID/VRAM/compute apps, owner lock, ledger, full quote, disk and memory. One expensive owned job at a time; Git synchronization is not a distributed execution lock. Long runs require actual-start-based halfway and terminal checks, without duplicate submissions or checks.
- Keep pinned upstream unmodified. Identify and version runtime adaptations separately; share them between comparison paths where appropriate.
- True anchors are full computations in the same request, CFG branch and model/expert. Shadow truth never updates deployed state. Reset on request or model/condition changes; fail safe on nonfinite values or insufficient anchors.
- CPU tests demonstrate implementation, not video quality or speed. Separate local MSE, endpoint fidelity, automatic quality, clean latency and billed GPUh. Preserve refusal/failure denominators and matched cohorts. Do not count reused artifacts as new independent samples.
- Keep CAL/SELECT/DEV/TEST roles and frozen selection rules. Do not fit thresholds to BANK24 DEV or tune from partial running outputs. Follow the registered PG-P1→P2→P3→P4 dependencies and each card's scope/cost/admission.

## Documentation and synchronization

- `docs/project_status.json` owns the current evidence snapshot and receipt pointers. `paper/experiment_master_table.json` owns the scientific rows and their evidence references. `paper/internal_to_paper_mapping.json` owns names and versioned identities. Update these inputs and the relevant `docs/templates/` file, then run `python3 docs/tools/render_repository_docs.py` and `--check`.
- Do not prepend daily logs to generated README/current state/overview/table/handoff/AGENTS. Add a numbered research note and a uniquely named machine receipt for a meaningful event, then regenerate all navigation together. Retain old records, aliases, complete evidence references and archived hashes.
- Commit and synchronize meaningful code/config/result changes to private `kuangda-source/CARA-cache` before reporting completion. Keep code, plans, tests, manifests, summaries and small receipts in Git. Never commit credentials, private transport logs, weights, bulk tensors or videos; record their paths/hashes instead.
- Preserve unrelated changes and remote parent history; no force push. When reconciling Git, choose evidence by actual receipt identity/time rather than combining incompatible statuses. A connector atomic commit is acceptable if local Git access fails; verify the resulting commit/tree.

For routine documentation work, use saved receipts and local checks; do not poll, restart or re-stage a running experiment merely to refresh prose.
