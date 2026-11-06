"""Full twelve-path continuous-clock H1 scalar feature replay, 0 model/GPU."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.w3_actual_clock_replay_r1 import replay,validate_clock

INPUT='reports/wc_p_w3_e0_h1_decisions_20261014.json'
CLOCK='reports/wc_w3_actual_schedule_native_CPU_replay_20261015.json'
CONFIG='configs/wc_h1_cost_curve_full60_production_r1_20261013.json'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Do not overwrite a previous clock replay')
    inputs=json.loads((ROOT/INPUT).read_text());receipt=json.loads((ROOT/CLOCK).read_text());clock=receipt['result']
    if receipt['transport_exit_code'] or clock['audit_script_sha256']!=sha(ROOT/'scripts/audit_wc_w3_actual_schedule_cpu_r1.py'):
        raise ValueError('Actual native execution/source receipt differs')
    validate_clock(clock)
    for ref,digest in inputs['sources'].items():
        if sha(ROOT/ref)!=digest:raise ValueError('Historical source receipt changed')
    config=json.loads((ROOT/CONFIG).read_text());requests=config['requests']
    if len(requests)!=4 or any(r['seed']!=0 or r['num_steps']!=35 for r in requests):raise ValueError('Original four seed0 inputs changed')
    scenes={r['name'] for r in requests};paths=inputs['paths']
    if len(paths)!=12 or {p['scene'] for p in paths}!=scenes:raise ValueError('Complete four scenes by three lambdas required')
    source_sha=sha(ROOT/INPUT);original=copy.deepcopy(inputs);output=[];refused=[]
    for path in paths:
        result=replay(path,clock,input_sha256=source_sha)
        # Change only future observations and after-the-fact H1 score estimates.
        future=copy.deepcopy(path)
        for row in future['rows'][29:]:
            if row['paid_packets']:
                for packet in row['paid_packets']:packet[2]+=1000.
        later=replay(future,clock,input_sha256=source_sha)
        if result['rows'][:29]!=later['rows'][:29]:raise ValueError('Future drift changed prior features')
        proxy=copy.deepcopy(path)
        for row in proxy['rows']:
            if row['scores'] is not None:
                for cell in row['scores'].values():cell['absolute_current_MSE']=1e20;cell['score']=1e20
        if replay(proxy,clock,input_sha256=source_sha)!=result:raise ValueError('H1 score estimate leaked as teacher input')
        bad=copy.deepcopy(path);bad['rows'][11]['scheduler_timestep']+=1
        try:replay(bad,clock,input_sha256=source_sha)
        except ValueError:refused.append(path['id']+':changed_timestep')
        else:raise ValueError('Different native clock accepted')
        output.append(result)
    if inputs!=original:raise ValueError('Original E0 data mutated')
    total=sum(len(p['rows']) for p in output)
    if total!=432 or len(refused)!=12:raise ValueError('Full432 controls incomplete')
    result={'status':'REAL_H1_FULL12_PATHS432_NATIVE_CONTINUOUS_CLOCK_CAUSAL_PREFIXES_ACCEPTED_NO_LABEL_FIT',
        'input_sha256':source_sha,'native_clock_receipt_ref':CLOCK,'native_clock_receipt_sha256':sha(ROOT/CLOCK),
        'config_ref':CONFIG,'config_sha256':sha(ROOT/CONFIG),'paths':output,'full_paths':12,'prefix_rows':total,
        'all36_native_timesteps_match_each_path':True,'future_drift_invariance_paths':12,
        'H1_score_estimate_excluded_from_inputs_paths':12,'mismatched_clock_refusals':refused,
        'GPU_submissions':0,'model_forwards':0,'new_teacher_calls':0,'predictor_fitted':False,
        'source_or_action_changed':False,'same_state_real_labels_available':False,
        'actual_continuous_sigma_replayed':True,'original_per_run_sigma_captured':False,
        'budget_sha256_unchanged_in_native_audit':clock['budget_after_sha256'],
        'next_missing':'Real same-H1 CAD teacher labels; reserved EXPL_DEV and complete production/card cost'}
    with a.output.open('xb') as f:f.write(gzip.compress(json.dumps(result,allow_nan=False).encode(),mtime=0))
    print(json.dumps({k:v for k,v in result.items() if k not in ('paths','mismatched_clock_refusals')}))


if __name__=='__main__':main()
