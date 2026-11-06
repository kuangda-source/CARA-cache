"""Independent saved-receipt acceptance; no SSH, replay or result interpretation."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:raise ValueError(message)


def worker_derivation():
    original=ROOT/'plans/cara_next_stage_20261028/mainline/CPU_WORKER_R1_BEFORE_EXIT_FIX.py.txt'
    old=ast.parse(original.read_text());new=ast.parse((ROOT/'scripts/check_cara_fast_cpu_r1.py').read_text())
    helpers=[n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='closing_guard']
    require(len(helpers)==1,'Exactly one lifecycle-only helper required')
    new.body.remove(helpers[0]);main=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    calls=[n for n in main.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
           and isinstance(n.value.func,ast.Name) and n.value.func.id=='closing_guard']
    require(len(calls)==1,'Exactly one lifecycle-only call required');main.body.remove(calls[0])
    require(ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False),'Worker changed outside lifecycle guard')
    return hashlib.sha256(original.read_bytes()).hexdigest()


def validate(capture, host, scope, component_only=False):
    p=capture['CPU_proof'];reg=capture['registration'];state=capture['container_state'];cfg=capture['host_config']
    require(state['Status']=='exited' and not state['OOMKilled'], 'Released CPU container required')
    if not component_only:
        require(state['ExitCode']==0,'Successful CPU container exit required; proof alone is insufficient')
    require(cfg['NanoCpus']==10**9 and cfg['Memory']==4*2**30 and not cfg['DeviceRequests']
            and cfg['NetworkMode']=='none' and cfg['ReadonlyRootfs'], 'Exact CPU-only container boundary required')
    require(capture['payload_intact'] and capture['runtime_intact'], 'Frozen runtime and stage payload required')
    raw=json.dumps(p,indent=2,allow_nan=False)+'\n'
    require(hashlib.sha256(raw.encode()).hexdigest()==capture['CPU_proof_sha256'], 'Proof byte SHA differs')
    require(p['host']==reg['host']==host and p['scope_sha256']==scope, 'Host/scope differs')
    require(p['registration_sha256']==capture['registration_sha256']==capture['launch']['registration_sha256'], 'Registration differs')
    require(p['payload_sha256']==reg['payload_sha256'] and p['runtime_source_sha256']==reg['runtime_source_sha256'], 'Payload/runtime proof binding differs')
    require(p['status']=='FAST_AFFECTED_PRODUCTION_AND_FIDELITY_CPU_PASS_NOT_GPU'
            and not p['CUDA_initialized'] and not p['Cosmos_model_weights_loaded']
            and p['GPU_submissions']==0 and not p['ledger_written'] and not p['whole_GPU_card_accepted'], 'CPU-only proof required')
    checks=p['numeric']['checks']
    require(len(checks)==2 and {r['flow'] for r in checks}=={False,True}, 'Both flow paths required')
    for row in checks:
        require(row['registered_paths']==60 and row['OFF_ON_pairs']==12 and row['native_allD_exact']
                and row['F18_CPU_only']==['F18_C','F18_A1'] and len(row['faults'])==12
                and row['no_replay'] and row['missing_freeze_refused'] and row['preparation_GPU_refused'], 'Affected production denominator differs')
    f=p['fidelity']
    require(f['status']=='SYNTHETIC_FIDELITY_AND_REAL_ALEX_CPU_CONTROLS_PASS'
            and f['checkpoint_sha256']=='7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
            and f['linear_sha256']=='df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'
            and f['package_versions']['piq']=='0.8.0' and f['old_videos_scored']==0
            and not f['scientific_quality_result'], 'Bound real-Alex synthetic scorer proof required')
    require(all(f[k] for k in ('identical_inf_and_zero','video_MSE_before_dB','constant_error_temporal_zero',
                               'SSIM_explicit_PIQ_parity','zero_gradient_denominator_preserved','decoded_all_frame_roundtrip')),
            'Fidelity controls incomplete')
    critical=[n for n in reg['payload_sha256'] if n.startswith(('src/wcomr/cara_fast_',
              'tests/test_cara_fast_', 'tests/check_cara_fast_', 'scripts/check_cara_fast_',
              'plans/cara_next_stage_20261028/mainline/'))]
    for path in critical:
        expected=worker_derivation() if path=='scripts/check_cara_fast_cpu_r1.py' else hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
        require(expected==reg['payload_sha256'][path], 'Current affected payload differs: '+path)
    return dict(receipt_scope='Affected production tiny CPU and synthetic fidelity only',
                tiny_registered_paths=120,OFF_ON_pairs=24,F18_extra_CPU_paths=4,declared_fault_cases=24,
                own_CPU_process_seconds=p['CPU_process_seconds'],worker_wall_seconds=p['ended_unix']-p['started_unix'],
                full_resolution_synthetic_frame_seconds=f['full_resolution_frame_wall_seconds'],
                validation_mode='COMPONENT_ONLY_NOT_WHOLE_CPU_ACCEPTANCE' if component_only else 'CLEAN_ORIGINAL_COMPLETE',
                original_container_exit_code=state['ExitCode'],
                whole_CPU_accepted=not component_only,
                critical_payload_sha256={n:reg['payload_sha256'][n] for n in critical})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--four',type=Path,required=True)
    parser.add_argument('--two',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--four-shutdown',type=Path)
    args=parser.parse_args();require(not args.output.exists(),'Output exists')
    scope=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json').read_text())['scope_sha256']
    data={};summaries={}
    repair=json.loads(args.four_shutdown.read_text()) if args.four_shutdown else None
    for host,path in [('four_card',args.four),('two_card',args.two)]:
        data[host]=json.loads(path.read_text())
        component_only=data[host]['container_state']['ExitCode']!=0
        summaries[host]=dict(validate(data[host],host,scope,component_only=component_only),receipt=str(path.relative_to(ROOT)),
            receipt_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    if repair:
        summaries['four_card']['exit_repair_receipt']=str(args.four_shutdown.relative_to(ROOT))
        summaries['four_card']['exit_repair_receipt_sha256']=hashlib.sha256(args.four_shutdown.read_bytes()).hexdigest()
        summaries['four_card']['exit_repair_exit_code']=repair['container_state']['ExitCode']
    require(summaries['four_card']['critical_payload_sha256']==summaries['two_card']['critical_payload_sha256'], 'Scientific Fast payload differs across hosts')
    mutations=[lambda x:x['container_state'].update(ExitCode=1),lambda x:x['host_config'].update(DeviceRequests=[{'Count':1}]),
               lambda x:x['CPU_proof'].update(CUDA_initialized=True),lambda x:x['CPU_proof']['numeric']['checks'][0].update(registered_paths=59),
               lambda x:x['CPU_proof'].update(scope_sha256='wrong'),lambda x:x.update(payload_intact=False)]
    for mutate in mutations:
        bad=copy.deepcopy(data['two_card']);mutate(bad)
        if bad['CPU_proof']!=data['two_card']['CPU_proof']:
            bad['CPU_proof_sha256']=hashlib.sha256((json.dumps(bad['CPU_proof'],indent=2)+'\n').encode()).hexdigest()
        try:validate(bad,'two_card',scope)
        except ValueError:pass
        else:raise ValueError('Corrupt receipt accepted')
    complete=all(s['whole_CPU_accepted'] for s in summaries.values())
    # A completed proof never clears a failed container termination. The caller
    # receives an explicit partial review, not a relaxed success condition.
    if not complete:
        try:validate(data['four_card'],'four_card',scope)
        except ValueError:pass
        else:raise ValueError('Failed lifecycle unexpectedly cleared whole acceptance')
    result=dict(status='DUAL_HOST_AFFECTED_CPU_ACCEPTED_NOT_GPU_OR_SCIENCE' if complete else 'COMPONENTS_REVIEWED_ADA_WHOLE_CPU_ACCEPTANCE_BLOCKED',scope_sha256=scope,hosts=summaries,
                acceptor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                independent_rejection_controls=len(mutations),GPU_submissions=0,new_GPUh=0,new_reserved_GPUh=0,
                Cosmos_model_loaded=False,new_videos_generated=0,old_videos_rescored=0,
                complete_GPU_adapter_ready=False,dual_host_whole_CPU_accepted=complete,full_CPU_batch_scoring_run=False,
                original_Ada_failures_retained=True,failed_lifecycle_does_not_count_as_pass=True,
                inherited_fixture_caption='Generic base fixture limit text is inherited; actual new sparse-route coverage is the explicit per-flow checks and their bound source, not a model/video claim',
                CPU_cost_boundary='Worker own process time measured; children, I/O wait, transport and local editing not fully process-metered')
    with args.output.open('x') as handle:json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps(dict(status=result['status'],hosts={h:{k:v for k,v in s.items() if k!='critical_payload_sha256'} for h,s in summaries.items()})))


if __name__=='__main__':main()
