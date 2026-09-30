"""Offline MUSIQ evaluation of all original CAL8 WC/scalar video pairs."""
import argparse, hashlib, json, os, signal, sys, time, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.imaging_quality import score_complete_frames, paired_summary
from wcomr.replay_results import summarize

p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--gpu-uuid',required=True);p.add_argument('--receipt',type=Path,required=True)
a=p.parse_args();project=a.project.resolve();started=time.time()
r={'pid':os.getpid(),'status':'INITIALIZING','gpu_uuid':a.gpu_uuid,'pairs':[],'source_sha256':{}}
def save():
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    tmp=a.receipt.with_suffix('.tmp');tmp.write_text(json.dumps(r,indent=2)+'\n');tmp.replace(a.receipt)
def load_bound(path,digest):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Input hash mismatch: '+str(path))
    return json.loads(data)
def terminate(*args):raise SystemExit('Evaluator supervisor SIGTERM')
signal.signal(signal.SIGTERM,terminate);save()
try:
    protocol=json.loads((project/'manifests/w1_imaging_protocol.json').read_text());r['protocol']=protocol
    if protocol['status']!='FROZEN_BEFORE_IMAGING_SCORES' or protocol['max_gpu_seconds']!=600:raise ValueError('Protocol/cap differs')
    for path in ['scripts/run_w1_imaging.py','scripts/supervise_f1.py','src/wcomr/imaging_quality.py','src/wcomr/replay_results.py','manifests/w1_imaging_protocol.json']:
        r['source_sha256'][path]=hashlib.sha256((project/path).read_bytes()).hexdigest()
    reference=load_bound(project/protocol['reference_receipt'],protocol['reference_sha256'])
    candidate=load_bound(project/protocol['candidate_receipt'],protocol['candidate_sha256'])
    validated=summarize(candidate,reference=reference)
    if [row['name'] for row in validated['samples']]!=protocol['samples']:raise ValueError('Original8 sample membership differs')
    import torch, av, inspect, importlib.metadata
    from pyiqa.archs.musiq_arch import MUSIQ
    checkpoint=Path(protocol['checkpoint_relative_to_home']).expanduser()
    if hashlib.sha256(checkpoint.read_bytes()).hexdigest()!=protocol['checkpoint_sha256']:raise ValueError('MUSIQ checkpoint differs')
    architecture=Path(inspect.getfile(MUSIQ))
    if hashlib.sha256(architecture.read_bytes()).hexdigest()!=protocol['architecture_source_sha256']:raise ValueError('MUSIQ architecture differs')
    if importlib.metadata.version('pyiqa')!=protocol['pyiqa_version']:raise ValueError('pyiqa version differs')
    torch.set_num_threads(2);torch.manual_seed(0);torch.cuda.manual_seed_all(0)
    torch.backends.cudnn.benchmark=False;torch.backends.cudnn.deterministic=True
    model=MUSIQ(pretrained_model_path=str(checkpoint)).cuda().eval()
    r['setup']={'torch':torch.__version__,'pyiqa':importlib.metadata.version('pyiqa'),'device':torch.cuda.get_device_name(0),'model_eval':not model.training,'preprocessing':'longer512 bilinear align_cornersFalse antialiasFalse /255','microbatch':1,'seed':0,'normalized_score':'mean all93 frame raw scores /100'}
    r['status']='SCORING';save()
    def score_video(arm):
        path=Path(arm['video_path'])
        if hashlib.sha256(path.read_bytes()).hexdigest()!=arm['video_sha256']:raise ValueError('Video hash differs')
        with av.open(str(path)) as video:
            frames=((f.to_ndarray(format='rgb24'),f.pts,str(f.time_base)) for f in video.decode(video=0))
            result=score_complete_frames(frames,model,'cuda')
        result['video_sha256']=arm['video_sha256'];return result
    for old,new in zip(reference['cases'],candidate['cases']):
        name=new['name'];r['current_sample']=name;row={'name':name,'status':'SCORING'};r['pairs'].append(row);save()
        if new['scalar_off']['outcome']!='ACCEPTED':row['status']=new['scalar_off']['outcome'];save();continue
        if old['off']['outcome']!='ACCEPTED':raise ValueError('Official reference not accepted')
        print('Scoring',name,flush=True);pair_start=time.time()
        row['reference']=score_video(old['off']);row['candidate']=score_video(new['scalar_off'])
        if row['reference']['pts']!=row['candidate']['pts']:raise ValueError('Paired PTS differs')
        row['delta']=row['candidate']['normalized_score']-row['reference']['normalized_score'];row['seconds']=time.time()-pair_start;row['status']='SCORED';save()
        print('Completed',name,'delta',row['delta'],'seconds',row['seconds'],flush=True)
    r['summary']=paired_summary(r['pairs'],protocol['samples']);r['status']='W1_IMAGING_ALL_ORIGINAL8_ATTEMPTED'
    r['peak_memory']={'allocated_bytes':torch.cuda.max_memory_allocated(),'reserved_bytes':torch.cuda.max_memory_reserved()}
except BaseException as e:
    r.update(status='TECH_BLOCKED',error_type=type(e).__name__,error=str(e));raise
finally:
    r['wall_seconds']=time.time()-started;save()
