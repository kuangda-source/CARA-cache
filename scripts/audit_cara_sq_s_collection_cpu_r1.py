"""Accept full S CPU topology only; never accept real labels, raw storage or GPU."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess

from audit_cara_sq_s_owner_cpu_r1 import instant,require,result_sha

ROOT=Path(__file__).resolve().parents[1]
SCOPE='plans/cara_next_stage_20261028/sq/S_COLLECTION_CPU_R1.json'
STAGE='cara-sq-s-collection-cpu-four-card-r1-20261029'
CRITICAL=('src/wcomr/sq_s_collection_r1.py','src/wcomr/sq_s_owner_roundtrip_r1.py',
    'src/wcomr/sq_s_sources_r1.py','src/wcomr/sq_risk_r1.py',
    'tests/check_sq_s_collection_cpu_r1.py','scripts/check_cara_sq_s_collection_cpu_r1.py',SCOPE)


def accept(capture,scope,revision):
    state=capture['container_state'];launch=capture['launch'];result=capture['result']
    require(capture['status']=='SQ_CPU_PREPARATION_CAPTURE' and state['Status']=='exited'
            and not any(state[k] for k in ('Running','Paused','Restarting','OOMKilled','Dead'))
            and state['ExitCode']==0 and not state['Error'],'Original S topology CPU container is not cleanly terminal')
    require(launch['source_revision']==revision and launch['status']=='SQ_GPU_HIDDEN_CPU_PREPARATION_LAUNCHED'
            and launch['stage'].endswith('/'+STAGE) and launch['container']==STAGE+'-cpu'
            and capture['source_hashes_equal'] and capture['runtime_hashes_equal'],
            'S topology original handle or immutable source differs')
    require(capture['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
            and capture['host_config']==dict(DeviceRequests=None,NanoCpus=2_000_000_000,
            Memory=8*2**30,MemorySwap=8*2**30,CpusetCpus='4,5',NetworkMode='none',ReadonlyRootfs=True),
            'S topology CPU runtime or resource boundary differs')
    mounts={row['Destination']:row for row in capture['mounts']};root='/data20t/gaokuangda/worldcache_workspace'
    require(set(mounts)=={root,launch['stage']} and not mounts[root]['RW'] and mounts[launch['stage']]['RW'],
            'S topology CPU writable mount escaped its own stage')
    require(result is not None and result_sha(result)==capture['result_sha256'],
            'S topology original result bytes differ')
    require(result['status']=='SQ_S_COLLECTION_CPU_TOPOLOGY_PASS_NOT_REAL_MODEL_OR_STORAGE_ACCEPTANCE'
            and result['scope']==scope and result['profile']=='four_card'
            and result['fixture_status']=='PINNED_PIPELINE_CPU_FIXTURE_EXTERNAL_EXERCISE_COMPLETE',
            'Complete frozen S CPU topology required')
    require(all(result[k] is False for k in ('CUDA_initialized','actual_Cosmos_weights','real_generated_video',
            'streaming_raw_storage_accepted','complete_S_card_accepted'))
            and all(result[k]==0 for k in ('S_labels_collected','GPU_submissions','new_GPUh','ledger_writes'))
            and result['CPU_import_probes_restored_before_sampling'] is True
            and result['model_weight_loads_forbidden'] is True,
            'S topology exceeded its CPU-only evidence boundary')
    require(result['actual_platform']['system']=='Linux' and result['torch_version']=='2.7.1+cu128',
            'Registered Linux CPU runtime required')
    rows=result['rows'];require(len(rows)==2 and {r['flow'] for r in rows}=={False,True},'Both full flow settings required')
    expected_controls={(p,h) for p in scope['CPU_prompts'] for h in scope['parents']}
    expected_raw={(p,'F19-C',t) for p in scope['CPU_prompts'] for t in scope['raw_steps']}
    dense={'Shared25-C':tuple(range(1,22))+(24,27,30,36),
           'F19-C':tuple(range(1,9))+(10,12,14,16,18,20,21,24,27,30,36)}
    for row in rows:
        require(row['status']=='PASS' and row['complete_CPU_paths']==8 and row['CPU_fixture_moment_rows']==108
                and row['extra_Dense_teacher_pairs']==56 and row['extra_C_readout_pairs']==52
                and row['Dense_hidden_replay_heads']==0 and row['pre_D_sources_and_same_state_prefix_checked'] is True,
                'S topology 108/56/52 denominators or source controls differ')
        controls=row['OFF_ON_controls'];raw=row['raw_CPU_states']
        require(len(controls)==4 and {(r['prompt'],r['parent']) for r in controls}==expected_controls
                and all(r['full36_OFF_ON_equal'] is True for r in controls),'S full36 parent OFF/ON controls missing')
        require(len(raw)==8 and {(r['prompt'],r['parent'],r['step']) for r in raw}==expected_raw
                and all(r['CPU_data_only'] is True
                        and tuple(r['past_steps'])==tuple(t for t in dense[r['parent']] if t<r['step'])[-2:]
                        for r in raw),'S raw callback identities or strictly past sources differ')
        require(row['actual_Cosmos_weights'] is False and row['real_generated_video'] is False
                and row['S_labels_collected']==0 and row['streaming_raw_storage_accepted'] is False
                and row['real_model_S_collector_accepted'] is False,'S fixture cannot accept real labels, videos or storage')
    require(sum(r['complete_CPU_paths'] for r in rows)==scope['complete_CPU_paths'],'S topology complete path denominator differs')
    wall=(instant(state['FinishedAt'])-instant(state['StartedAt'])).total_seconds()
    require(0<wall<=1810 and all(math.isfinite(result[k]) and result[k]>0 for k in
            ('CPU_wall_seconds','CPU_seconds','peak_RSS_KiB'))
            and result['CPU_wall_seconds']<=wall and result['CPU_seconds']<=2*wall
            and result['peak_RSS_KiB']*1024<=8*2**30,'S topology CPU resources exceed the registered boundary')
    return dict(host='four_card',complete_CPU_paths=16,CPU_fixture_moment_rows=216,
        extra_Dense_teacher_pairs=112,extra_C_readout_pairs=104,raw_CPU_callbacks=16,
        worker_wall_seconds=result['CPU_wall_seconds'],CPU_seconds=result['CPU_seconds'],
        peak_RSS_GiB=result['peak_RSS_KiB']/2**20,container_wall_seconds=wall,
        CPU_topology_accepted=True,streaming_raw_storage_accepted=False,
        real_model_S_collector_accepted=False,actual_GPU_or_science_accepted=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original S topology CPU acceptance')
    capture=json.loads(args.capture.read_text());scope=json.loads((ROOT/SCOPE).read_text())
    revision=subprocess.check_output(['git','rev-parse',args.source_revision+'^{commit}'],cwd=ROOT,text=True).strip()
    accepted=accept(capture,scope,revision);negative=[]
    for case in ('running','missing_parent','missing_raw','current_D_source','wrong_Dense_count','CUDA_claim','storage_claim'):
        bad=copy.deepcopy(capture)
        if case=='running':bad['container_state'].update(Status='running',Running=True)
        elif case=='missing_parent':bad['result']['rows'][-1]['OFF_ON_controls'].pop()
        elif case=='missing_raw':bad['result']['rows'][-1]['raw_CPU_states'].pop()
        elif case=='current_D_source':
            raw=bad['result']['rows'][-1]['raw_CPU_states'][-1];raw['past_steps'][-1]=raw['step']
        elif case=='wrong_Dense_count':bad['result']['rows'][-1]['extra_Dense_teacher_pairs']=55
        elif case=='CUDA_claim':bad['result']['CUDA_initialized']=True
        elif case=='storage_claim':bad['result']['streaming_raw_storage_accepted']=True
        bad['result_sha256']=result_sha(bad['result'])
        try:accept(bad,scope,revision)
        except ValueError as error:negative.append(dict(case=case,rejected=True,reason=str(error)))
        else:raise AssertionError('S topology acceptance admitted '+case)
    value=dict(status='S_COLLECTION_FOUR_CARD_CPU_TOPOLOGY_ACCEPTED_NOT_REAL_MODEL_OR_STORAGE',
        passed=True,host='four_card',dual_host_CPU_accepted=False,source_revision=revision,
        critical_source_sha256={name:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)).hexdigest()
                               for name in CRITICAL},
        capture_ref=str(args.capture),capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        result_sha256=capture['result_sha256'],accepted=accepted,negative_controls=negative,
        streaming_raw_storage_accepted=False,complete_S_card_accepted=False,S_labels_collected=0,
        GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with args.output.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(value['accepted']))


if __name__=='__main__':main()
