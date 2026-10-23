"""All18 Native counts and own-history OFF/ON through pinned full sampler/RF/WC."""
import copy,inspect
from pathlib import Path
import numpy as np
import torch
from wcomr.policy_generator_r1.p2_native_sampling import execute as native_execute
from wcomr.policy_generator_r1.p2_history_sampling import execute as history_execute
from wcomr.policy_generator_r1.production_sampling import execute as policy_execute
from wcomr.policy_generator_r1.interval_grammar import Edge,compile_policy
from wcomr import clean_speed20_r1 as clean


def load(name):
 from importlib.util import spec_from_file_location,module_from_spec
 spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=module_from_spec(spec);spec.loader.exec_module(m);return m


def body(inference,selected,wc,rf,common,initial,profile,root,native,flow,inference_module):
 scheduler=inference.pipe.model.sample_scheduler;paths=0;schedules=[];frames=[]
 writer=inference_module.save_img_or_video
 def watched_write(video,path,fps):
  frames.append(np.moveaxis(np.array(video,copy=True),0,-1));return writer(video,path,fps)
 try:
  with clean.patched(inference_module,'save_img_or_video',watched_write):
   for n in range(18,36):
    initial.restore();sample=copy.copy(selected[0]);sample.num_steps=n
    grid=type(scheduler)(num_train_timesteps=1000,shift=1,use_dynamic_shifting=False)
    grid.set_timesteps(n,device='cpu',shift=5.,use_kerras_sigma=True)
    schedule=dict(requested_steps=n,actual_updates=len(grid.timesteps),timesteps=grid.timesteps.tolist(),sigmas=grid.sigmas.tolist())
    r=native_execute(inference,sample,schedule=schedule,CPU_native=native,output=root/f'native{n}',**common)
    assert r['status']=='COMPLETE' and r['full_block_calls']==[2*len(grid.timesteps)]*2
    assert r['cache_installed'] is False and frames[-1].shape[0]==93
    schedules.append(schedule);paths+=1
   for alpha in (.5,1.):
    bounds=list(range(1,8))+[10,16,27,36,37]
    plan=compile_policy(profile,[Edge(s,t,(s+1,t-1),alpha) if t>s+1 else Edge(s,t) for s,t in zip(bounds,bounds[1:])])
    initial.restore();off=policy_execute(inference,selected[0],profile=profile,policy=plan,output=root/f'OFF{alpha}',**common);rgb=frames[-1].copy();paths+=1
    initial.restore();on=history_execute(inference,selected[0],profile=profile,policy=plan,output=root/f'ON{alpha}',**common);paths+=1
    assert off['status']==on['status']=='COMPLETE'
    assert all(torch.equal(a,b) for a,b in zip(off['guided'],on['guided'])) and torch.equal(off['final_latent'],on['final_latent'])
    assert np.array_equal(rgb,frames[-1]) and len(rgb)==93
    assert len(on['history_records'])==3 and on['shadow_D_pairs']==6
    assert all(r['A_ONE_window_invariant'] and r['parent_state_before_after_equal'] for r in on['history_records'])
    for record in on['history_records']:
     # Reload the exact branch tensors; neither guided-only reduction nor missing
     # paired branch evidence can satisfy the future alpha diagnostic contract.
     with open(record['branch_artifact']['path'],'rb') as f:raw=torch.load(f,map_location='cpu',weights_only=False)
     assert len(raw['D'])==2 and set(raw['windows'])=={'actual','adjacent'}
     assert all(len(v)==2 for w in raw['windows'].values() for v in w.values())
   initial.restore();origin=initial.fingerprint()
   with clean.patched(inference,'generate',lambda *a,**k:[]):
    refused=native_execute(inference,selected[0],schedule=schedules[-1],CPU_native=native,output=root/'refused',**common)
   assert refused['status']=='TEXT_REJECTED'
   initial.restore();assert initial.fingerprint()==origin
  return [dict(flow=flow,status='PASS',complete_paths=paths,Native_requested_steps=list(range(18,36)),schedule_rows=schedules,
   all_Native_first_last_blocks_counted=True,no_production_cache_installer=True,history_alpha_half_one=True,
   shadow_OFF_ON_full36_guided_final_equal=True,shadow_OFF_ON_all93_RGB_equal=True,all_three_history_bins=True,
   parent_input_solver_cache_anchor_condition_RNG_unchanged=True,branch_tensors_reloaded=True,A_ONE_older_window_invariant=True,
   exact_shadow_pair_counts=True,refusal_retained=True,actual_Cosmos_weights=False,real_generated_video=False)]
 finally:initial.restore()


def run(runtime,artifact_root):
 old=load('check_cara_pg_production_sampling_cpu_r1')
 source=inspect.getsource(old.body);i=source.index('    try:\n        initial.restore();n=')
 source=source[:i]+'    return _p2(inference,selected,wc,rf,common,initial,profile,root,native,flow,inference_module)\n'
 ns={**vars(old),'_p2':body};exec(compile(source,__file__+'#accepted-small-weight-setup','exec'),ns)
 exercise=load('check_partial_mlp_guided_sampling_cpu_r1');s=inspect.getsource(exercise.exercise)
 a=s.index('    results=[]\n    try:');b=s.index('\n    finally:\n',a)+1
 s=s[:a]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+s[b:]
 env={**vars(exercise),'_body':ns['body']};exec(compile(s,__file__+'#pinned-Toy-setup','exec'),env)
 return load('check_full_sampling').run(runtime,exercise=lambda **kw:env['exercise'](runtime=Path(runtime),tensor_loader=None,artifact_root=artifact_root,**kw))
