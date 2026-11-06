"""New19-role request adapter on pinned sampler/RF/WC, both flow modes.
Tiny explicit weights and decoder; actual Cosmos weight inference is NOT claimed.
"""
import copy,inspect,json
from pathlib import Path
import numpy as np
import torch
from wcomr.policy_generator_r1.exploration_requests import Requests
from wcomr.policy_generator_r1.interval_grammar import Profile
from wcomr import clean_speed20_r1 as clean

ROOT=Path(__file__).resolve().parents[1]
def load(name):
 from importlib.util import spec_from_file_location,module_from_spec
 spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=module_from_spec(spec);spec.loader.exec_module(m);return m

def body(inference,selected,wc,rf,common,initial,unused_profile,root,native,flow,inference_module):
 card=json.loads((ROOT/'manifests/cara_shared_CAL106_scope_quote_r1_20261025.json').read_text())
 params=card['profile'];params['protected_dense']=tuple(params['protected_dense']);params['alpha_candidates']=tuple(params['alpha_candidates']);profile=Profile(**params)
 adapter=Requests(inference=inference,samples={selected[0].name:selected[0]},profile=profile,roles=card['roles'],schedules=card['schedules'],common=dict(common,CPU_native=native))
 frames=[];writer=inference_module.save_img_or_video;paths=0;controls=[]
 def watched(video,path,fps):frames.append(np.array(video,copy=True));return writer(video,path,fps)
 try:
  with clean.patched(inference_module,'save_img_or_video',watched):
   for role,spec in card['roles'].items():
    pair=[]
    for repeat in (1,2):
     initial.restore();slot=dict(id=f'{role}_{repeat}',role=role,member=selected[0].name,seed=0)
     r=adapter(slot,root/slot['id']);paths+=1
     assert r['status']=='COMPLETE' and r['solver_steps']==spec['requested_steps']+1
     if spec['kind']=='policy':
      assert [h['actual'] for h in r['semantic_history']]==spec['policy']['actions']
      for t,h in enumerate(r['semantic_history'],1):
       assert h['fallback_reason'] is None
       if h['actual']!='D':assert h['source_history']['shared_alpha']==(spec['policy']['shared_alpha'][t-1] or 0.)
     else:assert r['full_block_calls']==[2*(spec['requested_steps']+1)]*2 and not r['cache_installed']
     pair.append((r,frames[-1].copy()))
    assert torch.equal(pair[0][0]['final_latent'],pair[1][0]['final_latent'])
    assert all(torch.equal(a,b) for a,b in zip(pair[0][0]['guided'],pair[1][0]['guided']))
    assert np.array_equal(pair[0][1],pair[1][1])
    controls.append(dict(role=role,updates=spec['requested_steps']+1,repeat_all_guided_final_RGB_equal=True))
   try:adapter(slot,root/'duplicate')
   except ValueError:pass
   else:raise AssertionError('Duplicate physical slot replayed')
   initial.restore()
   with clean.patched(inference,'generate',lambda *a,**k:[]):
    r=adapter(dict(id='refusal',role='NATIVE28',member=selected[0].name,seed=0),root/'refusal')
   assert r['status']=='TEXT_REJECTED'
  return [dict(flow=flow,status='PASS',complete_paths=paths,roles=controls,
    all19_production_roles=True,repeat_identity_verified=True,original_alpha_and_D_preserved=True,
    duplicate_refused=True,guard_refusal_preserved=True,actual_Cosmos_weights=False,real_generated_video=False)]
 finally:initial.restore()

def run(runtime,artifact_root):
 old=load('check_cara_pg_production_sampling_cpu_r1')
 source=inspect.getsource(old.body);i=source.index('    try:\n        initial.restore();n=')
 source=source[:i]+'    return _new(inference,selected,wc,rf,common,initial,profile,root,native,flow,inference_module)\n'
 ns={**vars(old),'_new':body};exec(compile(source,__file__+'#accepted-setup','exec'),ns)
 exercise=load('check_partial_mlp_guided_sampling_cpu_r1');s=inspect.getsource(exercise.exercise)
 a=s.index('    results=[]\n    try:');b=s.index('\n    finally:\n',a)+1
 s=s[:a]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+s[b:]
 env={**vars(exercise),'_body':ns['body']};exec(compile(s,__file__+'#pinned-small-setup','exec'),env)
 return load('check_full_sampling').run(runtime,exercise=lambda **kw:env['exercise'](runtime=Path(runtime),tensor_loader=None,artifact_root=artifact_root,**kw))
