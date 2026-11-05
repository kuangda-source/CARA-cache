"""Tiny full36 sampler paths and the frozen-control analysis; no GPU."""
import json
import os
from pathlib import Path
import sys
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void')
import torch
from test_cara_f19_speed190_sampling_r1 import run
from postprocess import summarize,write_results

if __name__=='__main__':
    torch.set_num_threads(2)
    def forbidden(*args,**kwargs):raise RuntimeError('CPU preparation forbids CUDA')
    torch.cuda._lazy_init=forbidden
    card=json.loads((HERE/'manifest.json').read_text());checks=[]
    for name,role in card['roles'].items():
        for flow in (False,True):
            result=run(role['policy'],flow,light=True)
            assert [r['actual'] for r in result['history']]==role['policy']['actions']
            assert not any(r['fallback_reason'] for r in result['history'])
            assert torch.isfinite(result['latent']).all() and len(result['outputs'])==36
            checks.append(dict(role=name,flow=flow,actual36_actions_match=True,finite=True))
    rows=[dict(slot=s,Alex=.25,T_DD=card['predicted_T_DD'][s['role']],mask_matches=True)
        for s in card['matrix'] if s['section']!='warm']
    summary=summarize(card,rows)
    assert summary['reused_control_count']==8 and len(summary['contrasts'])==13
    expected=sum(.25-r['Alex'] for r in card['reused_controls'] if r['slot']['role']=='F17_A2_LIGHT_C')/4
    assert abs(summary['contrasts'][0]['mean_delta']-expected)<1e-12
    with tempfile.TemporaryDirectory(prefix='cara-avslc-CPU-report-') as directory:
        path=Path(directory);write_results(path/'complete_analysis.json',summary)
        assert all((path/name).is_file() for name in ('complete_analysis.json','outcome_summary.json','COMPLETE_RESULTS.md'))
    value=dict(passed=True,checks=checks,merged_controls=8,contrasts=13,analysis_fixture_passed=True,
        CUDA_initialized=torch.cuda.is_initialized(),model_weights_loaded=False,GPU_submissions=0,remote_calls=0,
        scope='Local tiny full36 paths and synthetic analysis only; not Linux production admission')
    (HERE/'cpu_check.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(dict(passed=True,complete36_paths=len(checks),CUDA_initialized=value['CUDA_initialized'])))
