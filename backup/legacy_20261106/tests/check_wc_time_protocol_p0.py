"""Pinned sampler/native/WC bodies; declared tiny CPU weights/decoder/writer."""
import ast,copy,importlib.util,inspect,json,os,tempfile,time,types,hashlib,sys
from pathlib import Path
import numpy as np
import torch
from wcomr import clean_speed20_r1 as clean
from wcomr.wc_time_protocol_p0 import installed_timing,compile_wc_adapter,BoundaryClock
from wcomr.full_sampling import CompleteStateRoundtrip
ROOT=Path(__file__).resolve().parents[1]
def load(name):
 s=importlib.util.spec_from_file_location(name,ROOT/'tests'/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def body(inference,samples,wc,settings,inference_module,mode_setup,kernel,flow,runtime):
 net=inference.pipe.model.net;model=inference.pipe.model
 initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
 frames=[];writer=inference_module.save_img_or_video;results={};proofs=[]
 # Load the actual helper omitted by the older CPU fixture.
 fixture=load('check_full_sampling');fixture.load_functions(Path(runtime)/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py',['compute_saliency_map'],vars(wc))
 allD,proof=compile_wc_adapter(runtime,wc,force_full=True);proofs.append(proof)
 port,proof=compile_wc_adapter(runtime,wc,paper_port=True);proofs.append(proof)
 settings={**settings,'worldcache_rel_l1_thresh':.06,'worldcache_flow_scale':2.,'worldcache_saliency_weight':1.}
 def save(video,path,fps):frames.append(np.array(video,copy=True));return writer(video,path,fps)
 with tempfile.TemporaryDirectory(prefix='wc-time-p0-') as tmp,clean.patched(inference_module,'save_img_or_video',save):
  for label,method,module,timed in [('NATIVE_OFF','NATIVE',wc,False),('NATIVE_ON','NATIVE',wc,True),('ALLD_OFF','WC',allD,False),('ALLD_ON','WC',allD,True),('README_OFF','WC',wc,False),('README_ON','WC',wc,True),('PORT_ON','WC',port,True)]:
   initial.restore();before=torch.get_rng_state().clone();sync=[]
   kw=dict(runtime=runtime,wc=module,rf=None,settings=({**settings,'worldcache_rel_l1_thresh':.08,'worldcache_saliency_weight':.12,'worldcache_flow_scale':.5} if label=='PORT_ON' else settings),calibration=None,specs={},inference_module=inference_module,expected_shape=[1,2048,2,8,8],audit=True,output=Path(tmp)/label)
   if timed:
    with installed_timing(model,runtime,lambda:sync.append(1)) as c:r=clean.execute(inference,samples[0],method,**kw)
    r['time_protocol']=c.receipt();assert len(sync)==2 and r['time_protocol']['T_DD']>0
   else:r=clean.execute(inference,samples[0],method,**kw)
   assert r['status']=='COMPLETE' and r['solver_steps']==r['guided_pairs']==36
   if label=='PORT_ON':assert net.worldcache_saliency_weight==.12 and net.worldcache_flow_scale==.5 and net.worldcache_rel_l1_thresh==.08
   results[label]=(r,frames[-1].copy(),torch.get_rng_state().clone())
  for a,b in [('NATIVE_OFF','NATIVE_ON'),('ALLD_OFF','ALLD_ON'),('README_OFF','README_ON'),('NATIVE_ON','ALLD_ON')]:
   x,y=results[a],results[b]
   assert torch.equal(x[0]['final_latent'],y[0]['final_latent']),(a,b)
   assert all(torch.equal(u,v) for u,v in zip(x[0]['guided'],y[0]['guided'])),(a,b)
   assert np.array_equal(x[1],y[1]) and torch.equal(x[2],y[2]),(a,b)
  assert results['ALLD_ON'][0]['actions']==['DD']*36
  initial.restore()
  with installed_timing(model,runtime,lambda:None) as clock,clean.patched(inference,'generate',lambda *a,**kw:[]):
   r=clean.execute(inference,samples[0],'NATIVE',**{**kw,'output':Path(tmp)/'refusal','wc':wc})
  assert r['status']=='TEXT_REJECTED' and clock.receipt()['T_DD'] is None
 initial.restore()
 return [dict(flow=flow,complete_tiny_paths=7,true_native_forward=True,three_roles=['Native','WC_wrapper_allD','WC_README'],
   Native_WC_allD_guided_latent_RGB_RNG_equal=True,timing_on_off_all_three_equal=True,
   two_boundary_sync_only=True,refusal_null_T_DD=True,port_runs_CPU_only=True,port_actual_parameter_routing=True,proofs=proofs,
   actual_Cosmos_weights=False,real_encoded_video=False,GPU_parity=False)]

def main(runtime):
 native=load('check_fair_sampling_cpu');s=inspect.getsource(native.exercise)
 i=s.index('    try:\n        contexts=')
 s=s[:i]+'    return _body(inference,samples,wc,settings,inference_module,mode,kernel,flow,runtime)\n'
 env={**vars(native),'_body':body};exec(compile(s,__file__+'#pinned-native-setup','exec'),env)
 result=load('check_full_sampling').run(runtime,exercise=lambda **kw:env['exercise'](runtime=Path(runtime),**kw))
 # Missing decode / repeated boundaries fail closed; no partial T_DD.
 c=BoundaryClock(lambda:None);c.begin();c.denoise_end();assert c.receipt()['T_DD'] is None
 for fn in [c.begin,c.denoise_end]:
  try:fn()
  except ValueError:pass
  else:raise AssertionError('Duplicate boundary accepted')
 c.finish()
 try:c.finish()
 except ValueError:pass
 else:raise AssertionError('Duplicate decode accepted')
 result['limits']='Pinned Native/WC/RF/UniPC bodies; explicit tiny CPU weights, noise generator, attention, conditioner, decoder and mock writer. No real Cosmos weights, encoded videos, GPU equality, quality score or latency evidence.'
 result.update(status='P0_PINNED_SOURCE_TINY_CPU_PASS_NOT_GPU_PARITY',CUDA_initialized=torch.cuda.is_initialized(),GPU_submissions=0)
 assert not result['CUDA_initialized'];return result
if __name__=='__main__':
 start=time.perf_counter();r=main(sys.argv[1]);r['CPU_wall_seconds']=time.perf_counter()-start
 Path(sys.argv[2]).write_text(json.dumps(r,indent=2,default=str)+'\n');print(r['status'])
