"""Independently accept only the frozen S owner CPU component cohort."""
import argparse
import copy
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SCOPE='plans/cara_next_stage_20261028/sq/S_OWNER_ROUNDTRIP_CPU_R1.json'
CRITICAL=('src/wcomr/sq_s_owner_roundtrip_r1.py','src/wcomr/sq_s_sources_r1.py',
          'tests/check_sq_s_owner_roundtrip_cpu_r1.py','scripts/check_cara_sq_s_owner_cpu_r1.py',SCOPE)


def require(value,message):
    if not value:raise ValueError(message)


def result_sha(value):
    return hashlib.sha256((json.dumps(value,indent=2,allow_nan=False)+'\n').encode()).hexdigest()


def instant(value):
    return datetime.fromisoformat(re.sub(r'(\.\d{6})\d+(?=Z|[+-])',r'\1',value).replace('Z','+00:00'))


def accept(capture,scope,revision):
    state=capture['container_state'];launch=capture['launch'];result=capture['result']
    require(capture['status']=='SQ_CPU_PREPARATION_CAPTURE' and state['Status']=='exited'
            and not any(state[k] for k in ('Running','Paused','Restarting','OOMKilled','Dead'))
            and state['ExitCode']==0 and not state['Error'],'Original S CPU container is not cleanly terminal')
    recorded=launch['source_revision']
    require(len(recorded)>=8 and revision.startswith(recorded) and launch['status']=='SQ_GPU_HIDDEN_CPU_PREPARATION_LAUNCHED'
            and launch['stage'].endswith('/cara-sq-s-owner-cpu-four-card-r2-20261029')
            and launch['container']=='cara-sq-s-owner-cpu-four-card-r2-20261029-cpu'
            and capture['source_hashes_equal'] and capture['runtime_hashes_equal'],
            'S CPU original handle or immutable source differs')
    require(capture['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d',
            'S CPU registered runtime image differs')
    require(capture['host_config']==dict(DeviceRequests=None,NanoCpus=2_000_000_000,
            Memory=8*2**30,MemorySwap=8*2**30,CpusetCpus='4,5',NetworkMode='none',ReadonlyRootfs=True),
            'S CPU resource boundary differs')
    mounts={row['Destination']:row for row in capture['mounts']}
    root='/data20t/gaokuangda/worldcache_workspace'
    require(set(mounts)=={root,launch['stage']} and not mounts[root]['RW'] and mounts[launch['stage']]['RW'],
            'S CPU writable mount escaped its own stage')
    require(result is not None and result_sha(result)==capture['result_sha256'],
            'S CPU original result bytes differ')
    require(result['status']=='SQ_S_OWNER_CPU_PASS_STANDINS_NOT_COMPLETE_COLLECTOR'
            and result['scope']==scope and result['profile']=='four_card'
            and result['fixture_status']=='PINNED_PIPELINE_CPU_FIXTURE_EXTERNAL_EXERCISE_COMPLETE',
            'Complete frozen S CPU fixture required')
    require(all(result[k] is False for k in ('CUDA_initialized','actual_Cosmos_weights',
            'real_generated_video','complete_S_collector_accepted'))
            and all(result[k]==0 for k in ('S_labels_collected','GPU_submissions','new_GPUh','ledger_writes'))
            and result['CPU_import_probes_restored_before_sampling'] is True
            and result['model_weight_loads_forbidden'] is True,
            'S component exceeded its CPU-only evidence boundary')
    require(result['actual_platform']['system']=='Linux' and result['torch_version']=='2.7.1+cu128',
            'Actual registered Linux CPU runtime required')
    rows=result['rows'];require(len(rows)==2 and {r['flow'] for r in rows}=={False,True},'Both complete flow settings required')
    for row in rows:
        require(row['status']=='PASS' and row['complete_CPU_paths']==4
                and [p['parent'] for p in row['parents']]==scope['parents']
                and all(p['full36_OFF_ON_guided_latent_CPU_video_equal'] is True for p in row['parents'])
                and [e['step'] for e in row['events']]==scope['checked_post_pair_steps']*2
                and all(e['dirty_owner_refused_and_cleaned'] is True
                        and e['policy_and_poison_changes_refused'] is True
                        and 0<e['logical_snapshot_bytes']<=128*2**20 for e in row['events'])
                and row['actual_Cosmos_weights'] is False and row['real_generated_video'] is False
                and row['S_labels_collected']==0 and row['complete_S_collector_accepted'] is False,
                'S CPU parent, full path, restoration or falsification cohort missing')
    require(sum(r['complete_CPU_paths'] for r in rows)==scope['complete_CPU_paths']
            and sum(len(r['events']) for r in rows)==scope['expected_checked_boundaries'],
            'S CPU complete cohort denominator differs')
    wall=(instant(state['FinishedAt'])-instant(state['StartedAt'])).total_seconds()
    require(0<wall<=1810 and all(math.isfinite(result[k]) and result[k]>0 for k in
            ('CPU_wall_seconds','CPU_seconds','peak_RSS_KiB'))
            and result['CPU_wall_seconds']<=wall and result['CPU_seconds']<=2*wall
            and result['peak_RSS_KiB']*1024<=8*2**30,'S CPU resource record exceeds the registered scope')
    return dict(host='four_card',complete_CPU_paths=8,checked_boundaries=16,
        worker_wall_seconds=result['CPU_wall_seconds'],CPU_seconds=result['CPU_seconds'],
        peak_RSS_GiB=result['peak_RSS_KiB']/2**20,container_wall_seconds=wall,
        component_CPU_accepted=True,complete_S_collector_accepted=False,actual_GPU_or_science_accepted=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original S CPU acceptance')
    capture=json.loads(args.capture.read_text());scope=json.loads((ROOT/SCOPE).read_text())
    revision=subprocess.check_output(['git','rev-parse',args.source_revision],cwd=ROOT,text=True).strip()
    require(subprocess.check_output(['git','rev-parse',capture['launch']['source_revision']+'^{commit}'],
            cwd=ROOT,text=True).strip()==revision,'Recorded source abbreviation does not resolve to the frozen full revision')
    accepted=accept(capture,scope,revision);negative=[]
    for case in ('running','missing_boundary','missing_parent','CUDA_claim','real_video_claim'):
        bad=copy.deepcopy(capture)
        if case=='running':bad['container_state'].update(Status='running',Running=True)
        elif case=='missing_boundary':bad['result']['rows'][-1]['events'].pop()
        elif case=='missing_parent':bad['result']['rows'][-1]['parents'].pop()
        elif case=='CUDA_claim':bad['result']['CUDA_initialized']=True
        elif case=='real_video_claim':bad['result']['real_generated_video']=True
        bad['result_sha256']=result_sha(bad['result'])
        try:accept(bad,scope,revision)
        except ValueError as error:negative.append(dict(case=case,rejected=True,reason=str(error)))
        else:raise AssertionError('S component acceptance admitted '+case)
    value=dict(status='S_OWNER_FOUR_CARD_R2_CPU_COMPONENT_ACCEPTED_NOT_COMPLETE_S_COLLECTOR',
        passed=True,host='four_card',dual_host_CPU_accepted=False,source_revision=revision,
        source_revision_as_recorded=capture['launch']['source_revision'],
        critical_source_sha256={name:hashlib.sha256(subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)).hexdigest()
                               for name in CRITICAL},
        capture_ref=str(args.capture),capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        result_sha256=capture['result_sha256'],accepted=accepted,negative_controls=negative,
        complete_S_collector_accepted=False,S_labels_collected=0,GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with args.output.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(value['accepted']))


if __name__=='__main__':main()
