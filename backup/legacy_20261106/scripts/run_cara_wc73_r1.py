"""One registered GPU phase; three-arm gate is evaluated before A calibration."""
import argparse,json,os,sys,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 for k in ('project','stage'):p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--source-revision',required=True);p.add_argument('--gpu-uuid',required=True);a=p.parse_args()
 sys.path[:0]=[str(a.stage/'src'),str(a.stage/'scripts'),str(a.project/'runtime'),str(a.project/'runtime/packages/cosmos-oss'),str(a.project/'runtime/packages/cosmos-cuda')]
 from wcomr.wc73_execution_r1 import validate,read,RUN,RA
 from wcomr.gpu_budget_pool_v2 import atomic_json
 from wcomr.history104_storage_r2 import storage_for
 c,reg,auth=validate(a.project,a.stage);phase=auth['phase'];out=a.project/'outputs'/RUN
 storage=storage_for(a.stage);storage.check()
 assert reg['source_revision']==a.source_revision and auth['gpu_uuid']==a.gpu_uuid==os.environ['CUDA_VISIBLE_DEVICES']
 assert os.environ['WC_SUPERVISOR_PID']==str(os.getppid())
 assert Path('/proc/self/fd/'+os.environ['WC_LOCK_FD']).resolve()==(a.project/'.sync/gpu-locks'/(a.gpu_uuid+'.lock')).resolve()
 from wcomr.wc73_exclusive_r1 import runner_context_gate
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
 from wcomr.simple26d_r1 import MODE_REF
 from wcomr.wc_time_card_r1 import Requests
 from wcomr.wc_time_collection_r1 import collect_phase
 from wcomr.wc_time_diagnostics_r1 import verify
 setup=SetupArguments(**{**read(a.stage/'configs/f1_setup.json'),'keep_going':True,'worldcache_enabled':True,'output_dir':str(out)})
 assert not setup.disable_guardrails and not setup.use_torch_compile and not setup.offload_diffusion_model
 samples={r['name']:InferenceArguments(**r) for r in c['requests']}
 state=dict(phase=phase,status='MODEL_LOADING',started_unix=time.time(),source_revision=reg['source_revision'])
 def save(batch=None):
  if batch is not None:state.update(status=batch['status'],batch=batch);atomic_json(out/(phase+'-collection.json'),batch)
  atomic_json(out/(phase+'-runner.json'),state)
 save();init_environment();init_output_dir(out,profile=False)
 try:
  install_core_inference_registration(setup.model,setup.experiment)
  t=time.monotonic();inference=im.Inference(setup);torch.cuda.synchronize();state['load_seconds']=time.monotonic()-t
  model=inference.pipe.model;net=model.net
  mode=establish_shared_eval(net,read(a.stage/MODE_REF)['module_types']);verify_shared_eval(net,mode)
  assert torch.__version__=='2.7.1+cu128' and list(torch.cuda.get_device_capability())==read(a.stage/'plans/cara_wc_time_protocol_r1_20261027/EXECUTION_PLAN.json')['host_profiles'][auth['host']]['capability'] and len(net.blocks)==28
  settings=c['roles']['WC_README_U36']['settings'];wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
  initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1));origin=initial.fingerprint();versions=[(v,v._version) for v in net.parameters()]
  common=dict(runtime=a.project/'runtime',wc=wc,rf=rf,inference_module=im,expected_shape=read(a.stage/'configs/wc_ra_comparison_production_r2_20261010.json')['expected_real_shape'])
  frozen=read(out/'frozen-selection.json') if phase=='B' else None
  adapter=Requests(inference=inference,samples=samples,card=c,common=common,ra_binding=read(a.stage/RA),host=auth['host'],frozen=frozen)
  def before(slot):
   storage.check();initial.restore();assert initial.fingerprint()==origin;verify_shared_eval(net,mode);assert all(v._version==ver for v,ver in versions)
  collect_phase(adapter,phase,out/phase,before_request=before,save=save,after_diagnostics=verify)
  initial.restore();assert initial.fingerprint()==origin
 finally:cleanup_environment();state['ended_unix']=time.time();save()
if __name__=='__main__':main()
