"""Tiny36-step generated/control paths and ten-prompt analysis fixtures; no CUDA."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
os.environ.update(CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES='void')
import torch
from test_cara_f19_speed190_sampling_r1 import run
from postprocess import interval, summarize, write_results


if __name__ == '__main__':
    torch.set_num_threads(2)
    def forbidden(*a, **kw):
        raise RuntimeError('Local preparation forbids CUDA')
    torch.cuda._lazy_init = forbidden
    card = json.loads((HERE / 'manifest.json').read_text())
    checks = []
    for name, role in card['roles'].items():
        if role['kind'] != 'speed_policy':
            continue
        for flow in (False, True):
            result = run(role['policy'], flow, light=True)
            assert [h['actual'] for h in result['history']] == role['policy']['actions']
            assert not any(h['fallback_reason'] for h in result['history'])
            assert len(result['outputs']) == 36 and torch.isfinite(result['latent']).all()
            checks.append(dict(role=name, flow=flow, actual36_actions_match=True))
    assert len(card['matrix']) == 62 and card['counts']['LPIPS_pairs'] == 50
    assert card['roles']['NATIVE_K18']['schedule']['actual_updates'] == 19
    fixture = copy.deepcopy(card)
    fixture['bootstrap']['replicates'] = 1000
    assert interval([-.04, .02], fixture['bootstrap']) == [-.04, .02]
    values = dict(F17_A2_LIGHT_C=.25, R16C=.24, R18C=.22, R21C=.20, NATIVE_K18=.30)
    rows = [dict(slot=s, Alex=values[s['role']], T_DD=100., mask_matches=True)
            for s in card['matrix'] if s['section'] != 'warm' and s['role'] != 'NATIVE35']
    native_timings = {m: 200. for m in card['inputs_by_alias'].values()}
    summary = summarize(fixture, rows, native_timings)
    assert summary['primary_success'] and summary['monotonic_mean_LPIPS']
    assert abs(summary['contrasts'][0]['mean_delta'] + .03) < 1e-12
    for row in rows:
        if row['slot']['role'] == 'R18C':
            row['Alex'] = .255
    assert summarize(fixture, rows, native_timings)['verdict'] == 'SECONDARY_NONINFERIOR'
    for row in rows:
        if row['slot']['role'] == 'R18C':
            row['Alex'] = .27
    assert summarize(fixture, rows, native_timings)['verdict'] == 'INCONCLUSIVE'
    with tempfile.TemporaryDirectory(prefix='cara-confirm10-cpu-') as directory:
        output = Path(directory) / 'complete_analysis.json'
        write_results(output, summary)
        assert (output.parent / 'COMPLETE_RESULTS.md').read_text().index('Frozen prediction comparison') < (output.parent / 'COMPLETE_RESULTS.md').read_text().index('Verdict:')
    value = dict(passed=True, checks=checks, analysis_fixture_passed=True,
        CUDA_initialized=torch.cuda.is_initialized(), GPU_submissions=0, remote_calls=0,
        Native_k18_production_adapter_tested=False,
        scope='Local8tiny36 paths and synthetic10-prompt analysis only; k18 adapter and Linux production CPU acceptance remain pending')
    (HERE / 'cpu_check.json').write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(value))
