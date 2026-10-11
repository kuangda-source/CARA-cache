"""Read-only E5 source consumers and actual accepted head-opportunity census."""
import ast
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    sha=lambda raw:hashlib.sha256(raw).hexdigest()
    capture=json.loads((root/'reports/wc_ra_plus_a_r1_terminal_20261010_capture_and_independent_audit.json').read_text())
    art=capture['files']['runner'];z=(root/art['local_path']).read_bytes();raw=gzip.decompress(z)
    assert sha(z)==art['compressed_sha256'] and len(raw)==art['bytes'] and sha(raw)==art['sha256']
    runner=json.loads(raw);assert runner['comparison']['planned_paths']==32 and capture['GPU_exit_code']==capture['CPU_exit_code']==0
    census=[];totals={}
    for request in runner['comparison']['batch']['requests']:
        for row in request['paths']:
            readout=row.get('A_readout')
            if readout is None:continue
            assert row['status']=='COMPLETE_PATH' and len(readout['history'])==36
            histories=readout['history'];eligible=[]
            for h in histories:
                assert h['extra_heads']==sum(s in ('scalar','BETA1') for s in h['branch_status'])
                if h['action']=='CC' and h['shared_alpha']==1 and h['extra_heads']:
                    eligible.append({'step':h['step'],'candidate_heads':h['extra_heads'],'branch_status':h['branch_status']})
            item={'sample':request['sample_name'],'method':row['method'],'existing_original_heads':72,
                  'existing_extra_candidate_heads':readout['extra_candidate_heads'],
                  'alpha1_available_candidate_branch_opportunities':sum(h['candidate_heads'] for h in eligible),'eligible_steps':eligible}
            assert item['existing_extra_candidate_heads']==sum(h['extra_heads'] for h in histories)
            census.append(item);v=totals.setdefault(row['method'],{'paths':0,'original_heads':0,'extra_candidate_heads':0,'possible_original_head_elisions_before_state_contract':0})
            for key,value in (('paths',1),('original_heads',72),('extra_candidate_heads',item['existing_extra_candidate_heads']),('possible_original_head_elisions_before_state_contract',item['alpha1_available_candidate_branch_opportunities'])):v[key]+=value
    assert len(census)==16 and len(totals)==4 and all(v['paths']==4 for v in totals.values())
    leaves=[];bindings={}
    for path,cls in (('src/wcomr/partial_mlp_deployment.py','PartialDeployment'),('src/wcomr/cfg_guided_w1_deployment.py','GuidedW1Readout')):
        text=(root/path).read_text();tree=ast.parse(text);c=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
        f=next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='output')
        loads=[n.lineno for n in ast.walk(f) if isinstance(n,ast.Name) and n.id=='head' and isinstance(n.ctx,ast.Load)]
        assert not loads;leaves.append({'file':path,'class':cls,'function':'output','line':f.lineno,'head_value_loads':loads,'output_seen_flag_still_required':True});bindings[path]=sha((root/path).read_bytes())
    for path in ('src/wcomr/partial_mlp_guided_readout.py','src/wcomr/cfg_guided_w1_outputs.py','src/wcomr/cfg_guided_w1_forward.py','src/wcomr/source_aware_partial_deployment.py'):
        bindings[path]=sha((root/path).read_bytes())
    physical=json.loads((root/'manifests/wc_e4c_matched_source_age_full_cpu_r3_20261011.json').read_text())['runtime_source_sha256']
    native_names=['cosmos_predict2/_src/predict2/inference/worldcache_utils.py','cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py']
    packet={n:physical[n] for n in native_names}
    code='P='+repr(packet)+'\n'+r'''import ast,hashlib,json,pathlib,subprocess
r=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr/runtime');texts={}
for n,h in P.items():
 raw=(r/n).read_bytes();assert hashlib.sha256(raw).hexdigest()==h;texts[n]=raw.decode()
w=next(v for k,v in texts.items() if k.endswith('worldcache_utils.py'));tree=ast.parse(w)
f=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='worldcache_mini_train_dit_forward')
refs=[{'line':n.lineno,'code':ast.unparse(n),'context':type(n.ctx).__name__} for n in ast.walk(f) if isinstance(n,ast.Attribute) and n.attr=='previous_output']
assert len(refs)==4
scan=subprocess.run(['rg','-n','previous_output',str(r/'cosmos_predict2/_src/predict2')],text=True,capture_output=True,check=True)
d=next(v for k,v in texts.items() if k.endswith('minimal_v4_dit.py'));ct=ast.parse(d);c=next(n for n in ct.body if isinstance(n,ast.ClassDef) and n.name=='FinalLayer');forward=next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
mutations=[ast.unparse(n) for n in ast.walk(forward) if isinstance(n,ast.Attribute) and isinstance(n.ctx,ast.Store) and isinstance(n.value,ast.Name) and n.value.id=='self']
assert not mutations
print(json.dumps({'source_sha256':P,'WC_previous_output_references':refs,'all_primary_runtime_previous_output_references':scan.stdout.splitlines(),
 'FinalLayer_forward_self_attribute_assignments':mutations,'no_dynamic_module_state_or_hook_or_RNG_claim_from_AST_alone':True}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
                         '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-3000:])
    result={'status':'E5_EARLY_HEAD_SOURCE_AND_EXISTING_OPERATION_CENSUS_NOT_IMPLEMENTATION_OR_SPEED_RESULT',
        'accepted_full32_receipt_sha256':art['sha256'],'actual_readout_paths':16,'actual_readout_updates':576,
        'per_existing_path':census,'per_method_totals':totals,'leaf_output_observers':leaves,'bound_local_source_sha256':bindings,
        'native_source_consumers':json.loads(call.stdout),
        'original_actual_output_still_finite_checked':True,'previous_output_still_in_full_physical_state_snapshots':True,
        'state_contract_must_be_explicit_before_elision':True,'old_E2_E3_E4c_versions_unchanged':True,
        'actual_elided_heads':0,'actual_measured_speed_gain':None,'GPU_submissions':0,'ledger_written':False}
    target=root/'reports/wc_early_head_consumer_source_audit_r1_20261011.json';assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'per_method_totals':totals}));return 0


if __name__=='__main__':raise SystemExit(main())
