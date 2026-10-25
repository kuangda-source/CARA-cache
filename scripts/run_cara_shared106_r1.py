#!/usr/bin/env python3
"""One resident Cosmos, all106 frozen historical/boundary paths; no search."""
import argparse,json,os,sys,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--source-revision',required=True);p.add_argument('--gpu-uuid',required=True);a=p.parse_args()
 os.environ.update(WC_SCOUT_KIND='CAL12',HF_HUB_CACHE=str(a.project/'cache/huggingface/hub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
 sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.project/'runtime'),str(a.project/'runtime/packages/cosmos-oss'),str(a.project/'runtime/packages/cosmos-cuda')]
 from wcomr.policy_generator_r1.shared106_card import validate,read,sha,RUN,COUNTS,CONFIG
 c,reg,card=validate(a.project,a.stage)
 from wcomr.history104_storage_r2 import storage_for
 storage=storage_for(a.stage);storage.check()
 assert reg['source_revision']==a.source_revision
 auth=read(a.stage/'pg-GPU-authorization.json');out=a.project/'outputs'/RUN
 assert auth['gpu_uuid']==a.gpu_uuid==os.environ['CUDA_VISIBLE_DEVICES'] and os.environ['WC_SUPERVISOR_PID']==str(os.getppid())
 assert Path('/proc/self/fd/'+os.environ['WC_LOCK_FD']).resolve()==(a.project/'.sync/gpu-locks'/(a.gpu_uuid+'.lock')).resolve()
 from wcomr.policy_generator_r1.production_exclusive import runner_context_gate
 context=runner_context_gate(a.project,a.stage,a.gpu_uuid)
 import torch
 torch.set_num_threads(2)
 from cosmos_predict2.config import SetupArguments,InferenceArguments
 import cosmos_predict2.inference as im
 from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
 from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf
 from cosmos_oss.init import init_environment,init_output_dir,cleanup_environment
 from wcomr.runtime_config import install_core_inference_registration
 from wcomr.full_sampling import CompleteStateRoundtrip
 from wcomr.h0_mode import establish_shared_eval,verify_shared_eval
 from wcomr.drop1_full18_r1 import MODE_REF,STRATEGY
 from wcomr import clean_speed20_r1 as clean
 from wcomr.policy_generator_r1.production_sampling import execute,complete_request_seconds
 from wcomr.policy_generator_r1.exploration_requests import Requests
 from wcomr.policy_generator_r1.shared106_collection import collect,gather

 from wcomr.policy_generator_r1.interval_grammar import Profile
 from wcomr.policy_generator_r1.continuation_preparation import TIME_BOUNDARY
 from wcomr.gpu_budget_pool_v2 import atomic_json,process_identity
 from four_card_policy_assets_port_r1 import reconstruct
 from wcomr.policy_generator_r1.production_evidence import metric_resource_identity
 base,parent,inputs,*_=reconstruct(a.stage);calibration,specs,*_=inputs
 fit=card['CAL_FIT_members'];assert len(fit)==4
 samples=dict(zip(fit,[InferenceArguments(**r) for r in base['requests']]))
 pp=dict(card['profile']);pp['protected_dense']=tuple(pp['protected_dense']);pp['alpha_candidates']=tuple(pp['alpha_candidates']);profile=Profile(**pp)
 setup=SetupArguments(**{**read(a.stage/'configs/f1_setup.json'),'keep_going':True,'worldcache_enabled':True,'output_dir':str(out)})
 assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
 state=dict(status='SHARED106_MODEL_LOADING',pid=os.getpid(),source_revision=a.source_revision,config_sha256=sha(a.stage/CONFIG),
  registration_sha256=sha(a.stage/'registration.json'),scope_counts=COUNTS,model_loads=0,started_unix=time.time())
 def save(batch=None):
  if batch is not None:state['batch']=batch;state['status']=batch['status']
  atomic_json(out/'runner.json',state)
  rows=state.get('batch',{}).get('rows',[])
  atomic_json(out/'runner-health.json',dict(phase=state['status'],registered_paths=106,completed_paths=sum(r['status']=='COMPLETE' for r in rows),
   running_paths=sum(r['status']=='RUNNING' for r in rows),failed_paths=sum(r['status']=='TECH_FAILED' for r in rows)))
 save();init_environment();init_output_dir(out,profile=False)
 try:
  install_core_inference_registration(setup.model,setup.experiment)
  t=time.perf_counter();inference=im.Inference(setup);torch.cuda.synchronize();state.update(model_loads=1,load_seconds=time.perf_counter()-t)
  model=inference.pipe.model;net=model.net;mode=establish_shared_eval(net,read(a.stage/MODE_REF)['module_types']);verify_shared_eval(net,mode)
  assert torch.__version__=='2.7.1+cu128' and torch.cuda.get_device_capability()==(8,9) and len(net.blocks)==28
  settings=parent['historical_wc_settings'];wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
  initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1));origin=initial.fingerprint();versions=[(v,v._version) for v in net.parameters()]
  adapter=Requests(inference=inference,samples=samples,profile=profile,roles=card['roles'],schedules=card['schedules'],common={})
  def request(slot,policy,directory):
   storage.check()  # Outside complete_request_seconds and all timed sampling.
   initial.restore();assert initial.fingerprint()==origin;verify_shared_eval(net,mode)
   kw=dict(runtime=a.project/'runtime',wc=wc,rf=rf,settings=settings,calibration=calibration,specs=specs[STRATEGY],inference_module=im,output=directory,expected_shape=parent['expected_real_shape'],audit=slot['section']=='DIAGNOSTIC')
   adapter.common={k:v for k,v in kw.items() if k!='output'}
   result=adapter(slot,directory)
   assert all(v._version==ver for v,ver in versions)
   return result
  batch=collect(card,out,request,save)
  verified=gather(card,batch,out)
  atomic_json(out/'collection-verified.json',dict(status='COMPLETE106_NUMERICAL_ORIGINALS_VERIFIED',controls=verified['controls'],before_GPU_release=True))
  initial.restore();assert initial.fingerprint()==origin
 finally:cleanup_environment();state['ended_unix']=time.time();save()
if __name__=='__main__':main()
