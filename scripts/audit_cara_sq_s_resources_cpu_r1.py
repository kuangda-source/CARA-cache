"""Accept only original terminal S metadata CPU evidence and all boundaries."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess

from audit_cara_sq_s_owner_cpu_r1 import cpu_mounts,instant,require,result_sha
from cara_sq_s_resources_cpu_r1 import FILES,SCOPE_R2,SCOPE_R3

ROOT=Path(__file__).resolve().parents[1]
WIDTHS={'torch.bool':1,'torch.uint8':1,'torch.int8':1,'torch.int16':2,'torch.int32':4,'torch.int64':8,
    'torch.bfloat16':2,'torch.float16':2,'torch.float32':4,'torch.float64':8,'torch.complex64':8,'torch.complex128':16}


def validate_inventory(report):
    tensors=report['tensors'];storages=report['storages']
    require(report['tensor_values_read'] is False and report['tensor_copies_performed']==0
        and report['measured_allocator_peak'] is False,'Inventory claimed value/copy/allocator work')
    require([row['id'] for row in storages]==list(range(len(storages)))
        and len(storages)==report['unique_tensor_storages']
        and len(tensors)==report['logical_tensor_references'],'Storage/reference denominator differs')
    for row in tensors:
        width=WIDTHS[row['dtype']];shape=row['shape'];stride=row['stride']
        require(len(shape)==len(stride) and all(type(v) is int and v>=0 for v in shape+stride)
            and row['logical_bytes']==math.prod(shape)*width,'Original tensor shape/dtype/byte count differs')
        storage=storages[row['storage_id']]
        require(storage['device']==row['device'] and storage['metadata_only']==(row['device']=='meta')
            and (not math.prod(shape) or (row['storage_offset']+sum((n-1)*s for n,s in zip(shape,stride))+1)*width<=storage['bytes']),
            'A tensor view extends beyond its reported backing storage')
    devices={}
    for row in storages:devices[row['device']]=devices.get(row['device'],0)+row['bytes']
    require(devices==report['backing_storage_bytes_by_device']
        and sum(r['logical_bytes'] for r in tensors)==report['logical_tensor_bytes']
        and len({r['object_id'] for r in tensors})==report['unique_tensor_objects']
        and report['numpy_backing_bytes']>=0
        and report['any_meta_tensors']==any(r['device']=='meta' for r in tensors),
        'Original ownership inventory accounting differs')


def accept(capture,scope,revision,host):
    state,launch,result=capture['container_state'],capture['launch'],capture['result']
    name='cara-sq-s-resources-cpu-'+host.replace('_','-')+'-r3-20261029'
    require(state['Status']=='exited' and state['ExitCode']==0 and not state['Error']
        and not any(state[k] for k in ('Running','Paused','Restarting','OOMKilled','Dead'))
        and capture['original_CLI_live'] is False,'Original S resource CPU handles are not terminal')
    require(launch['source_revision']==revision and launch['stage'].endswith('/'+name)
        and launch['container']==name+'-cpu' and capture['source_hashes_equal'] and capture['runtime_hashes_equal'],
        'Original S resource CPU source/handle differs')
    require(capture['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
        and capture['host_config']==dict(DeviceRequests=None,NanoCpus=2_000_000_000,Memory=8*2**30,
            MemorySwap=8*2**30,CpusetCpus='4,5',NetworkMode='none',ReadonlyRootfs=True),
        'Original registered CPU image/resources differ')
    cpu_mounts(capture,host)
    require(result is not None and result_sha(result)==capture['result_sha256']
        and result['status']=='SQ_S_COMPLETE_OWNERSHIP_AND_META_ARCHITECTURE_CPU_PASS_NOT_GPU_CARD'
        and result['scope']==scope and result['profile']==host,'Original complete resource result bytes differ')
    require(result['unit_controls']['tests']==8 and result['unit_controls']['skipped']==0,
        'Eight complete original unit controls required')
    meta=result['full2B_meta_architecture']
    require(meta['blocks']==28 and meta['parameter_tensors']==569 and meta['parameter_dtypes']=={'torch.bfloat16':569}
        and meta['matches_original_shared_eval_topology'] is True and meta['use_wan_fp32_strategy'] is True
        and meta['checkpoint_paths_resolved'] is False
        and all(meta[k] is False for k in ('weights_loaded','network_forward_executed','full_model_GPU_memory_peak_measured')),
        'Only the original full2B meta architecture may be accepted')
    for key in ('parameters','buffers'):
        validate_inventory(meta[key]);require(meta[key]['any_meta_tensors'] is True
            and all(r['device']=='meta' for r in meta[key]['tensors']), 'Non-meta full2B allocation observed')
    adapter=meta['constructor_adapter']
    require(adapter['calls']==scope['meta_only_constructor_adapter']['expected_calls']
        and adapter['device']=='meta' and adapter['restored'] is True
        and adapter['original_class_and_body_preserved'] is True and adapter['restored_before_tiny_sampling'] is True,
        'Original TE constructor/meta-device adaptation was not restored')
    require(3*2**30<meta['parameters']['logical_tensor_bytes']<5*2**30,'Full2B parameter geometry differs')
    from wcomr.mid_coverage import WC_FIELDS
    schemas=result['schemas']
    groups={'native','solver','buffers','owner_history','readout_history','calibrators','paired_inputs','conditions'}
    for key,schema in schemas.items():
        raw=json.dumps(schema,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        require(hashlib.sha256(raw).hexdigest()==key and schema['captured_before_pair'] is True
            and schema['any_meta_tensors'] is False and set(schema['native_field_names'])==set(WC_FIELDS)
            and set(schema['group_inventories'])==groups,'Incomplete or mixed S boundary schema')
        validate_inventory(schema)
        for value in schema['group_inventories'].values():validate_inventory(value)
        require(schema['logical_tensor_bytes']==sum(v['logical_tensor_bytes'] for v in schema['group_inventories'].values())
            and schema['logical_copy_guard_bytes']==8*schema['logical_tensor_bytes'],
            'Full boundary does not reconcile with the deployed copy guard')
    expected=[(flow,parent,step) for flow in (False,True) for parent in ('Shared25-C','F19-C')
              for step in scope['tiny_scope']['targets']]
    boundaries=result['before_pair_boundaries']
    require([(r['flow'],r['parent'],r['step']) for r in boundaries]==expected
        and all(r['schema_sha256'] in schemas for r in boundaries) and result['complete_tiny_CPU_paths']==4,
        'Complete four paths/all108 declared CPU boundaries required')
    require(all(result[k] is True for k in ('original_deployed_copy_guard_reconciled',
        'CPU_import_probes_restored_before_metadata_and_sampling','model_weight_loads_forbidden',
        'Hugging_Face_download_functions_blocked'))
        and all(result[k] is False for k in ('native_production_source_modified','actual_Cosmos_weights',
            'real_generated_video','CUDA_initialized','physical_GPU_or_RAM_peak_measured',
            'complete_S_GPU_entry_accepted','whole_S_quote_frozen'))
        and all(result[k]==0 for k in ('S_real_labels','GPU_submissions','new_GPUh','ledger_writes')),
        'S metadata CPU work exceeded or overstated its evidence scope')
    require(result['actual_platform']['system']=='Linux' and result['torch_version']=='2.7.1+cu128',
        'Actual registered Linux CPU runtime required')
    wall=(instant(state['FinishedAt'])-instant(state['StartedAt'])).total_seconds()
    require(0<result['CPU_wall_seconds']<=wall<=1810 and 0<result['peak_RSS_KiB']<8*2**20,
        'Original S resource CPU resource accounting differs')
    return dict(status='S_COMPLETE_OWNERSHIP_AND_FULL2B_META_CPU_ACCEPTED_NOT_GPU_CARD',passed=True,
        host=host,source_revision=revision,unit_controls=8,complete_tiny_CPU_paths=4,before_pair_boundaries=108,
        schemas=len(schemas),full2B_parameter_logical_bytes=meta['parameters']['logical_tensor_bytes'],
        full2B_buffer_logical_bytes=meta['buffers']['logical_tensor_bytes'],
        resources=dict(container_wall_seconds=wall,worker_wall_seconds=result['CPU_wall_seconds'],
            worker_CPU_seconds=result['CPU_seconds'],reaped_child_CPU_seconds=result['reaped_child_CPU_seconds'],
            parent_peak_RSS_GiB=result['peak_RSS_KiB']/2**20,allocated_vCPU_seconds_upper_bound=2*wall,
            staging_transport_git_CPU_unmetered=True),
        GPU_submissions=0,ledger_writes=0,S_real_labels=0,physical_GPU_or_RAM_peak_measured=False,
        complete_S_GPU_entry_accepted=False,whole_S_quote_frozen=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--host',choices=('two_card','four_card'),required=True)
    p.add_argument('--source-revision',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    require(not args.output.exists(),'Retain original resource acceptance')
    revision=subprocess.check_output(['git','rev-parse',args.source_revision+'^{commit}'],cwd=ROOT,text=True).strip()
    capture=json.loads(args.capture.read_text());scope=json.loads(subprocess.check_output(['git','show',revision+':'+SCOPE_R3],cwd=ROOT))
    result=accept(capture,scope,revision,args.host)
    cases=dict(live_container=lambda c:c['container_state'].update(Running=True),
        live_CLI=lambda c:c.update(original_CLI_live=True),
        GPU_exposed=lambda c:c['host_config'].update(DeviceRequests=[{}]),
        stale_source=lambda c:c.update(source_hashes_equal=False),
        skipped_unit=lambda c:c['result']['unit_controls'].update(skipped=1),
        missing_boundary=lambda c:c['result']['before_pair_boundaries'].pop(),
        weights_loaded=lambda c:c['result']['full2B_meta_architecture'].update(weights_loaded=True),
        path_resolved=lambda c:c['result']['full2B_meta_architecture'].update(checkpoint_paths_resolved=True),
        peak_claim=lambda c:c['result'].update(physical_GPU_or_RAM_peak_measured=True),
        whole_card_claim=lambda c:c['result'].update(complete_S_GPU_entry_accepted=True))
    rejected={}
    for name,mutate in cases.items():
        forged=copy.deepcopy(capture);mutate(forged);forged['result_sha256']=result_sha(forged['result'])
        try:accept(forged,scope,revision,args.host)
        except ValueError:rejected[name]=True
        else:raise ValueError('Forged S resource receipt accepted: '+name)
    result.update(capture_ref=str(args.capture),capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        rejection_controls=rejected,critical_source_sha256={n:hashlib.sha256(subprocess.check_output(
            ['git','show',revision+':'+n],cwd=ROOT)).hexdigest() for n in FILES+(SCOPE_R2,SCOPE_R3)})
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','host','schemas','full2B_parameter_logical_bytes','resources')}))


if __name__=='__main__':main()
