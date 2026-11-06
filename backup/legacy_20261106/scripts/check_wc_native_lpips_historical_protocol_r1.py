"""Reconstruct old WC/Native pair identities without generating or altering data."""
import ast
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    sources = {}

    def read(name):
        p = ROOT / name
        sources[name] = hashlib.sha256(p.read_bytes()).hexdigest()
        return json.loads(gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_bytes())

    old = read('reports/w1d_cal8_r1_runner.json')
    native = read('reports/wc_w1_native_reference_runner_20261006.json')
    metric = read('reports/wc_w1_native_reference_full93_lpips_cpu_r1_20261006.json')
    fair = read('reports/wc_existing_fair_w1_lpips_cpu_r1_20261004.json')['result']
    raw = read('reports/wc_fair_cal_r1_runner_20261004.json.gz')
    protocol = read('manifests/f1_runtime_protocol.json')
    cases = {c['name']: c for c in old['cases']}
    setup_differences = {k: [old['setup'].get(k), native['setup'].get(k)]
                         for k in old['setup'].keys() | native['setup'].keys()
                         if old['setup'].get(k) != native['setup'].get(k)}
    assert set(setup_differences) == {'output_dir', 'worldcache_enabled'}
    requests = []
    for c in native['cases']:
        wc = cases[c['sample_name']]
        assert c['request'] == wc['sample']
        assert c['flags_before'] == wc['off']['flags_before']
        assert c['flags_after'] == wc['off']['flags_after']
        assert c['request']['seed'] == 0 and c['request']['input_path'] is None
        assert c['CFG_calls'] == 72 and c['solver_steps'] == 36
        assert c['block_counts']['full_calls'] == 72
        assert c['block_counts']['skipped_deep_calls'] == 0
        assert c['sampling']['timesteps'] == wc['off']['sampling']['timesteps'] == protocol['timesteps']
        requests.append(dict(scene=c['sample_name'], full_request_equal=True,
                             seed=0, timesteps_equal=True, backend_flags_equal=True, Native_full_calls=72))
    pairs = [p for p in metric['pairs'] if p['method'] == 'official_WC']
    assert len(pairs) == 7 and len(cases) == 8 and len(requests) == 5
    bridges = []
    for p in pairs:
        assert p['candidate']['sha256'] == cases[p['scene']]['off']['video_sha256']
        assert p['score']['frames'] == 93
        assert abs(sum(p['score']['frame_distances']) / 93 - p['score']['mean_LPIPS']) < 1e-12
        if p['scene'] not in {c['sample_name'] for c in native['cases']}:
            q = next(q for q in fair['pairs'] if q['sample'] == p['scene'] and q['variant'] == 'wc006')
            assert p['candidate']['sha256'] == q['candidate']['sha256']
            assert p['reference']['sha256'] == q['reference']['sha256']
            bridges.append(dict(scene=p['scene'], WC_byte_equal_across_batches=True,
                                reference_byte_equal=True))
    threshold_sweeps = []
    for req in raw['measurements']['requests']:
        rows = []
        for p in req['phases']:
            if p['workpoint']['name'] not in ('native35', 'wc004', 'wc006', 'wc008'):
                continue
            assert p['CFG_calls'] == 72 and p['sampling']['timesteps'] == protocol['timesteps']
            rows.append(dict(variant=p['workpoint']['name'], counts=p['block_counts']))
        threshold_sweeps.append(dict(scene=req['sample_name'], rows=rows))
    cache = ROOT / 'vendor/WorldCache/Models/Cosmos-Predict2.5/cosmos_predict2/_src/predict2/inference/worldcache_utils.py'
    assert hashlib.sha256(cache.read_bytes()).hexdigest() == old['cache_source_sha256']
    tree = ast.parse(cache.read_text())
    expr = next(n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'base_mult' for t in n.targets))
    ats_multiplier = eval(compile(ast.Expression(expr), '<pinned ATS expression>', 'eval'),
                          {'__builtins__': {}}, {'u': protocol['worldcache_horizon'] / 35.0})
    assert ats_multiplier == 5.0
    for name in [str(cache.relative_to(ROOT)),
                 'vendor/WorldCache/Models/Cosmos-Predict2.5/cosmos_predict2/_src/predict2/inference/video2world.py',
                 'vendor/WorldCache/Evaluation/EgoDex-Eval/evaluate.py',
                 'vendor/WorldCache/README.md',
                 'vendor/CosmosPredict25/cosmos_predict2/_src/imaginaire/utils/misc.py']:
        sources[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    result = dict(
        status='PASS_HISTORICAL_IDENTITIES_NOT_PAPER_EXACT_REPRODUCTION',
        input_sha256=sources, setup_differences=setup_differences,
        same_request_native_five=requests, fair_two_byte_equal_bridges=bridges,
        same_batch_threshold_sweeps=threshold_sweeps,
        original_denominator=8, accepted_WC_native_pairs=7,
        original_rejection='robot_054_VIDEO_REJECTED_NOT_REPLACED',
        original_Alex_WC006_scene_mean=sum(p['score']['mean_LPIPS'] for p in pairs)/7,
        sampler=protocol,
        actual_ATS_base_multiplier=ats_multiplier,
        noise_evidence='same explicit seed/shape; arch_invariant_rand uses private numpy RandomState(seed); original initial-noise tensor hashes not recovered',
        remaining_attribution_limits=[
            'No saved same-run forced-all-full WC wrapper versus Native parity control identified.',
            'Five Native references were generated later with shared eval; old WC runner does not persist the same explicit eval guard. Two FAIR WC006 bridges are byte equal, but do not prove five other scenes mode-equivalent.',
            'Paper Euler35 sigma grid and author per-sample generation artifacts are not fully pinned publicly.',
        ],
        paper_mismatches=dict(sampler='Euler35 versus UniPC/Karras36',
                              threshold='.08 versus .06 (.08 exists only in two-scene sweep)',
                              saliency_weight='.12 versus 1.0',
                              flow_scale='.5 paper/default versus 2.0 README/local; direct interpolate factor',
                              ATS='paper beta_d=4 versus pinned expression at horizon70 gives5',
                              metric='PIQ default VGG16 versus lpips AlexNet',
                              reference='EgoDex I2V ground truth versus CAL T2W Native'),
        standards_changed=False, GPU_submissions=0)
    out = ROOT / 'reports/wc_native_lpips_historical_protocol_audit_20261027.json'
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(result['status'])


if __name__ == '__main__':
    main()
