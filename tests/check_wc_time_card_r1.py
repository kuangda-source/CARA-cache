"""Seven production role routes; true pinned Native; explicit tiny CPU geometry."""
import copy,inspect,json,types
from pathlib import Path
import numpy as np
import torch
from wcomr import clean_speed20_r1 as clean
from wcomr.wc_time_card_r1 import Requests,select_tau
from wcomr.full_sampling import CompleteStateRoundtrip
ROOT=Path(__file__).resolve().parents[1]
def load(name):
 from importlib.util import spec_from_file_location,module_from_spec
 s=spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=module_from_spec(s);s.loader.exec_module(m);return m

def body(inference,selected,wc,rf,common,unused_initial,profile,root,native,flow,inference_module,host,samples):
 card=json.loads((ROOT/'plans/cara_wc_time_protocol_p0_20261027/CONTROL_IDENTITY_MATRIX.yaml').read_text())
 binding=json.loads((ROOT/'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json').read_text())
 model=inference.pipe.model;net=model.net
 net.__class__=load('check_fair_sampling_cpu').native_toy_class(Path(common['runtime']),type(net),dict(vars(wc)))
 net.timestep_scale=.001
 # The production RF condition and pinned Block bodies are retained. Only
 # weights/attention/prepare/decode/writer are declared tiny CPU substitutes.
 initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1))
 kw=dict(inference=inference,samples=samples,card=card,common=common,ra_binding=binding,host=host,cpu_validation=True)
 frozen=dict(selected_tau=.04,phase_A_GPU_released=True,CPU_FIXTURE_ONLY=True)
 results={};frames=[];old_write=inference_module.save_img_or_video
 originals=(model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)
 def restore_check():
  assert (model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)==originals
  assert '_cara_paper_timing_active_r1' not in vars(model)
 def writer(video,path,fps):frames.append(np.array(video,copy=True));return old_write(video,path,fps)
 with clean.patched(inference_module,'save_img_or_video',writer):
  a=Requests(**kw,frozen=frozen)
  for slot in card['physical_matrix']:
   initial.restore();out=a(slot,root/slot['id'].replace(':','_'))
   assert out['status']=='COMPLETE' and out['solver_steps']==out['guided_pairs']==36
   if slot.get('timing_enabled',True):assert out['paper_timing']['synchronization_calls']==2 and 0<out['T_DD']<=out['T_generate']<=out['T_request']
   if slot['role']=='WC_WRAPPER_ALLD_U36':assert out['actions']==['DD']*36
   if slot['role']=='CARA_SHARED25_C_U36':assert [h['actual'] for h in out['semantic_history']]==card['roles'][slot['role']]['policy']['actions']
   if slot['section']=='B_QUALITY' and slot['scene']==card['requests'][0]['name']:results[slot['role']]=(out,frames[-1].copy(),torch.get_rng_state().clone())
   restore_check()
  for role,(on,rgb,rng) in results.items():
   slot=next(s for s in card['physical_matrix'] if s['section']=='B_QUALITY' and s['role']==role and s['scene']==card['requests'][0]['name'])
   initial.restore();off=Requests(**kw,frozen=frozen)(slot,root/('OFF_'+role),timing=False)
   assert torch.equal(on['final_latent'],off['final_latent']) and all(torch.equal(x,y) for x,y in zip(on['guided'],off['guided']))
   assert on.get('semantic_history')==off.get('semantic_history') and on.get('actions')==off.get('actions')
   assert np.array_equal(rgb,frames[-1]) and torch.equal(rng,torch.get_rng_state());restore_check()
  n,allD=results['NATIVE_U36'],results['WC_WRAPPER_ALLD_U36']
  assert torch.equal(n[0]['final_latent'],allD[0]['final_latent']) and np.array_equal(n[1],allD[1])
  faults=[]
  for role in results:
   slot=next(s for s in card['physical_matrix'] if s['section']=='B_QUALITY' and s['role']==role)
   for fault in ('refusal','decode','writer'):
    initial.restore();runner=Requests(**kw,frozen=frozen)
    def fail(*a,**k):raise OSError('DECLARED_FAILURE')
    owner,field,fn=(inference,'generate',lambda *a,**k:[]) if fault=='refusal' else (model,'decode',fail) if fault=='decode' else (inference_module,'save_img_or_video',fail)
    with clean.patched(owner,field,fn):
     try:r=runner(slot,root/(fault+'_'+role))
     except OSError:assert fault!='refusal'
     else:assert fault=='refusal' and r['status']=='TEXT_REJECTED' and r['T_DD'] is None
    restore_check()
    try:runner(slot,root/'retry')
    except ValueError:pass
    else:raise AssertionError('Duplicate slot replayed')
    faults.append(role+':'+fault)
  slot=next(s for s in card['physical_matrix'] if s['section']=='B_QUALITY')
  try:Requests(**kw)(slot,root/'no_freeze')
  except ValueError:pass
  else:raise AssertionError('Unfrozen phase B accepted')
 initial.restore()
 return [dict(status='PASS',flow=flow,registered_paths=73,extra_OFF_comparisons=7,roles=list(results),true_native_allD_equal=True,all_seven_timing_OFF_ON_equal=True,all_seven_refusal_decode_writer_cleanup=True,no_replay=True,missing_freeze_refused=True,failures_checked=faults,Cosmos_weights=False,real_video=False)]

def run(runtime,artifact_root,host,samples):
 old=load('check_cara_pg_production_sampling_cpu_r1');s=inspect.getsource(old.body);i=s.index('    try:\n        initial.restore();n=')
 s=s[:i]+'    return _body(inference,selected,wc,rf,common,initial,profile,root,native,flow,inference_module)\n'
 ns={**vars(old),'_body':lambda *args:body(*args,host=host,samples=samples)};exec(compile(s,__file__+'#setup','exec'),ns)
 old=load('check_partial_mlp_guided_sampling_cpu_r1');s=inspect.getsource(old.exercise);a=s.index('    results=[]\n    try:');b=s.index('\n    finally:\n',a)+1
 s=s[:a]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+s[b:]
 ns={**vars(old),'_body':ns['body']};exec(compile(s,__file__+'#blocks','exec'),ns)
 return load('check_full_sampling').run(runtime,exercise=lambda **kw:ns['exercise'](runtime=Path(runtime),tensor_loader=None,artifact_root=artifact_root,**kw))
