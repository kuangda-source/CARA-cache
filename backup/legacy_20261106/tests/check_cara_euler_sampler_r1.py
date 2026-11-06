"""Pinned full sampler/Native/WC CPU integration, with declared tiny stand-ins."""
import ast,copy,hashlib,importlib.util,inspect,json,sys,tempfile,types
from pathlib import Path
import numpy as np
import torch
from wcomr.cara_euler_protocol_r1 import reconstructed_grid
from wcomr.cara_euler_sampler_r1 import CosmosEuler35,installed_euler35
from wcomr.fair_sampling import native_forward
from wcomr.prepared_input import RNGState
from wcomr.wc_time_protocol_p0 import compile_wc_adapter,installed_timing
ROOT=Path(__file__).resolve().parents[1]
VIDEO='cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py'
VIDEO_SHA='9b53e3f024e5cbb2cb3778819e1a6fd353923c13ad9b868d99602051640a65e8'

def load(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'tests'/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def body(inference,samples,wc,settings,inference_module,mode_setup,kernel,flow,runtime):
 model=inference.pipe.model;net=model.net;fixture=load('check_full_sampling')
 fixture.load_functions(Path(runtime)/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py',['compute_saliency_map'],vars(wc))
 path=Path(runtime)/VIDEO;assert hashlib.sha256(path.read_bytes()).hexdigest()==VIDEO_SHA
 ns={**vars(wc),'NUM_CONDITIONAL_FRAMES_KEY':'num_conditional_frames',
     'parallel_state':types.SimpleNamespace(is_initialized=lambda:False)}
 fixture.load_functions(path,['get_velocity_fn_from_batch'],ns)
 original_cfg=model.get_velocity_fn_from_batch;original_conditions=model.conditioner.get_condition_with_negative_prompt
 original_forward=net.forward;original_enabled=inference.pipe.worldcache_enabled
 original_decode=model.decode;original_writer=inference_module.save_img_or_video
 original_denoise=model.denoise;original_scheduler=model.sample_scheduler
 original_config=copy.copy(vars(model.config));entry=RNGState();rows={};frames=[]
 def conditions(batch):
  values=original_conditions(batch)
  for value in values:
   value.set_video_condition=lambda _value=value,**kw:_value
   value.edit_for_inference=lambda _value=value,**kw:_value
  return values
 model.conditioner.get_condition_with_negative_prompt=conditions
 model.get_velocity_fn_from_batch=types.MethodType(ns['get_velocity_fn_from_batch'],model)
 model.config.min_num_conditional_frames=0;model.config.max_num_conditional_frames=0;model.config.conditional_frames_probs=None
 active={}
 def denoise(noise,x,t,condition):
  active['branches'].append(condition.branch);active['initial_noise'].append(noise.detach().clone()) if not active['initial_noise'] else None
  active['pre_cnt'].append(net.cnt)
  value=original_denoise(noise,x,t,condition);active['post_cnt'].append(net.cnt)
  active['branch_outputs'].append(value.detach().clone());return value
 def decode(latent):active['latent']=latent.detach().clone();return original_decode(latent)
 def writer(video,path,fps):frames.append(np.array(video,copy=True));return original_writer(video,path,fps)
 model.denoise=denoise;model.decode=decode;inference_module.save_img_or_video=writer
 grid=reconstructed_grid(35)
 allD,allDproof=compile_wc_adapter(runtime,wc,force_full=True,paper_port=True)
 paper,paperproof=compile_wc_adapter(runtime,wc,paper_port=True)
 assert allDproof['changed_sites']==['skip_predicate_false','ATS_base_mult_4']
 assert paperproof['changed_sites']==['ATS_base_mult_4']
 paper_settings={**settings,'worldcache_num_steps':35,'worldcache_rel_l1_thresh':.08,
  'worldcache_motion_sensitivity':2.,'worldcache_saliency_enabled':True,'worldcache_saliency_weight':.12,
  'worldcache_flow_scale':.5,'worldcache_dynamic_decay':True}
 try:
  with tempfile.TemporaryDirectory(prefix='euler35-pinned-cpu-') as temp:
   for label,module,native,timed in [('Native',wc,True,True),('allD',allD,False,True),('allD_repeat',allD,False,False),('paper',paper,False,True)]:
    entry.restore()
    for b in net.buffers():b.zero_()
    module.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in paper_settings.items()})
    inference.pipe.worldcache_enabled=not native
    if native:net.forward=native_forward(net);net.worldcache_enabled=False
    active=dict(branches=[],branch_outputs=[],initial_noise=[],pre_cnt=[],post_cnt=[],updates=[])
    with installed_euler35(model,grid) as scheduler:
     step=scheduler.step
     def record_step(*a,**kw):
      out=step(*a,**kw);active['updates'].append(out[0].detach().clone());return out
     scheduler.step=record_step
     if timed:
      with installed_timing(model,runtime,lambda:None) as clock:
       paths=inference.generate([samples[0]],output_dir=Path(temp)/label)
      assert clock.receipt()['boundary_sync_calls']==2 and clock.receipt()['T_DD']>0
     else:paths=inference.generate([samples[0]],output_dir=Path(temp)/label)
     assert scheduler._step_index==35 and scheduler.timesteps.tolist()==grid['timesteps']
     assert active['branches']==[0,1]*35 and len(active['updates'])==35
     if not native:
      assert active['pre_cnt']==list(range(70)) and active['post_cnt']==list(range(1,70))+[0]
      assert net.worldcache_num_steps==70
     rows[label]=dict(active,RGB=frames[-1],rng=RNGState().signatures(),mock_file_sha=hashlib.sha256(Path(paths[0]).read_bytes()).hexdigest())
    assert model.sample_scheduler is original_scheduler
   for other in ('allD','allD_repeat'):
    a,b=rows['Native'],rows[other]
    for key in ('initial_noise','branch_outputs','updates'):
     assert len(a[key])==len(b[key]) and all(torch.equal(x,y) for x,y in zip(a[key],b[key])),(other,key)
    assert torch.equal(a['latent'],b['latent']) and np.array_equal(a['RGB'],b['RGB']) and a['rng']==b['rng']
  # Original request scheduler is restored after failure as well as success.
  try:
   with installed_euler35(model,grid):raise RuntimeError('declared CPU request failure')
  except RuntimeError:pass
  assert model.sample_scheduler is original_scheduler
 finally:
  model.get_velocity_fn_from_batch=original_cfg;model.conditioner.get_condition_with_negative_prompt=original_conditions
  model.denoise=original_denoise;model.decode=original_decode;inference_module.save_img_or_video=original_writer
  model.config.__dict__.clear();model.config.__dict__.update(original_config)
  net.forward=original_forward;inference.pipe.worldcache_enabled=original_enabled
  for b in net.buffers():b.zero_()
  entry.restore()
 return [dict(flow=flow,complete_paths=4,updates_per_path=35,CFG_calls_per_path=70,
  Native_allD_all70_branch_outputs_all35_latents_final_latent_RGB_RNG_equal=True,
  timed_untimed_allD_equal=True,WC_counters_before=list(range(70)),WC_reset_after_call70=True,
  ATS_coefficient=4,ATS_horizon_decoupled=True,paper_settings=paper_settings,
  scheduler_restored_on_success_and_failure=True,source_CFG_sha256=VIDEO_SHA,WC_adapter_proofs=[allDproof,paperproof],
  real_Cosmos_weights=False,real_encoded_video=False,GPU_parity=False)]

def main(runtime):
 torch.set_num_threads(1);assert not torch.cuda.is_initialized()
 native=load('check_fair_sampling_cpu');source=inspect.getsource(native.exercise)
 i=source.index('    try:\n        contexts=')
 source=source[:i]+'    return _body(inference,samples,wc,settings,inference_module,mode,kernel,flow,runtime)\n'
 env={**vars(native),'_body':body};exec(compile(source,__file__+'#pinned-native-setup','exec'),env)
 result=load('check_full_sampling').run(runtime,exercise=lambda **kw:env['exercise'](runtime=Path(runtime),**kw))
 result.update(status='EULER35_PINNED_FULL_PIPELINE_TINY_CPU_PASS_NOT_GPU',CUDA_initialized=torch.cuda.is_initialized(),GPU_submissions=0,
  real_weights_loaded=False,real_encoded_video=False,limits='Pinned inference, sampler, video CFG, Native/WC bodies; explicit tiny CPU weights, condition objects, patch embedding, attention, decoder, mock writer and CUDA telemetry stand-ins. No GPU quality, speed or real-weight parity claim.')
 assert not result['CUDA_initialized'];return result
if __name__=='__main__':
 result=main(sys.argv[1]);Path(sys.argv[2]).write_text(json.dumps(result,indent=2,default=str)+'\n');print(result['status'])
