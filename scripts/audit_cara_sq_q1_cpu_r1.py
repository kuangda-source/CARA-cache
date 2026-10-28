"""Accept only the Q1 CPU scopes actually exercised, preserving R1 failures."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def wall(state):
    def parse(value):
        return datetime.fromisoformat(re.sub(r'(\.\d{6})\d+(?=Z$)',r'\1',value).replace('Z','+00:00'))
    return (parse(state['FinishedAt'])-parse(state['StartedAt'])).total_seconds()


def audit(captures, failures, asset_receipt):
    expected_weights=next(row for row in asset_receipt['files'] if row['sha256']=='565bbb2c9645737327983f4461e4d32627bba465b0a8dc26447edea144e1ff47')
    hosts={};CPU_seconds=0.;allocated=0.;failed_bound=0.
    for host,c in captures.items():
        state=c['container_state'];h=c['host_config'];r=c['result']
        assert state['Status']=='exited' and state['ExitCode']==0 and not state['OOMKilled'] and not state['Error']
        assert c['source_hashes_equal'] and c['runtime_hashes_equal']
        assert not h['DeviceRequests'] and h['NetworkMode']=='none' and h['ReadonlyRootfs']
        assert h['NanoCpus']==2*10**9 and h['Memory']==h['MemorySwap']==8*2**30 and h['CpusetCpus']=='4,5'
        assert r['fixture_checks']['tests']==10 and r['fixture_checks']['failures']==r['fixture_checks']['errors']==0
        assert not r['fixture_checks']['real_model'] and not r['actual_model_C_replayed'] and not r['CUDA_initialized']
        assert r['GPU_submissions']==r['ledger_writes']==0
        assert not r['actual_condition_module_imported']
        assert r['condition_definition_mode']=='EXISTING_PINNED_WHOLE_CLASS_CPU_COMPILATION'
        assert r['condition_schema_import_error']['message']=='flash_attn_2 not available. run pip install flash_attn'
        assert r['condition_class_AST_sha256']=='59e3528fca84aa6c0f3e33114cacf85f5f358ab28300c397645ef976e868b696'
        if host=='two_card':
            assert {(x['prompt'],x['step']) for x in r['actual_saved_conditions']}=={(p,t) for p in (
                'av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632','human_199') for t in (22,23,25,33,34,35)}
            assert all(x['exact_types_and_tensor_bindings'] for x in r['actual_saved_conditions'])
            assert len(r['verified_B1_files'])==32
        else:
            assert r['actual_saved_conditions']==[]
        head=r['actual_head_metadata']
        assert head['checkpoint_sha256']==expected_weights['sha256'] and head['checkpoint_bytes']==expected_weights['bytes']
        assert not head['full_model_constructed'] and not head['head_executed']
        assert {k:tuple(v['shape']) for k,v in head['tensors'].items()}=={
            'net.final_layer.linear.weight':(64,2048),
            'net.final_layer.adaln_modulation.1.weight':(256,2048),
            'net.final_layer.adaln_modulation.2.weight':(4096,256)}
        assert 0<r['wall_seconds']<1800 and 0<r['CPU_seconds']<=2*r['wall_seconds']+10
        assert r['peak_RSS_KiB']<8*2**20 and 0<wall(state)<1810
        CPU_seconds+=r['CPU_seconds'];allocated+=2*wall(state)/3600
        hosts[host]=dict(source_revision=c['launch']['source_revision'],container=c['launch']['container'],
            result_sha256=c['result_sha256'],container_wall_seconds=wall(state),worker_wall_seconds=r['wall_seconds'],
            actual_process_CPU_seconds=r['CPU_seconds'],worker_peak_RSS_GiB=r['peak_RSS_KiB']/2**20,
            pinned_condition_definition=True,actual_runtime_condition_import=False,
            actual_B1_condition_states=len(r['actual_saved_conditions']),head_metadata=head,
            BF16_CPU_grid_sample_supported=r['BF16_CPU_grid_sample_supported'],actual_C_replay=False)
    assert hosts['two_card']['head_metadata']['tensors']==hosts['four_card']['head_metadata']['tensors']
    for host,c in failures.items():
        state=c['container_state']
        assert state['Status']=='exited' and state['ExitCode']==1 and not state['OOMKilled']
        assert 'AssertionError: flash_attn_2 not available.' in c['log_tail']
        assert not c['host_config']['DeviceRequests'] and c['source_hashes_equal']
        failed_bound+=2*wall(state)/3600
    return dict(status='Q1_AFFECTED_CPU_AND_SOURCE_CONDITION_RESTORE_ACCEPTED_SCOPED',hosts=hosts,
        actual_process_CPUh_R2=CPU_seconds/3600,allocated_vCPUh_upper_bound_R2=allocated,
        allocated_vCPUh_upper_bound_R1_failures=failed_bound,R1_actual_process_CPUh=None,
        R1_failures_preserved=True,R1_original_stages_unchanged=True,new_GPU_submissions=0,new_GPUh=0,
        budget_reserved_GPUh=0,ledger_writes=0,actual_model_C_replay=False,GPU_ready=False,
        limits=['Full CUDA-linked condition module import remains unvalidated here',
                'Four-card B1 tensor data is absent; no bulk port performed',
                'Head weights identified, not executed; no compression quality/deployment result',
                'Local editing, SSH/staging and Git CPU were not fully metered'])


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    refs={host:ROOT/('reports/cara_sq_q1_'+host+'_cpu_capture'+('1' if host=='two_card' else '2')+'_r2_20261028.json') for host in ('two_card','four_card')}
    old={host:ROOT/('reports/cara_sq_q1_'+host+'_cpu_capture'+('1' if host=='two_card' else '2')+'_20261028.json') for host in ('two_card','four_card')}
    weights=ROOT/'reports/cara_wc73_asset_recheck_20261027.json'
    r=audit({h:json.loads(f.read_text()) for h,f in refs.items()},
            {h:json.loads(f.read_text()) for h,f in old.items()},json.loads(weights.read_text()))
    r['evidence_sha256']={str(f.relative_to(ROOT)):sha(f) for f in [*refs.values(),*old.values(),weights,Path(__file__)]}
    with a.output.open('x') as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:r[k] for k in ('status','actual_process_CPUh_R2','allocated_vCPUh_upper_bound_R2','allocated_vCPUh_upper_bound_R1_failures','new_GPUh','GPU_ready')},indent=2))
