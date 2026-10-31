"""Rebuild accepted evidence locally and write the complete25 proposal and quote."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from wcomr.cara_fast_b36_analysis_r1 import analyze_complete
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_s_initialization_audit_r1 import audit
from wcomr.cara_s_uniform_endpoint_plan_r1 import build,quote
from accept_cara_s_initialization_numeric_cpu_r1 import accept as accept_numeric


def main():
    parser=argparse.ArgumentParser()
    for name in ('plan','quote','receipt'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    assert all(not p.exists() for p in (args.plan,args.quote,args.receipt))
    evidence={}
    def read(name):
        raw=(ROOT/name).read_bytes()
        evidence[name]=hashlib.sha256(raw).hexdigest()
        return json.loads(raw)
    analysis=read('reports/cara_fast_B36_complete_analysis_r1_20261029.json')
    values={}
    for key,binding in analysis['input_file_sha256'].items():
        values[key]=read(binding['path'])
        assert evidence[binding['path']]==binding['sha256']
    card=load_card(ROOT,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    rebuilt=analyze_complete(values['capture'],card,values['settlement'],values['manifest'],
        analysis['input_file_sha256']['manifest']['sha256'],values['score-capture'],values['accepted-scores'])
    assert all(analysis[k]==v for k,v in rebuilt.items())
    diagnostic=read('reports/cara_s_initialization_sensitivity_r1_20261031.json')
    contract=read('plans/cara_next_stage_20261028/mainline/r2/S_INITIALIZATION_SELECTOR_CPU_R1_20261031.json')
    risk={j:{int(k):v for k,v in rows.items()} for j,rows in contract['risk'].items()}
    rebuilt=audit(contract['profile'],contract['baselines'],risk,contract['original_choices'],contract['original_candidate_count'])
    assert all(diagnostic[k]==v for k,v in rebuilt.items())
    numeric=read('reports/cara_s_initialization_numeric_CPU_accepted_r3_20261031.json')
    captured=read(numeric['capture_ref']);launched=read(numeric['launch_ref'])
    assert evidence[numeric['capture_ref']]==numeric['capture_sha256']
    assert evidence[numeric['launch_ref']]==numeric['launch_sha256']
    rebuilt=accept_numeric(captured,launched)
    assert all(numeric[k]==v for k,v in rebuilt.items() if k!='observed_unix')
    plan=build(card,diagnostic,values['accepted-scores'],analysis,numeric)
    cost=quote(plan,analysis)
    sources={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
        'scripts/prepare_cara_s_uniform_endpoint_plan_r1.py','src/wcomr/cara_s_uniform_endpoint_plan_r1.py')}
    report=dict(status='COMPLETE25_ENDPOINT_SCOPE_AND_REUSE_LOCAL_REVALIDATED_NOT_DISPATCH',
        observed_unix=time.time(),plan_ref=str(args.plan),quote_ref=str(args.quote),
        original_complete_B36_rebuilt=True,original_initialization_diagnostic_rebuilt=True,
        original_numerical_CPU_acceptance_rebuilt=True,evidence_sha256=evidence,source_sha256=sources,
        physical_paths=25,reused_score_rows=12,new_score_pairs=8,decoded_identity_controls=9,
        remote_assets_read=False,actual_asset_availability_currently_verified=False,
        source_selection_used_new_endpoint_results=False,whole25_GPU_entry_CPU_accepted=False,
        new_GPU_authorization_requested=False,GPU_submissions=0,ledger_written=False)
    for path,data in ((args.plan,plan),(args.quote,cost)):
        with path.open('x') as f:json.dump(data,f,indent=2,allow_nan=False);f.write('\n')
        report[path.stem+'_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    with args.receipt.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(dict(physical_paths=25,forecast_GPUh=cost['forecast_GPUh'],proposed_hard_GPUh=cost['proposed_hard_GPUh'])))


if __name__=='__main__':
    main()
