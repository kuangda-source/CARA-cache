"""Independent terminal/source and complete affected guard-matrix acceptance."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

from audit_cara_sq_s_owner_cpu_r1 import cpu_mounts,instant,require,result_sha
from cara_sq_s_resource_guard_cpu_r1 import FILES,SCOPE

ROOT=Path(__file__).resolve().parents[1]


def accept(capture,scope,contract,revision,host):
    s,L,r=capture['container_state'],capture['launch'],capture['result']
    name='cara-sq-s-resource-guard-cpu-'+host.replace('_','-')+'-r1-20261029'
    require(s['Status']=='exited' and s['ExitCode']==0 and not s['Error']
        and not any(s[k] for k in ('Running','Paused','Restarting','OOMKilled','Dead'))
        and capture['original_CLI_live'] is False,'Original guard CPU handles must both be terminal')
    require(L['source_revision']==revision and L['stage'].endswith('/'+name) and L['container']==name+'-cpu'
        and capture['source_hashes_equal'] and capture['runtime_hashes_equal'],'Original guard source/handle differs')
    require(capture['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
        and capture['host_config']==dict(DeviceRequests=None,NanoCpus=2_000_000_000,Memory=8*2**30,
            MemorySwap=8*2**30,CpusetCpus='4,5',NetworkMode='none',ReadonlyRootfs=True),'Original CPU sandbox differs')
    cpu_mounts(capture,host)
    require(r is not None and result_sha(r)==capture['result_sha256']
        and r['status']=='S_RESOURCE_ENTRY_FULL_PHYSICAL_CPU_PASS_NOT_GPU_CARD'
        and r['scope']==scope and r['profile']==host,'Original guard CPU result bytes differ')
    require(r['unit_controls']['tests']==13 and r['unit_controls']['skipped']==0
        and r['original_meta_and_default_decode_components_reused']==scope['accepted_unchanged_components']
        and r['new_meta_architecture_or_synthetic_decode_runs']==0,'Affected controls or reuse boundary differs')
    rows=r['rows'];expected=scope['hosts'][host]
    require(len(rows)==2 and [row['flow'] for row in rows]==[False,True]
        and r['tiny_tensor_files_loaded']==expected['tiny_tensor_reloads'],'Both exact original flow matrices required')
    maxima=dict(logical=0,backing=0)
    for row in rows:
        guard=row['resource_entry'];records=guard['records']
        require(row['status']=='PASS' and row['physical_counts']==expected['counts_per_flow']
            and row['complete_new_CPU_paths']==expected['counts_per_flow']['new_paths']
            and row['fixture_source_CPU_paths']==expected['fixture_source_paths_per_flow']
            and row['logical_paths']==10 and len(row['OFF_ON_controls'])==4
            and all(c['exact'] for c in row['OFF_ON_controls'])
            and row['observed_head_forward_calls']==expected['counts_per_flow']['branch_readouts']
            and row['observed_deep_block_calls']==expected['counts_per_flow']['deep_block_calls']
            and row['reload_audit']['files_SHA_and_bytes_reloaded']==140
            and row['storage']['measured_rows']==108 and row['storage']['raw_states']==8
            and row['storage']['unique_anchor_files']==24,'Full physical/streaming cohort changed')
        require(guard['status']=='ALL108_PRE_SNAPSHOT_GUARDS_PASS_CPU_FIXTURE'
            and guard['contract_sha256']==contract['contract_sha256']
            and guard['original_collection_entry_restored'] is True
            and guard['original_numerical_collector_and_physical_matrix_unchanged'] is True
            and guard['source_OFF_resource_checks']==0 and len(records)==108,'Incomplete original guard cohort')
        slots=[]
        for record in records:
            key=(record['slot_id'],record['prompt'],record['parent'])
            if key not in slots:slots.append(key)
            require(record['contract_sha256']==contract['contract_sha256']
                and len(record['inventory_sha256'])==64
                and record['all_eight_groups_checked'] is True and record['unknown_tensor_fields_refused'] is True
                and record['tensor_values_read'] is False and record['tensor_copies_performed']==0
                and record['GPU_admission'] is False
                and record['mutable_buffer_bytes']==0
                and 0<record['original_logical_copy_guard_bytes']<=contract['limits']['logical_copy_guard_bytes']
                and 0<record['full_backing_copy_guard_bytes']<=contract['limits']['backing_copy_guard_bytes']
                and set(record['live_backing_storage_bytes_by_device'])=={'cpu'},'Resource metadata or scope changed')
            maxima['logical']=max(maxima['logical'],record['original_logical_copy_guard_bytes'])
            maxima['backing']=max(maxima['backing'],record['full_backing_copy_guard_bytes'])
        require(len(slots)==4 and len({s[1] for s in slots})==2
            and {s[2] for s in slots}=={'Shared25-C','F19-C'}
            and [(v['slot_id'],v['prompt'],v['parent'],v['step']) for v in records]==[
                (*slot,step) for slot in slots for step in range(8,36) if step!=24],
            'Complete both inputs/parents and ordered27 target guards required')
    require(all(r[k] is True for k in ('CPU_import_probes_restored','model_weight_loads_forbidden','Hugging_Face_downloads_blocked'))
        and all(r[k] is False for k in ('actual_Cosmos_weights','real_generated_video','CUDA_initialized',
            'actual_S_GPU_entry_accepted','whole_S_quote_frozen'))
        and all(r[k]==0 for k in ('S_real_labels','GPU_submissions','new_GPUh','ledger_writes')),
        'Guard CPU preparation exceeded its evidence scope')
    require(r['actual_platform']['system']=='Linux' and r['torch_version']=='2.7.1+cu128','Registered Linux runtime required')
    wall=(instant(s['FinishedAt'])-instant(s['StartedAt'])).total_seconds()
    require(0<r['CPU_wall_seconds']<=wall<=1810 and 0<r['peak_RSS_KiB']<8*2**20,'Original CPU cost/limit differs')
    return dict(status='S_RESOURCE_ENTRY_FULL_PHYSICAL_DUAL_COMPONENT_CPU_ACCEPTED_NOT_GPU_CARD',passed=True,
        host=host,source_revision=revision,unit_controls=13,complete_matrix_paths=2*expected['counts_per_flow']['new_paths'],
        separate_fixture_source_paths=2*expected['fixture_source_paths_per_flow'],selected_target_guards=216,
        streamed_files_reloaded=280,max_guard_bytes=maxima,
        resources=dict(container_wall_seconds=wall,worker_wall_seconds=r['CPU_wall_seconds'],worker_CPU_seconds=r['CPU_seconds'],
            reaped_child_CPU_seconds=r['reaped_child_CPU_seconds'],parent_peak_RSS_GiB=r['peak_RSS_KiB']/2**20,
            allocated_vCPU_seconds_upper_bound=2*wall,wrapper_post_result_and_staging_CPU_unmetered=True),
        real_S_labels=0,actual_S_GPU_entry_accepted=False,whole_S_quote_frozen=False,GPU_submissions=0,ledger_writes=0)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    require(not args.output.exists(),'Retain original guard CPU acceptance')
    revision=subprocess.check_output(['git','rev-parse',args.source_revision+'^{commit}'],cwd=ROOT,text=True).strip()
    frozen=lambda n:json.loads(subprocess.check_output(['git','show',revision+':'+n],cwd=ROOT))
    scope=frozen(SCOPE);contract=frozen('plans/cara_next_stage_20261028/sq/S_RESOURCE_GUARD_CPU_CONTRACT_R1.json')
    capture=json.loads(args.capture.read_text());result=accept(capture,scope,contract,revision,args.host)
    cases=dict(live_container=lambda c:c['container_state'].update(Running=True),live_CLI=lambda c:c.update(original_CLI_live=True),
        GPU_exposure=lambda c:c['host_config'].update(DeviceRequests=[{}]),stale_source=lambda c:c.update(source_hashes_equal=False),
        skipped_unit=lambda c:c['result']['unit_controls'].update(skipped=1),
        missing_guard=lambda c:c['result']['rows'][0]['resource_entry']['records'].pop(),
        bypass_schema=lambda c:c['result']['rows'][0]['resource_entry']['records'][0].update(unknown_tensor_fields_refused=False),
        bad_contract=lambda c:c['result']['rows'][0]['resource_entry']['records'][0].update(contract_sha256='0'*64),
        missing_raw=lambda c:c['result']['rows'][0]['storage'].update(raw_states=7),
        whole_GPU_claim=lambda c:c['result'].update(actual_S_GPU_entry_accepted=True))
    rejected={}
    for name,mutate in cases.items():
        forged=copy.deepcopy(capture);mutate(forged);forged['result_sha256']=result_sha(forged['result'])
        try:accept(forged,scope,contract,revision,args.host)
        except ValueError:rejected[name]=True
        else:raise ValueError('Forged guard CPU evidence accepted: '+name)
    result.update(capture_ref=str(args.capture),capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        rejection_controls=rejected,critical_source_sha256={n:hashlib.sha256(subprocess.check_output(
            ['git','show',revision+':'+n],cwd=ROOT)).hexdigest() for n in FILES})
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','host','selected_target_guards','resources')}))


if __name__=='__main__':main()
