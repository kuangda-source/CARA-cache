"""Supplementary first registered window only; whole24 audit stays queued."""
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    code=r'''import hashlib,json,os,pathlib,sys,time
os.environ['CUDA_VISIBLE_DEVICES']=''
project=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=project/'.sync/wc-e4c-source-age-selected-r1-20261011';out=project/'outputs/wc-e4c-matched-p-d-age124-offon4-suffix16-r1/model'
c=json.loads((stage/'e4c-source-age-config.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert {n:sha(stage/n) for n in c['payload_sha256']}==c['payload_sha256']
scope=json.loads((stage/c['scope_ref']).read_text());event=scope['events'][0]
assert event['sample_name']=='av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632' and event['birth_step']==13 and event['phase']=='early'
receipt=json.loads((out/'receipt.json').read_text());assert receipt['pid']==4075494 and receipt['source_revision']=='6a5910ce07dd7cb6896f57de7f8827c9583f07bc'
assert pathlib.Path('/proc/4075494').exists() and pathlib.Path('/proc/4075406').exists()
budget_sha=sha(project/'reports/budget.json');sample=event['sample_name'];directory=out/sample/'source-age'/event['id']
import torch;torch.set_num_threads(2)
def forbidden(*a,**k):raise RuntimeError('First-window reader forbids CUDA/downloads')
torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
sys.path.insert(0,str(stage/'src'));from wcomr.mid_coverage import tree_digest
files=[]
def load(path):
 assert path.resolve().is_relative_to(out.resolve());before=sha(path);size=path.stat().st_size
 x=torch.load(path,map_location='cpu',weights_only=True)
 assert sha(path)==before and path.stat().st_size==size
 files.append({'path':str(path),'sha256':before,'bytes':size,'tensor_sha256':{k:tree_digest(v) for k,v in x.items()}})
 return x
shape=[1,16,24,54,96]
def geometry(values):
 assert all(v.dtype==torch.float32 and list(v.shape)==shape and v.device.type=='cpu' and torch.isfinite(v).all() for v in values)
parent_row=receipt['batch']['requests'][0]['paths'][0];assert parent_row['status']=='COMPLETE_PARENT_PATH' and not parent_row['collect']
parent=load(pathlib.Path(parent_row['vector_artifact']['path']));assert files[-1]['sha256']==parent_row['vector_artifact']['sha256']
assert len(parent['guided'])==36;geometry(parent['guided']+[parent['final_latent']])
suffixes={};equalities=0
for label in scope['suffix_arms']:
 x=load(directory/label/'suffix.pt');assert set(x)=={'guided','final_latent'} and len(x['guided'])==5;geometry(x['guided']+[x['final_latent']]);suffixes[label]=x
for label in scope['suffix_arms'][:2]:
 assert all(torch.equal(a,b) for a,b in zip(suffixes[label]['guided'],parent['guided'][12:17]));equalities+=5
assert all(torch.equal(a,b) for a,b in zip(suffixes['POLICY_REPEAT1']['guided']+[suffixes['POLICY_REPEAT1']['final_latent']],suffixes['POLICY_REPEAT2']['guided']+[suffixes['POLICY_REPEAT2']['final_latent']]));equalities+=6
points=[]
for source in ('P','D'):
 for age in (1,2,4):
  x=load(directory/source/(str(age)+'.pt'));assert set(x)=={'C','DENSE_SAME_STATE','candidate_latent','timestep'}
  assert len(x['C'])==len(x['DENSE_SAME_STATE'])==2;geometry(list(x['C'])+list(x['DENSE_SAME_STATE'])+[x['candidate_latent']])
  ec,eu=[a-b for a,b in zip(x['C'],x['DENSE_SAME_STATE'])];mse=(8*ec-7*eu).double().square().mean().item()
  guided=x['C'][0]+7*(x['C'][0]-x['C'][1]);assert torch.equal(guided,suffixes[source+'_BIRTH_C4']['guided'][age]);equalities+=1
  points.append({'source':source,'age':age,'registered_step':13+age,'guided_MSE':mse,'branch_MSE':[e.double().square().mean().item() for e in (ec,eu)],'candidate_latent_sha256':tree_digest(x['candidate_latent']),'actual_timestep':x['timestep'].tolist()})
pairs=[]
for age in (1,2,4):
 p,d=[next(x for x in points if x['source']==source and x['age']==age) for source in ('P','D')]
 assert p['actual_timestep']==d['actual_timestep']
 pairs.append({'age':age,'P_MSE':p['guided_MSE'],'D_MSE':d['guided_MSE'],'ratio_P_over_D':p['guided_MSE']/d['guided_MSE'] if d['guided_MSE'] else None,'each_arm_own_later_state':True})
assert len(files)==11 and equalities==22 and not torch.cuda.is_initialized()
assert sha(project/'reports/budget.json')==budget_sha
print(json.dumps({'status':'E4C_FIRST_FIXED_WINDOW_ACTUAL_TENSORS_READ_ONLY_NOT_WHOLE24_ACCEPTANCE','registered_scope':scope['scope_counts'],'event':event,'actual_loaded_files':files,'actual_direct_comparisons':equalities,'points':points,'matched_source_age_pairs':pairs,'completed_point_tensor_reads':6,'whole_registered_points':24,'complete_parent_and_all_event_metadata_still_pending':True,'unread_18_points_not_negative_results':True,'no_endpoint_quality_or_clean_latency_claim':True,'teacher_restore_metadata_not_independently_accepted_before_whole_receipt':True,'GPU_submissions':0,'ledger_written':False,'budget_sha256':budget_sha,'CUDA_initialized':False,'observed_unix':time.time()}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen',
        '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-3500:])
    v=json.loads(call.stdout);target=root/'reports/wc_e4c_first_fixed_window_actual_tensor_reads_cpu_r1_20261011.json';assert not target.exists()
    target.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':v['status'],'actual_direct_comparisons':v['actual_direct_comparisons'],'matched_source_age_pairs':v['matched_source_age_pairs']}))


if __name__=='__main__':main()
