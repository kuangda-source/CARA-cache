"""GPU-free complete-asset diagnostics and optional failed-R1 numeric parity.

One state at a time; no inference, gain fitting for deployment, or new sample
claim. The old two-state assets can check engineering parity only.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
import torch
from analyze_cara_ig_b1_raw_r1 import moments, fit
from wcomr.innovation_gain_assets_r1 import load_state, sha
from wcomr.mid_coverage import tree_digest
from wcomr.scout_readout_v22 import actual_guided_error


def numeric_identity(value):
    return tree_digest(dict(teacher=value['teacher'], current=value['current'],
        anchors=value['anchors'],
        outputs={k:v['outputs'] for k,v in value['readouts'].items()},
        gain_outputs={k:v['outputs'] for k,v in value['innovation_gain']['outputs'].items()}))


def analyze(assets, original_assets=None):
    manifest = json.loads((assets / 'manifest.json').read_text())
    rows = manifest['states']
    prompts = sorted({r['prompt'] for r in rows})
    assert len(rows) == 12 and len(prompts) == 2
    assert {(r['prompt'], r['step']) for r in rows} == {
        (p,s) for p in prompts for s in (22,23,25,33,34,35)}
    originals = {}
    if original_assets is not None:
        old = json.loads((original_assets / 'manifest.json').read_text())
        for row in old['states']:
            payload = load_state(original_assets, row['artifact'])
            originals[(row['prompt'], row['step'])] = numeric_identity(payload)
            del payload
    result_rows = []
    for row in rows:
        value = load_state(assets, row['artifact'])
        assert all(value[k] for k in ('P0_actual_dense', 'P1_dense_head_RF_equal', 'P2_C_actual_parent_equal'))
        G,b,c = moments(value)
        key = (row['prompt'], row['step'])
        parity = dict(available=key in originals, independent_sample=False)
        if key in originals:
            parity['numeric_tensor_digest_equal'] = numeric_identity(value) == originals[key]
        actual = {k:actual_guided_error(v['outputs'],value['teacher'])
                  for k,v in value['innovation_gain']['outputs'].items()}
        result_rows.append(dict(prompt=row['prompt'],step=row['step'],token_shape=value['innovation_gain']['token_shape'],
            original_readout_summary=value['summary'], actual_corner_midpoint=actual,
            moments=row['moments'], G=G.tolist(), b=b.tolist(), c=c, raw_oracle=fit(G,b,c),
            original_failed_attempt_parity=parity,
            P1_dense_head_RF_exact=True, P2_C_paid_parent_exact=True))
        del value
    pooled = fit(np.mean([r['G'] for r in result_rows],axis=0),
                 np.mean([r['b'] for r in result_rows],axis=0),
                 float(np.mean([r['c'] for r in result_rows])))
    return dict(status='B1_COMPLETE_SAVED_CPU_DIAGNOSTICS_NOT_VIDEO',
        assets_manifest_sha256=sha(assets / 'manifest.json'),rows=result_rows,pooled_raw_oracle=pooled,
        original_parity_states=len(originals), all_available_original_parity_equal=all(
            r['original_failed_attempt_parity'].get('numeric_tensor_digest_equal',True) for r in result_rows),
        GPU_submissions=0,real_model_rerun=False,teacher_oracle_only=True,
        fitted_gain_detail_error_available=False,
        limitation='Fitted Phi replay saved MSE only; corner detail diagnostics do not establish fitted-gain detail quality')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--assets',type=Path,required=True)
    p.add_argument('--original-assets',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists() and os.environ.get('CUDA_VISIBLE_DEVICES','') == ''
    torch.set_num_threads(2)
    def forbid(*args,**kwargs):raise RuntimeError('Saved analysis forbids CUDA')
    torch.cuda._lazy_init=forbid
    start=time.monotonic();result=analyze(a.assets,a.original_assets)
    result.update(CPU_wall_seconds=time.monotonic()-start,cuda_initialized=torch.cuda.is_initialized())
    assert not result['cuda_initialized']
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','CPU_wall_seconds','original_parity_states')}))


if __name__=='__main__':main()
