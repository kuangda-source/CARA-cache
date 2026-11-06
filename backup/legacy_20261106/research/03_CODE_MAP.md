# WorldCache code map

Pinned source: manifests/upstream.json. Main package root is Models/Cosmos-Predict2.5.

- examples/inference.py: CLI and per-sample inference.
- cosmos_predict2/config.py: setup, cache knobs and sample configuration.
- cosmos_predict2/_src/predict2/inference/video2world.py: enables cache and resets state for each sample; CFG uses two separate branch slots.
- worldcache_utils.py: shallow probe and skip decision, OSI approximation, optional spatial warp, full-anchor updates, final layer/unpatchify.

Actual tensors: shallow probe p = test_x − ori_x; cached full residual r = transformer_output − ori_x (includes shallow computation). The two tensors have matching layout. Our beta estimates historical Δr from Δp; it is not the official gamma projecting current shallow displacement onto past shallow displacement.

Insertion is before official warp on a skip. True full anchor updates occur only on a full branch. Historical full steps need not be consecutive. Additional cloning/reductions may add memory and synchronization costs; these must be measured, not assumed free.

The version-checked hook supports scalar and shrink modes. Current tests are synthetic and do not validate expert switches or full Cosmos end-to-end latency. Automatic request counter/model identity plus separate CFG slots reset state; future custom conditioning paths must provide explicit reset/context identity.
