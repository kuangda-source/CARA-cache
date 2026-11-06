#!/usr/bin/env python3
"""Released-GPU full sixteen-pair raw tensor and original-parent CPU audit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path.insert(0,str(args.stage/'src'))
    from wcomr.cfg_real_paired_interface_production import validate,validate_selected
    c,_=validate(args.project,args.stage);validate_selected(c,args.project,args.stage)
    import torch
    assert not torch.cuda.is_initialized()
    torch.set_num_threads(2)
    def forbidden(*a,**kw):raise RuntimeError('Raw interface CPU audit forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.cfg_paired_interface_sampling import verify_batch
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import probe_video,decoded_video
    out=args.project/'outputs'/c['execution_run_id'];supervisor=json.loads((out/'supervisor.json').read_text())
    assert supervisor['exit_code']==0 and supervisor['run_id']==c['execution_run_id']
    assert not any(Path('/proc/'+str(supervisor[k])).exists() for k in ('pid','child_pid'))
    source=out/'diagnostic/receipt.json';r=json.loads(source.read_text());state=r['teacher'];started=time.perf_counter()
    assert r['config']==c and r['source_revision']==supervisor['source_revision']
    assert r['status']=='REAL_PAIRED_INTERFACE_GPU_COMPLETE_REQUIRES_RAW_CPU_AUDIT'
    verdict=verify_batch(state);rows=state['parents'][1]['origin']['pairs'];tensors={};files=[]
    for row in rows:
        a=row['artifact'];path=Path(a['path']).resolve()
        assert path.is_relative_to((out/'diagnostic').resolve()) and path.suffix=='.pt'
        raw_bytes=path.read_bytes();assert len(raw_bytes)==a['bytes'] and hashlib.sha256(raw_bytes).hexdigest()==a['sha256']
        v=torch.load(path,weights_only=True,map_location='cpu');assert set(v)=={'conditional','unconditional','guided'}
        assert all(x.dtype==torch.float32 and list(x.shape)==c['expected_real_shape'] and bool(torch.isfinite(x).all()) for x in v.values())
        assert all(tree_digest(v[k])==a['tensor_sha256'][k] for k in v)
        assert torch.equal(v['conditional']+7*(v['conditional']-v['unconditional']),v['guided'])
        if row['action'] in tensors:assert all(torch.equal(tensors[row['action']][k],v[k]) for k in v)
        else:tensors[row['action']]=v
        assert row['block_visits']==([2,2]+[0]*26 if row['action']=='CC' else [2]*28)
        assert len(row['origin_components'])==len(row['pair_end_components'])==c['expected_real_components']
        files.append({'label':row['label'],'path':str(path),'bytes':a['bytes'],'sha256':a['sha256'],
                      'tensor_sha256':a['tensor_sha256']})
    assert len(rows)==16 and len(files)==16
    actual={str(p.resolve()) for p in (out/'diagnostic').rglob('*.pt')}
    assert actual=={x['path'] for x in files}
    videos=[]
    for parent in state['parents']:
        a=parent['artifact'];path=Path(a['path']).resolve();assert path.is_relative_to((out/'diagnostic').resolve())
        assert path.stat().st_size==a['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==a['sha256']
        probe=probe_video(path);count=0;decoded_hash=hashlib.sha256()
        with decoded_video(path) as frames:
            for frame,pts,base in frames:
                assert list(frame.shape)==[432,768,3]
                decoded_hash.update(frame.tobytes());count+=1
        assert count==93 and probe['fps']==16
        videos.append({'path':str(path),'sha256':a['sha256'],'probe':probe,'all_frames_shape':[count,432,768,3],
            'decoded_RGB_SHA':decoded_hash.hexdigest(),'fps':probe['fps']})
    assert videos[0]['sha256']==videos[1]['sha256'] and not torch.cuda.is_initialized()
    assert videos[0]['decoded_RGB_SHA']==videos[1]['decoded_RGB_SHA']
    result={'status':'REAL_PAIRED_INTERFACE_COMPLETE_RAW_CPU_AUDIT_NOT_ENDPOINT_OR_POLICY',
        'source_revision':r['source_revision'],'run_id':c['execution_run_id'],'config_sha256':hashlib.sha256((args.stage/'teacher-config.json').read_bytes()).hexdigest(),
        'runner_receipt_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'complete_comparisons':8,'complete_local_pairs':16,
        'actual_FP32_tensors_reconstructed':48,'full_state_components':c['expected_real_components'],
        'direct_tensor_order_observer_and_repeat_equal':True,'actual_FP32_guided_expression_equal':True,
        'full_parent_parity':verdict['full_parent_parity'],'artifacts':files,'videos':videos,
        'local_instrumented_costs':[{'label':x['label'],'action':x['action'],'order':x['order'],'observers':x['observers'],
            'current_velocity_instrumented_wall_seconds':x['current_velocity_instrumented_wall_seconds'],
            'memory_before':x['memory_before_core'],'memory_after':x['memory_after_core']} for x in rows],
        'clean_deployment_latency_claim':False,'endpoint_labels':0,'future_cost_labels':0,'candidate_full_sampler_policy_claim':False,
        'CPU_wall_seconds':time.perf_counter()-started,'CUDA_initialized':False,'GPU_submissions':0}
    assert not args.output.exists();args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','complete_local_pairs','actual_FP32_tensors_reconstructed','CPU_wall_seconds')}))


if __name__=='__main__':main()
