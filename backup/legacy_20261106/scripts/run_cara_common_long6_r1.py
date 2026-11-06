#!/usr/bin/env python3
"""One resident Cosmos, isolated four-parent B1 plus actual gain replay."""
import argparse,json,os,sys,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 for n in ('project','stage'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--source-revision',required=True);p.add_argument('--gpu-uuid',required=True);a=p.parse_args()
 os.environ.update(WC_SCOUT_KIND='CAL12',HF_HUB_CACHE=str(a.project/'cache/huggingface/hub'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
 sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.project/'runtime'),str(a.project/'runtime/packages/cosmos-oss'),str(a.project/'runtime/packages/cosmos-cuda')]
 from wcomr.common_long_card_r1 import validate,read,sha,RUN,COUNTS,CONFIG
 c,reg,manifest=validate(a.project,a.stage)
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
 from wcomr.scout_common_long_r1 import execute
 import contextlib
 from wcomr.common_long_collection_r1 import collect
 from wcomr.scout_parent_v22 import DenseObserver
 from wcomr.scout_readout_v22 import PARENT_FINGERPRINT
 from wcomr.cfg_guided_w1_forward import compile_collection
 from wcomr.gpu_budget_pool_v2 import atomic_json
 from four_card_policy_assets_port_r1 import reconstruct
 base,parent,inputs,tables,prior=reconstruct(a.stage);calibration,specs,*_=inputs
 raw=manifest['requests']
 samples={r['name']:InferenceArguments(**r) for r in raw}
 assert list(samples)==[r['name'] for r in manifest['requests']]
 setup=SetupArguments(**{**read(a.stage/'configs/f1_setup.json'),'keep_going':True,'worldcache_enabled':True,'output_dir':str(out)})
 assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
 state=dict(status='COMMON_LONG6_MODEL_LOADING',pid=os.getpid(),source_revision=a.source_revision,config_sha256=sha(a.stage/CONFIG),
  registration_sha256=sha(a.stage/'registration.json'),scope_counts=COUNTS,model_loads=0,started_unix=time.time())
 def save(batch=None):
  if batch is not None:state['batch']=batch;state['status']=batch['status']
  atomic_json(out/'runner.json',state)
  rows=state.get('batch',{}).get('rows',[])
  atomic_json(out/'runner-health.json',dict(phase=state['status'],registered_paths=6,completed_paths=sum(r['status']=='COMPLETE' for r in rows),
   running_paths=sum(r['status']=='RUNNING' for r in rows),failed_paths=sum(r['status']=='TECH_FAILED' for r in rows)))
 save();init_environment();init_output_dir(out,profile=False)
 try:
  install_core_inference_registration(setup.model,setup.experiment)
  t=time.perf_counter();inference=im.Inference(setup);torch.cuda.synchronize();state.update(model_loads=1,load_seconds=time.perf_counter()-t)
  model=inference.pipe.model;net=model.net;mode=establish_shared_eval(net,read(a.stage/MODE_REF)['module_types']);verify_shared_eval(net,mode)
  assert torch.__version__=='2.7.1+cu128' and torch.cuda.get_device_capability()==tuple(c['compute_capability']) and len(net.blocks)==28
  settings=parent['historical_wc_settings'];wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
  initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1));origin=initial.fingerprint();versions=[(v,v._version) for v in net.parameters()]
  schemas={}
  def request(prompt,enabled,sink,directory):
   storage.check();initial.restore();assert initial.fingerprint()==origin;verify_shared_eval(net,mode)
   result=execute(inference,samples[prompt],enabled=enabled,timing_host=c['host'],
    context=(prompt,c['model_identity'],PARENT_FINGERPRINT),sink=sink,copy_cap=c['logical_copy_cap_bytes'],
    table_parameters=tables,previous_parameters=prior,runtime=a.project/'runtime',wc=wc,rf=rf,
    settings=settings,calibration=calibration,specs=specs[STRATEGY],inference_module=im,
    output=directory,expected_shape=parent['expected_real_shape'],audit=True)
   assert all(v._version==ver for v,ver in versions)
   return result
  batch=collect(out,manifest,request,byte_limit=c['asset_byte_limit'],check_space=storage.check,save=save)
  atomic_json(out/'collection-verified.json',dict(status=batch['status'],scope_counts=COUNTS,before_GPU_release=True,real_model=True,video_quality_claim=False))
  initial.restore();assert initial.fingerprint()==origin;verify_shared_eval(net,mode)
 finally:cleanup_environment();state['ended_unix']=time.time();save()
if __name__=='__main__':main()
