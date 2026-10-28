"""Independent acceptance of host-specific physical S CPU composition only."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from audit_cara_sq_s_owner_cpu_r1 import cpu_mounts, instant, require, result_sha
from cara_sq_s_physical_cpu_r1 import FILES, SCOPE

ROOT=Path(__file__).resolve().parents[1]


def accept(capture,scope,revision,host):
    state,launch,result=capture['container_state'],capture['launch'],capture['result']
    stage='cara-sq-s-physical-cpu-'+host.replace('_','-')+'-r1-20261029'
    require(state['Status']=='exited' and state['ExitCode']==0 and not state['Error']
            and not any(state[k] for k in ('Running','Paused','Restarting','OOMKilled','Dead')),
            'Original CPU container must exit cleanly before physical acceptance')
    require(capture['status']=='SQ_CPU_PREPARATION_CAPTURE' and launch['source_revision']==revision
            and launch['stage'].endswith('/'+stage) and launch['container']==stage+'-cpu'
            and capture['source_hashes_equal'] and capture['runtime_hashes_equal'],
            'Original physical CPU handle/source/runtime differs')
    require(capture['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
            and capture['host_config']==dict(DeviceRequests=None,NanoCpus=2_000_000_000,
                Memory=8*2**30,MemorySwap=8*2**30,CpusetCpus='4,5',NetworkMode='none',ReadonlyRootfs=True),
            'Physical CPU resource/runtime boundary differs')
    cpu_mounts(capture,host)
    require(result is not None and result_sha(result)==capture['result_sha256']
            and result['status']=='S_PHYSICAL_MATRIX_CPU_PASS_NOT_GPU_OR_SCIENTIFIC_ACCEPTANCE'
            and result['scope']==scope and result['profile']==host,
            'Original complete physical CPU result differs')
    require(result['torch_version']=='2.7.1+cu128' and result['actual_platform']['system']=='Linux'
            and result['unit_controls']['tests']==9 and result['unit_controls']['skipped']==0,
            'Complete actual Linux physical controls required')
    require(all(result[k] is False for k in ('CUDA_initialized','actual_Cosmos_weights','real_generated_video',
                'real_OFF_ON_equivalence_accepted','complete_S_GPU_card_accepted'))
            and result['model_weight_loads_forbidden'] is True
            and all(result[k]==0 for k in ('S_labels_collected','GPU_submissions','new_GPUh','ledger_writes')),
            'Physical CPU exceeded its science/GPU boundary')
    expected=scope['hosts'][host]['counts_per_flow'];rows=result['rows']
    require(len(rows)==2 and {r['flow'] for r in rows}=={False,True}
            and result['tiny_tensor_files_loaded']==80,'Both complete physical CPU flows required')
    for row in rows:
        require(row['status']=='PASS' and row['physical_counts']==expected
                and row['complete_new_CPU_paths']==expected['new_paths'] and row['logical_paths']==10
                and row['warm_CPU_paths']==2 and row['imported_OFF_roles']==expected['reused_OFF_paths']
                and row['observed_head_forward_calls']==expected['branch_readouts']
                and row['observed_deep_block_calls']==expected['deep_block_calls']
                and row['whole_state_status']=='COMPLETE_DATA_ONLY_AWAITING_TERMINAL_ACCEPTANCE',
                'Actual physical sampler/head/deep denominators differ')
        require(len(row['OFF_ON_controls'])==4 and all(c['exact'] for c in row['OFF_ON_controls'])
                and sum(c['retained_OFF_has_no_pre_encoding_pixels'] for c in row['OFF_ON_controls'])==expected['reused_OFF_paths']
                and sum(c['pre_encoding_RGB_compared'] for c in row['OFF_ON_controls'])==4-expected['reused_OFF_paths']
                and row['exact_full36_guided_final_latent_and_CPU_RGB_witness'] is True
                and row['full_pipeline_decode_uses_declared_CPU_standin'] is True,
                'Legacy/common decoded/fresh pre-encoding controls differ')
        require((row['storage']['measured_rows'],row['storage']['raw_states'],row['storage']['unique_anchor_files'])==(108,8,24)
                and row['reload_audit']['files_SHA_and_bytes_reloaded']==140
                and row['S_labels_collected']==0 and not row['actual_Cosmos_weights'] and not row['real_generated_video'],
                'Complete data-only streaming/reload cohort differs')
    decode=result['actual_synthetic93_MP4_decode_control'];black=hashlib.sha256();frame=bytes(432*768*3)
    for _ in range(93):black.update(frame)
    require(decode==dict(status='PASS',frames=93,HWC=[432,768,3],production_default_decoder=True,
            actual_full_parent_sampling=False,synthetic_video=True,Cosmos_generated_video=False,
            RGB_sha256=black.hexdigest(),encoded_bytes=decode['encoded_bytes']) and 0<decode['encoded_bytes']<64*2**20,
            'Actual production adapter synthetic93 MP4 decode control differs')
    wall=(instant(state['FinishedAt'])-instant(state['StartedAt'])).total_seconds()
    require(0<result['CPU_wall_seconds']<=wall<=1810 and 0<result['peak_RSS_KiB']*1024<8*2**30,
            'Original physical CPU resource interval differs')
    return dict(passed=True,status='S_PHYSICAL_COLLECTION_CPU_ACCEPTED_NOT_REAL_GPU_OR_LABELS',host=host,
        source_revision=revision,new_CPU_paths=2*expected['new_paths'],logical_roles=20,
        imported_tiny_OFF_roles=2*expected['reused_OFF_paths'],actual_heads_per_flow=expected['branch_readouts'],
        actual_deep_blocks_per_flow=expected['deep_block_calls'],unit_controls=9,files_reloaded=280,
        production_adapter_synthetic93_MP4_decode_accepted=True,real_OFF_ON_equivalence_accepted=False,
        complete_S_GPU_card_accepted=False,S_real_labels=0,GPU_submissions=0,ledger_writes=0,
        resources=dict(container_wall_seconds=wall,worker_wall_seconds=result['CPU_wall_seconds'],
            parent_CPU_seconds=result['CPU_seconds'],reaped_child_CPU_seconds=result['reaped_child_CPU_seconds'],
            parent_peak_RSS_GiB=result['peak_RSS_KiB']/2**20,allocated_vCPU_seconds_upper_bound=2*wall,
            parent_RSS_is_not_cgroup_peak=True,unreaped_child_CPU_not_in_parent_counter=True,
            transport_staging_git_CPU_unmetered=True))


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('Retain independent physical CPU acceptance')
    capture=json.loads(args.capture.read_text());scope=json.loads((ROOT/SCOPE).read_text())
    revision=subprocess.check_output(['git','rev-parse',args.source_revision+'^{commit}'],cwd=ROOT,text=True).strip()
    result=accept(capture,scope,revision,args.host)
    mutations=dict(running_body=lambda c:c['container_state'].update(Running=True),
        changed_source=lambda c:c.update(source_hashes_equal=False),
        GPU_request=lambda c:c['host_config'].update(DeviceRequests=[{'Count':1}]),
        missing_flow=lambda c:c['result']['rows'].pop(),
        changed_heads=lambda c:c['result']['rows'][0].update(observed_head_forward_calls=1),
        changed_imports=lambda c:c['result']['rows'][0].update(imported_OFF_roles=5),
        changed_RGB=lambda c:c['result']['actual_synthetic93_MP4_decode_control'].update(RGB_sha256='0'*64),
        premature_real_acceptance=lambda c:c['result'].update(real_OFF_ON_equivalence_accepted=True))
    rejected={}
    for name,mutate in mutations.items():
        altered=copy.deepcopy(capture);mutate(altered);altered['result_sha256']=result_sha(altered['result'])
        try:accept(altered,scope,revision,args.host)
        except ValueError:rejected[name]=True
        else:raise ValueError('Forged physical CPU receipt accepted: '+name)
    result.update(capture_ref=str(args.capture),capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        rejection_controls=rejected,critical_source_sha256={name:hashlib.sha256(subprocess.check_output(
            ['git','show',revision+':'+name],cwd=ROOT)).hexdigest() for name in FILES})
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','host','new_CPU_paths','actual_heads_per_flow','resources')}))


if __name__=='__main__':main()
