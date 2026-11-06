"""Pinned full loop/RF/WC and pipeline; declared tiny weights/prepare/decode/writer.
Tests real source boundaries and opt-in request adapter, not model performance.
"""
import copy,inspect,json
from pathlib import Path
import numpy as np
import torch
from pydantic import BaseModel,ConfigDict
from wcomr import clean_speed20_r1 as clean
from wcomr.method_experiment_timing_r1 import TimedRequests
from wcomr.policy_generator_r1.exploration_requests import Requests
from wcomr.policy_generator_r1.interval_grammar import Profile
from wcomr.paper_latency_r1 import measure,TimingBoundaryError

ROOT=Path(__file__).resolve().parents[1]
def load(name):
 from importlib.util import spec_from_file_location,module_from_spec
 spec=spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=module_from_spec(spec);spec.loader.exec_module(m);return m

class FrozenCPURequest(BaseModel):
 model_config=ConfigDict(frozen=True)
 name:str='CLOCK_CPU';prompt:str='CLOCK_CPU';num_steps:int=35;seed:int=0;guidance:int=7
 num_output_frames:int=93;num_input_frames:int=0;input_path:None=None
 negative_prompt:str='negative';resolution:str='16,16';enable_autoregressive:bool=False

def body(inference,selected,wc,rf,common,initial,unused_profile,root,native,flow,inference_module,host,actual_sample):
 card=json.loads((ROOT/'manifests/cara_DEV128_scope_r1_20261026.json').read_text())
 params=dict(card['profile']);params['protected_dense']=tuple(params['protected_dense']);params['alpha_candidates']=tuple(params['alpha_candidates']);profile=Profile(**params)
 sample=actual_sample;before=sample.model_dump();roles=('NATIVE35','NATIVE26','S25_A_PHASE','SHARED25_C')
 kw=dict(inference=inference,samples={sample.name:sample},profile=profile,roles=card['roles'],schedules=card['schedules'],common=dict(common,CPU_native=native))
 base=Requests(**kw);timed=TimedRequests(**kw,timing_host=host,timing_cpu_validation=True)
 frames=[];writer=inference_module.save_img_or_video;checks=[]
 model=inference.pipe.model;originals=(model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world)
 def restored():
  assert originals==(model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world)
  assert '_cara_paper_timing_active_r1' not in vars(model)
 def watched(video,path,fps):frames.append(np.array(video,copy=True));return writer(video,path,fps)
 with clean.patched(inference_module,'save_img_or_video',watched):
  for role in roles:
   pair=[]
   for name,adapter in [('off',base),('on',timed)]:
    initial.restore();slot=dict(id=role+'_'+name,role=role,member=sample.name,seed=0)
    r=adapter(slot,root/slot['id']);pair.append((r,frames[-1].copy()));restored()
   a,b=pair[0][0],pair[1][0]
   assert torch.equal(a['final_latent'],b['final_latent'])
   assert all(torch.equal(x,y) for x,y in zip(a['guided'],b['guided']))
   assert a.get('semantic_history')==b.get('semantic_history') and a.get('A_history')==b.get('A_history')
   assert np.array_equal(pair[0][1],pair[1][1])
   assert 0<b['paper_denoise_decode_seconds']<=b['core_seconds']<=b['full_request_seconds']
   assert b['paper_timing']['synchronization_calls']==2 and not b['paper_timing']['deployment_latency_eligible']
   assert sample.model_dump()==before
   checks.append(dict(role=role,updates=b['solver_steps'],all_guided_final_mock_RGB_equal=True,original_alpha_history_equal=True,clock_nested=True))
  # Post-sampling and pre-loop prepare remain inside core but outside the new clock.
  events=[];prepare=inference.pipe._get_data_batch_input;decode=model.decode
  def watch_prepare(*a,**k):events.append('prepare');return prepare(*a,**k)
  def watch_decode(*a,**k):events.append('decode');return decode(*a,**k)
  from wcomr.paper_latency_r1 import BoundaryClock
  class WatchClock(BoundaryClock):
   def begin(self):events.append('loop_start');super().begin()
   def loop_done(self):events.append('loop_end');super().loop_done()
   def decode(self,*a,**k):v=super().decode(*a,**k);events.append('timed_end');return v
  initial.restore()
  with clean.patched(inference.pipe,'_get_data_batch_input',watch_prepare),clean.patched(model,'decode',watch_decode):
   with measure(inference,runtime=common['runtime'],host=host,expected_updates=36,cpu_validation=True,_clock_factory=WatchClock) as clock:
    row=base(dict(id='order',role='SHARED25_C',member=sample.name,seed=0),root/'order')
    clock.finish(row,36,False)
  assert events==['prepare','loop_start','loop_end','decode','timed_end'],events
  restored()
  # Early refusal never emits zero as a successful new clock.
  initial.restore()
  with clean.patched(inference,'generate',lambda *a,**k:[]):
   rejected=timed(dict(id='refusal',role='SHARED25_C',member=sample.name,seed=0),root/'refusal')
  assert rejected['paper_denoise_decode_seconds'] is None;restored()
  try:timed(dict(id='refusal',role='SHARED25_C',member=sample.name,seed=0),root/'retry')
  except ValueError:pass
  else:raise AssertionError('Failed/refused slot replayed')
  failures=[]
  for fault in ('decode','writer','prepare'):
   initial.restore()
   def fail(*a,**k):raise OSError('DECLARED_'+fault)
   owner,field={'decode':(model,'decode'),'writer':(inference_module,'save_img_or_video'),'prepare':(inference.pipe,'_get_data_batch_input')}[fault]
   with clean.patched(owner,field,fail):
    try:timed(dict(id=fault,role='SHARED25_C',member=sample.name,seed=0),root/fault)
    except OSError as e:assert str(e)=='DECLARED_'+fault;failures.append(fault)
    else:raise AssertionError('Failure swallowed')
   restored()
  # Live function substitution and nested same-model timing are unsupported.
  with clean.patched(model,'generate_samples_from_batch',lambda *a,**k:None):
   try:
    with measure(inference,runtime=common['runtime'],host=host,expected_updates=36,cpu_validation=True):pass
   except TimingBoundaryError:failures.append('modified_live_sampler')
   else:raise AssertionError('Unbound sampler accepted')
  with measure(inference,runtime=common['runtime'],host=host,expected_updates=36,cpu_validation=True):
   try:
    with measure(inference,runtime=common['runtime'],host=host,expected_updates=36,cpu_validation=True):pass
   except TimingBoundaryError:failures.append('nested_request')
   else:raise AssertionError('Nested timing accepted')
  restored();initial.restore()
 return [dict(host=host,flow=flow,complete_paths=9,status='PASS',roles=checks,event_order=events,
   failures=failures,original_full_clock_formula_preserved=True,restored_after_all_paths=True,
   frozen_request_unchanged=True,request_schema=type(sample).__module__+'.'+type(sample).__qualname__,
   pinned_sampler_pipeline_RF_WC=True,actual_Cosmos_weights=False,real_generated_video=False)]

def run(runtime,artifact_root,host,actual_sample):
 old=load('check_cara_pg_production_sampling_cpu_r1');source=inspect.getsource(old.body);i=source.index('    try:\n        initial.restore();n=')
 source=source[:i]+'    return _new(inference,selected,wc,rf,common,initial,profile,root,native,flow,inference_module)\n'
 ns={**vars(old),'_new':lambda *args:body(*args,host=host,actual_sample=actual_sample)};exec(compile(source,__file__+'#accepted-setup','exec'),ns)
 exercise=load('check_partial_mlp_guided_sampling_cpu_r1');s=inspect.getsource(exercise.exercise)
 a=s.index('    results=[]\n    try:');b=s.index('\n    finally:\n',a)+1
 s=s[:a]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+s[b:]
 env={**vars(exercise),'_body':ns['body']};exec(compile(s,__file__+'#pinned-small-setup','exec'),env)
 return load('check_full_sampling').run(runtime,exercise=lambda **kw:env['exercise'](runtime=Path(runtime),tensor_loader=None,artifact_root=artifact_root,**kw))
