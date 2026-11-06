"""All 28 formal videos x4 CPU metrics, bound original constructors and sources."""
import argparse,os,json,sys,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 b=json.loads((a.stage/'reports/cara_CAL66_quality_binding_20261025.json').read_text());root=Path(b['registration']['stage'])
 sys.path[:0]=[str(root/'src'),str(root/'scripts')]
 if b.get('dependency_overlay'):sys.path.insert(0,str(b['dependency_overlay']))
 assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
 import torch
 torch.set_num_threads(4);assert not torch.cuda.is_initialized()
 from wcomr.policy_generator_r1.p2_quality_entry import original_factory,validate_sources_and_decoder
 from wcomr.automatic_quality_batch_r1 import validate_result
 from wcomr.automatic_quality_r1 import sampling_spec,text_sha
 from wcomr.gpu_budget_pool_v2 import atomic_json,sha
 from wcomr.policy_generator_r1.p2_quality_entry import digest
 factory=original_factory(stage=root,resources=b['resources'],acceptance=b['acceptance'],registration=b['registration'],identity=b['identity'],torch=torch,device='cpu')
 state=json.loads((a.output/'B-collection.json').read_text());card=json.loads((a.stage/'plans/cara_wc_time_protocol_p0_20261027/CONTROL_IDENTITY_MATRIX.yaml').read_text());members={x['name']:x for x in card['requests']}
 videos=[r for r in state['rows'] if r['slot']['section']=='B_QUALITY'];assert len(videos)==28 and all(r['status']=='COMPLETE' for r in videos)
 rows=[];progress=dict(status='RUNNING',expected=112,rows=rows,started_unix=time.time());dest=a.output/'quality';dest.mkdir(exist_ok=False)
 for dim in ('MUSIQ_LONGER512','subject_consistency','motion_smoothness','dynamic_degree'):
  with factory(dim) as scorer:
   for r in videos:
    s=r['slot'];member=members[s['scene']];path=r['result']['video_path']
    row=dict(case_id=s['scene'],method=s['id'],dimension=dim,seed=s['seed'],prompt=member['prompt'],prompt_sha256=text_sha(member['prompt']),video_path=path,video_sha256=sha(path),scorer_fingerprint=digest(b['identity']),expected_sampling=sampling_spec(dim),input_status='READY_TO_SCORE')
    result=scorer.score(row);atomic_json(dest/(str(len(rows))+'.raw.json'),result);validate_result(row,result);validate_sources_and_decoder(b['identity'],result)
    rows.append(dict(planned=row,status='SCORED',result=result));atomic_json(a.output/'B-quality-progress.json',progress)
 assert len(rows)==112 and not torch.cuda.is_initialized();progress.update(status='COMPLETE112',ended_unix=time.time(),CUDA_initialized=False);atomic_json(a.output/'B-quality.json',progress)
if __name__=='__main__':main()
