"""Accept the exact whole S CPU cohort; this never accepts real S labels."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess

from audit_cara_sq_s_owner_cpu_r1 import cpu_mounts,instant,require,result_sha
from audit_cara_sq_s_storage_cpu_r2 import CRITICAL as COMPONENTS

ROOT=Path(__file__).resolve().parents[1]
SCOPE='plans/cara_next_stage_20261028/sq/S_BATCH_CPU_R1.json'
CRITICAL=tuple(dict.fromkeys(COMPONENTS+('src/wcomr/sq_s_batch_r1.py',
    'tests/test_sq_s_batch_r1.py','tests/check_sq_s_batch_cpu_r1.py',
    'scripts/check_cara_sq_s_batch_cpu_r1.py',SCOPE)))


def accept(capture,scope,revision,host):
    state=capture['container_state'];launch=capture['launch'];result=capture['result']
    stage='cara-sq-s-batch-cpu-'+host.replace('_','-')+'-r1-20261029'
    require(state['Status']=='exited' and not any(state[k] for k in ('Running','Paused','Restarting','OOMKilled','Dead'))
            and state['ExitCode']==0 and not state['Error'],'Original whole S CPU container is not cleanly terminal')
    require(launch['source_revision']==revision and launch['stage'].endswith('/'+stage)
            and launch['container']==stage+'-cpu' and capture['source_hashes_equal']
            and capture['runtime_hashes_equal'],'Original whole S source/host/handle differs')
    require(capture['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d',
            'Registered runtime image differs')
    require(capture['host_config']==dict(DeviceRequests=None,NanoCpus=2_000_000_000,
        Memory=8*2**30,MemorySwap=8*2**30,CpusetCpus='4,5',NetworkMode='none',ReadonlyRootfs=True),
        'Whole S CPU resource boundary differs')
    cpu_mounts(capture,host)
    require(result is not None and result_sha(result)==capture['result_sha256'],'Original whole S result bytes differ')
    require(result['status']=='S_WHOLE_UPPER_MATRIX_CPU_PASS_NOT_GPU_OR_SCIENTIFIC_ACCEPTANCE'
            and result['scope']==scope and result['profile']==host,'Complete whole S CPU scope required')
    require(all(result[k] is False for k in ('CUDA_initialized','actual_Cosmos_weights','real_generated_video'))
            and all(result[k]==0 for k in ('S_labels_collected','GPU_submissions','new_GPUh','ledger_writes'))
            and result['model_weight_loads_forbidden'] is True,'Whole S exceeded its CPU evidence boundary')
    require(result['actual_platform']['system']=='Linux' and result['torch_version']=='2.7.1+cu128',
            'Actual registered Linux CPU runtime required')
    require(result['unit_controls']['tests']==7 and result['unit_controls']['skipped']==0
            and result['tiny_tensor_files_loaded']==80,'Full unit and tiny-file cohort required')
    rows=result['rows'];require(len(rows)==2 and {r['flow'] for r in rows}=={False,True},'Both flow cohorts required')
    expected=dict(paths=10,warm_paths=2,OFF_paths=4,ON_paths=4,parent_solver_pairs=360,
        parent_Dense_pairs=220,parent_C_pairs=140,extra_Dense_teacher_pairs=56,
        extra_C_shadow_pairs=52,total_pairs=468,total_branch_readouts=936,moment_rows=108,
        F19_raw_states=8,unique_raw_anchors=24,extra_Dense_hidden_head_pairs=0)
    for row in rows:
        require(row['status']=='PASS' and row['complete_CPU_paths']==10 and row['warm_CPU_paths']==2
                and row['counts']==expected and row['whole_state_status']=='COMPLETE_DATA_ONLY_AWAITING_TERMINAL_ACCEPTANCE'
                and row['observed_head_forward_calls']==936 and row['observed_deep_block_calls']==552
                and row['exact_full36_guided_final_latent_decoded93_RGB'] is True
                and row['all_results_JSON_metadata_only'] is True
                and row['S_labels_collected']==0 and row['actual_Cosmos_weights'] is False
                and row['real_generated_video'] is False,'Complete ten-path/head/deep/CPU cohort missing')
        controls=row['OFF_ON_controls']
        require(len(controls)==4 and {(r['prompt'],r['parent']) for r in controls}=={
            (p,h) for p in scope['CPU_prompts'] for h in ('Shared25-C','F19-C')}
            and all(r['exact'] is True for r in controls),'All four full OFF/ON controls required')
        store=row['storage'];reload=row['reload_audit']
        require((store['measured_rows'],store['raw_states'],store['unique_anchor_files'])==(108,8,24)
                and 0<store['actual_stored_bytes']<=16*2**20
                and reload['files_SHA_and_bytes_reloaded']==140 and reload['measured_rows_reloaded']==108
                and reload['raw_states_reloaded']==8 and reload['unique_anchors_reloaded']==24
                and reload['actual_C_reference_and_noise_grid_retained'] is True,
                'Complete streaming/reload denominator missing')
    wall=(instant(state['FinishedAt'])-instant(state['StartedAt'])).total_seconds()
    require(0<wall<=1810 and all(math.isfinite(result[k]) and result[k]>0 for k in
        ('CPU_wall_seconds','CPU_seconds','peak_RSS_KiB')) and result['CPU_wall_seconds']<=wall
        and result['CPU_seconds']<=2*wall and result['peak_RSS_KiB']*1024<=8*2**30,
        'Whole S CPU resource record exceeds the registered boundary')
    return dict(host=host,complete_CPU_paths=20,unit_controls=7,files_reloaded=280,
        observed_heads_per_flow=936,observed_deep_blocks_per_flow=552,
        worker_wall_seconds=result['CPU_wall_seconds'],worker_parent_CPU_seconds=result['CPU_seconds'],
        parent_peak_RSS_GiB=result['peak_RSS_KiB']/2**20,container_wall_seconds=wall,
        allocated_vCPUh_upper_bound=2*wall/3600,child_compiler_CPU_not_fully_metered=True,
        whole_CPU_matrix_accepted=True,actual_GPU_or_S_science_accepted=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original whole S acceptance')
    capture=json.loads(args.capture.read_text());scope=json.loads((ROOT/SCOPE).read_text())
    revision=subprocess.check_output(['git','rev-parse',args.source_revision+'^{commit}'],cwd=ROOT,text=True).strip()
    accepted=accept(capture,scope,revision,args.host);negative=[]
    for case in ('running','missing_flow','missing_warm','wrong_heads','wrong_deep','unit_skip',
                 'short_RGB','missing_reload','GPU_claim','real_label','resource_expansion','extra_mount'):
        bad=copy.deepcopy(capture);r=bad['result']
        if case=='running':bad['container_state'].update(Status='running',Running=True)
        elif case=='missing_flow':r['rows'].pop()
        elif case=='missing_warm':r['rows'][0]['warm_CPU_paths']=1
        elif case=='wrong_heads':r['rows'][0]['observed_head_forward_calls']=935
        elif case=='wrong_deep':r['rows'][0]['observed_deep_block_calls']=551
        elif case=='unit_skip':r['unit_controls']['skipped']=1
        elif case=='short_RGB':r['rows'][0]['exact_full36_guided_final_latent_decoded93_RGB']=False
        elif case=='missing_reload':r['rows'][0]['reload_audit']['files_SHA_and_bytes_reloaded']=139
        elif case=='GPU_claim':r['CUDA_initialized']=True
        elif case=='real_label':r['S_labels_collected']=108
        elif case=='resource_expansion':bad['host_config']['Memory']=16*2**30
        elif case=='extra_mount':
            extra=copy.deepcopy(bad['mounts'][0]);extra.update(Source='/unregistered',Destination='/unregistered');bad['mounts'].append(extra)
        bad['result_sha256']=result_sha(r)
        try:accept(bad,scope,revision,args.host)
        except ValueError as error:negative.append(dict(case=case,rejected=True,reason=str(error)))
        else:raise AssertionError('Whole S CPU acceptance admitted '+case)
    value=dict(status='S_WHOLE_UPPER_MATRIX_'+args.host.upper()+'_CPU_ACCEPTED',passed=True,
        host=args.host,source_revision=revision,critical_source_sha256={n:hashlib.sha256(
            subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT)).hexdigest() for n in CRITICAL},
        capture_ref=str(args.capture),capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        result_sha256=capture['result_sha256'],accepted=accepted,negative_controls=negative,
        complete_S_GPU_card_accepted=False,S_real_labels=0,GPU_submissions=0,ledger_writes=0)
    with args.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(accepted))


if __name__=='__main__':main()
