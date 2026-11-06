#!/usr/bin/env python3
"""All eight registered slots, original files, full vectors and memory evidence."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    p=argparse.ArgumentParser()
    for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
    args=p.parse_args();os.environ['CUDA_VISIBLE_DEVICES']=''
    import torch
    torch.cuda._lazy_init=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('E1 raw CPU audit forbids CUDA'))
    torch.set_num_threads(2)
    sys.path[:0]=[str(args.stage/'src'),str(args.project/'runtime'),
        str(args.project/'runtime/packages/cosmos-oss'),str(args.project/'runtime/packages/cosmos-cuda')]
    from wcomr.e1_diag8_production_r1 import RUN,CONFIG,sha,write,validate,validate_selected
    c,old,_=validate(args.project,args.stage);validate_selected(c,args.stage)
    from wcomr.e1_memory_diagnostic_sampling_r1 import audit_vectors
    from wcomr.mid_coverage import tree_digest
    root=args.project/'outputs'/RUN;supervisor=json.loads((root/'supervisor.json').read_text())
    assert supervisor['status']=='E1_DIAG8_EXITED_REQUIRES_COMPLETE_SCOPE_RAW_CPU_AUDIT'
    assert supervisor['config_sha256']==sha(args.stage/CONFIG)
    assert not Path('/proc/'+str(supervisor['pid'])).exists()
    slots=[];arms=[];loaded={};metadata=[];vector_files=set()
    for arm,process in zip(c['arms'],supervisor['arms']):
        assert arm['id']==process['id'] and len(arm['paths'])==process['planned_paths']
        path=root/arm['id']/'receipt.json'
        if not path.exists():
            arms.append({'arm':arm['id'],'status':'UNSTARTED_OR_FAILED_BEFORE_RECEIPT','planned_paths':len(arm['paths'])})
            slots.extend({**x,'arm':arm['id'],'status':'UNSTARTED_REGISTERED_SCOPE_RETAINED'} for x in arm['paths']);continue
        receipt=json.loads(path.read_text())
        assert sha(path)==process['receipt_sha256'] and receipt['source_revision']==supervisor['source_revision']
        assert receipt['arm']==arm and not Path('/proc/'+str(receipt['pid'])).exists()
        batch=receipt['batch'];rows={}
        for request in batch.get('requests',[]):
            for row in request['paths']:rows[(request['sample_name'],row['collect'])]=(request,row)
        valid=False
        if process['exit_code']==0:
            verdict=audit_vectors(batch,arm,root,torch.load,old['expected_real_shape'])
            assert receipt['status']=='E1_ARM_COMPLETE_REQUIRES_INDEPENDENT_CPU_AUDIT';valid=True
        else:verdict=None
        events=[];observer=root/arm['id']/'memory-observer.jsonl'
        if observer.exists():
            events=[json.loads(line) for line in observer.read_text().splitlines()]
            assert all(e['arm']==arm['id'] for e in events);metadata.extend(events)
        for declared in arm['paths']:
            key=(declared['sample_name'],declared['method']);pair=rows.get(key)
            slot={**declared,'arm':arm['id'],'status':'UNSTARTED_REGISTERED_SCOPE_RETAINED'}
            if pair:
                request,row=pair;slot.update(status='COMPLETE_NUMERIC_AUDITED' if valid else 'PARTIAL_OR_UNACCEPTED_ARM',
                    outcome=row.get('outcome'),solver_updates=len(row.get('guided_sha256',[])))
                if 'vector_artifact' in row:
                    art=row['vector_artifact'];v=Path(art['path']).resolve()
                    assert v.is_relative_to(root.resolve()) and sha(v)==art['sha256'] and v.stat().st_size==art['bytes']
                    vector_files.add(str(v));data=torch.load(v,map_location='cpu',weights_only=True)
                    assert len(data['guided'])==36 and set(data)=={'guided','final_latent'}
                    assert all(t.dtype==torch.float32 and list(t.shape)==old['expected_real_shape']
                        and bool(torch.isfinite(t).all()) for t in data['guided']+[data['final_latent']])
                    assert {k:tree_digest(v) for k,v in data.items()}==art['tensor_sha256']
                    assert [tree_digest(t) for t in data['guided']]==row['guided_sha256']
                    if valid:loaded[(arm['id'],*key)]=data
                if 'video_artifact' in row:
                    video=Path(row['video_artifact']['path']).resolve()
                    assert video.is_relative_to(root.resolve()) and sha(video)==row['video_artifact']['sha256']
                    assert video.stat().st_size==row['video_artifact']['bytes']
                    # Full original decoding, no VLM/human review or frame subsampling.
                    subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],check=True,
                        stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
                    details=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0',
                        '-show_entries','stream=width,height,nb_read_frames','-of','json',str(video)],text=True))['streams']
                    assert len(details)==1 and (details[0]['width'],details[0]['height'],int(details[0]['nb_read_frames']))==(768,432,93)
                    slot['video_all93_decoded']=True
            slots.append(slot)
        arms.append({'arm':arm['id'],'planned_paths':len(arm['paths']),'exit_code':process['exit_code'],
            'status':receipt['status'],'protected_capacity_failure':receipt.get('protected_capacity_failure',False),
            'error':receipt.get('error'),'whole_numeric_audit':verdict,'memory_events':len(events),
            'after_load_memory':receipt.get('after_load_memory')})
    comparisons=[]
    pairs=[('ORIGINAL_COLD','CPU_COLD'),('ORIGINAL_PREFIX','CPU_PREFIX'),
        ('ORIGINAL_COLD','ORIGINAL_PREFIX'),('CPU_COLD','CPU_PREFIX')]
    for a,b in pairs:
        for key,left in loaded.items():
            if key[0]!=a:continue
            right=loaded.get((b,*key[1:]));item={'arms':[a,b],'sample_name':key[1],'method':key[2],
                'status':'MISSING_COMPLETE_COUNTERPART'}
            if right:
                equality=[torch.equal(x,y) for x,y in zip(left['guided']+[left['final_latent']],right['guided']+[right['final_latent']])]
                item.update(status='DIRECT_FULL36_AND_FINAL_COMPARISON',equal=equality,
                    all_equal=all(equality))
            comparisons.append(item)
    assert len(slots)==8 and len(arms)==4
    actual={str(v.resolve()) for v in root.rglob('*.pt')};assert actual==vector_files
    value={'status':'E1_DIAG8_ALL_REGISTERED_SLOTS_RAW_CPU_AUDITED_NOT_METHOD_CONFIRMATION',
        'source_revision':supervisor['source_revision'],'planned_paths':8,'slots':slots,'arms':arms,
        'complete_numeric_paths':sum(x['status']=='COMPLETE_NUMERIC_AUDITED' for x in slots),
        'successful_storage_or_cold_prefix_comparisons':comparisons,'memory_events':metadata,
        'supervisor_sha256':sha(root/'supervisor.json'),'config_sha256':sha(args.stage/CONFIG),
        'CUDA_initialized':torch.cuda.is_initialized(),'scientific_quality_or_clean_speed_claim':False,
        'short_prefix_reproduces_old14_path_lifetime':False,'whole64_recovery_proven':False}
    assert not value['CUDA_initialized'];assert not (root/'raw-CPU-audit.json').exists()
    write(root/'raw-CPU-audit.json',value)
    print(json.dumps({'status':value['status'],'complete_numeric_paths':value['complete_numeric_paths'],'planned_paths':8}))


if __name__=='__main__':main()
