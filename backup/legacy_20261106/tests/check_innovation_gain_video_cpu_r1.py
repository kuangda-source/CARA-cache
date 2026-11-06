"""Declared small CPU model, complete46 collection and free-running controls."""
import inspect
import hashlib
import json
import torch
import check_scout_parent_cpu_v22 as base
from wcomr.innovation_gain_video_r1 import Requests, collect, repeat_controls
from wcomr.policy_generator_r1.interval_grammar import Profile

TAIL='''    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
    root=Path(artifact_root)/('video_flow_'+str(flow))
    repo=Path(__file__).resolve().parents[1]
    card=json.loads((repo/'manifests/cara_shared_CAL66_scope_quote_r1_20261025.json').read_text())
    protocol=json.loads((repo/'manifests/cara_IG_B2_predeclared_matrix_r1_20261027.json').read_text())
    params=dict(card['profile']);params['protected_dense']=tuple(params['protected_dense']);params['alpha_candidates']=tuple(params['alpha_candidates'])
    profile=_Profile(**params)
    samples={name:_actual_request(name) for name in card['CAL_FIT_members']}
    def native(self,*a,**kw):
        threshold=self.worldcache_rel_l1_thresh;self.worldcache_rel_l1_thresh=-1.
        try:return wc.worldcache_mini_train_dit_forward(self,*a,**kw)
        finally:self.worldcache_rel_l1_thresh=threshold
    common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
        inference_module=inference_module,expected_shape=[1,8,2,8,8],audit=False,CPU_native=native)
    adapter=_Requests(inference=inference,samples=samples,profile=profile,original_card=card,
        gains={'IG_SCALAR':(.3,.3),'IG_BAND':(.2,.8)},common=common,table_parameters=tables,
        previous_parameters=prior,model_identity='DECLARED_CPU_ONLY')
    def request(slot,directory):
        initial.restore();assert initial.fingerprint()==origin
        return adapter(slot,directory)
    try:
        state=_collect(protocol,root,request,lambda s:None)
        controls=_repeats(state,root,lambda p:_hashlib.sha256(p.read_bytes()).hexdigest())
        assert len(state['rows'])==46 and len(controls)==6
        try:adapter(protocol['matrix'][0],root/'duplicate')
        except ValueError as exc:assert 'retried' in str(exc)
        else:raise AssertionError('Repeated slot was accepted')
        return [dict(flow=flow,status='B2_COMPLETE46_CPU_ONLY',paths=46,repeat_controls=6,
            no_timed_guided_copies=True,all_head_counts_and_D_masks=True,
            real_weights=False,real_video_quality=False,GPU_submissions=0)]
    finally:initial.restore();assert initial.fingerprint()==origin
'''


def run(runtime,artifact_root,actual_request=None):
    original=base.body
    prefix=inspect.getsource(original).split('    initial=CompleteStateRoundtrip(')[0]
    real_schema=actual_request is not None
    if actual_request is None:
        from test_cara_frozen_request_arguments_r2 import Frozen
        class DeclaredFrozenFixture(Frozen):
            def model_dump_json(self):return json.dumps(self.model_dump())
        def actual_request(name):
            return DeclaredFrozenFixture(dict(name=name,prompt=name,num_steps=35,seed=0,guidance=7,
                num_output_frames=93,num_input_frames=0,input_path=None,negative_prompt='negative',
                resolution='16,16',enable_autoregressive=False))
    tail=TAIL
    ns={**vars(base),'_Profile':Profile,'_Requests':Requests,'_collect':collect,
        '_repeats':repeat_controls,'_hashlib':hashlib,'_actual_request':actual_request}
    exec(compile(prefix+tail,__file__+'#small-pinned-CPU-setup','exec'),ns)
    base.body=ns['body']
    try:
        value=base.run(runtime,lambda p:torch.load(p,map_location='cpu',weights_only=True),artifact_root)
        return dict(status='B2_COMPLETE_VIDEO_SOURCE_CPU_CHECK_NOT_REAL_MODEL',checks=value['checks'],
                    actual_Cosmos_request_class=real_schema,GPU_submissions=0)
    finally:base.body=original
