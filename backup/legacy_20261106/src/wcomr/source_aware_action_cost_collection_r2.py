"""Same-state post-probe C/A/P/D costs on the unchanged complete D6 parent.

This is a new diagnostic card, not a shortened RA+A video card. Readout arms
run the source C body and preserve actual D-only calibration. Full attention
and gathered four-layer MLP execute in P; all research time remains chargeable.
"""
import ast
import copy
import hashlib
import inspect
from textwrap import dedent

from . import partial_mlp_collection as base
from .calibration import ResidualCalibrator
from .cfg_guided_w1_deployment import GuidedW1Readout
from .cfg_paired_probe_forward import _function, _compile, _find_safe, WC_PATH, WC_SHA

MODES = ('C', 'A_W1_ONE_PHASE', 'A_BETA1_ONE_PHASE', 'ROTATION_050',
         'DENSE_REFERENCE', 'DENSE_WITH_P0')
METHODS = ('ORIGINAL',) + MODES
READOUT_MODES = MODES[:3]


def compile_cached_readout(runtime, wc):
    original = _function(runtime, WC_PATH, WC_SHA, 'worldcache_mini_train_dit_forward')
    hit = _find_safe(original, lambda n:isinstance(n,ast.If)
                     and ast.unparse(n.test)=='skip_forward')
    hidden = _find_safe(original, lambda n:isinstance(n,ast.Assign) and ast.unparse(n)==
        'x_B_T_H_W_O = self.final_layer(x_B_T_H_W_D, t_embedding_B_T_D, adaln_lora_B_T_3D=adaln_lora_B_T_3D)')
    head = _find_safe(original, lambda n:isinstance(n,ast.Assign) and ast.unparse(n)==
        'x_B_C_Tt_Hp_Wp = self.unpatchify(x_B_T_H_W_O)')
    body = copy.deepcopy(hit.body)
    count = 0
    for i,n in enumerate(body):
        if ast.unparse(n)=='self.previous_internal_states[current_idx] = test_x':
            body.insert(i,ast.parse('if observer is not None: observer.prewarp(self,current_idx,x_B_T_H_W_D)').body[0])
            count += 1
            break
    if count!=1:raise ValueError('Pinned C prewarp boundary differs')
    # Remove only the explicit observation; the C body AST must recover exactly.
    inverse = copy.deepcopy(body)
    inverse = [n for n in inverse if not (isinstance(n,ast.If)
        and ast.unparse(n.test)=='observer is not None')]
    if ast.dump(ast.Module(body=inverse,type_ignores=[]))!=ast.dump(ast.Module(body=hit.body,type_ignores=[])):
        raise ValueError('Cached C execution changed beyond an observation')
    fn = ast.parse('def cached(self, ori_x, test_x, residual_x, block_kwargs, t_embedding_B_T_D, adaln_lora_B_T_3D, observer):\n    pass').body[0]
    prefix = ast.parse('current_idx=self.cnt%2\nx_B_T_H_W_D=ori_x\nT=ori_x.shape[1]').body
    observe_hidden = ast.parse('if observer is not None: observer.hidden(self,True,current_idx,ori_x,test_x,x_B_T_H_W_D,block_kwargs,t_embedding_B_T_D,adaln_lora_B_T_3D)').body
    observe_output = ast.parse('if observer is not None: observer.output(self,current_idx,x_B_C_Tt_Hp_Wp)').body
    fn.body = prefix + body + observe_hidden + [copy.deepcopy(hidden),copy.deepcopy(head)] + observe_output + ast.parse('return x_B_C_Tt_Hp_Wp').body
    value = _compile(fn,vars(wc),WC_PATH+'#source-exact-C-cost-readout')
    proof = {'WC_source_sha256':WC_SHA,'cached_body_inverse_AST_equal':True,
        'original_skip_body_AST_sha256':hashlib.sha256(ast.dump(hit).encode()).hexdigest(),
        'original_head_and_unpatchify_AST_preserved':True,
        'C_gamma_flow_and_original_clone_cost_preserved':True,
        'three_optional_readout_observations':True,'deep_or_MLP_in_C':False}
    return value,proof


class ActionCostCollector(base.PartialGroupCollector):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.calibrators = [ResidualCalibrator(),ResidualCalibrator()]
        for c in self.calibrators:c.reset(self.context)
        self.cached_readout = None
        self.cached_readout_proof = None

    def hidden(self,net,skipped,slot,original,probe,hidden,kwargs,embedding,adaln):
        super().hidden(net,skipped,slot,original,probe,hidden,kwargs,embedding,adaln)
        if not self.enabled:return
        step=self.current['step']
        if not skipped:
            if not self.calibrators[slot].observe_full(context=self.context,step=step,
                    probe=net.probe_residual_cache[slot],residual=net.residual_cache[slot]):
                raise ValueError('Actual parent D-only readout anchor invalid')
        if step in base.SELECTED_STEPS:
            self.current['branches'][slot]['original']=original.detach().clone()

    def _readout_arm(self,mode):
        cur=self.current;step=cur['step'];saved_cnt=self.net.cnt
        before=[copy.deepcopy(c.receipt()) for c in self.calibrators]
        observer=None
        try:
            self.net.cnt=2*(step-1)%70
            if mode!='C':
                observer=GuidedW1Readout(self.model,method=mode.removeprefix('A_'),context=self.context)
                observer.calibrators=self.calibrators
                observer.completed=step-1
                observer.warp,observer.to_velocity=self.warp,self.to_velocity
                observer.begin(cur['noise'],cur['latent'],cur['timestep'],cur['conditions'])
            values=[]
            for slot in (0,1):
                self.net.cnt=(2*(step-1)+slot)%70
                branch=cur['branches'][slot]
                head=self.cached_readout(self.net,branch['original'],branch['probe'],
                    self.net.residual_cache[slot],branch['kwargs'],branch['embedding'],branch['adaln'],observer)
                values.append(self.to_velocity(self.model,cur['noise'],cur['latent'],cur['timestep'],
                    cur['conditions'][slot],_supplied_net_output=head))
            self.net.cnt=2*step%70
            if observer is not None:
                values=observer.end(tuple(values),'CC')
                self.last_A_readout=copy.deepcopy(observer.history[-1])
            if [c.receipt() for c in self.calibrators]!=before:
                raise ValueError('Score-only C/A cost arm changed actual D calibration')
            return tuple(values)
        finally:self.net.cnt=saved_cnt

    def _arm(self,mode):
        if mode in READOUT_MODES:
            if self.cached_readout is None:raise ValueError('Source-exact C compiler missing')
            return self._readout_arm(mode)
        if mode not in MODES:raise ValueError('Only registered complete cost modes permitted')
        return super()._arm(mode)


def derive_end():
    source = dedent(inspect.getsource(base.PartialGroupCollector.end))
    before = "if mode!='DENSE_REFERENCE':"
    after = "if mode not in ('DENSE_REFERENCE','C','A_W1_ONE_PHASE','A_BETA1_ONE_PHASE'):"
    assert source.count(before) == 1
    changed = source.replace(before, after)
    before2 = "            pairs={'ORIGINAL':original,**pairs}"
    after2 = "            if not all(torch.equal(x,y) for x,y in zip(pairs['C'],original)):\n                raise ValueError('Source-exact recomputed C output differs from actual parent')\n" + before2
    assert changed.count(before2) == 1
    changed = changed.replace(before2, after2)
    extra = [('            pairs={};rows={};timings={mode:[] for mode in MODES};peaks={mode:[] for mode in MODES}', '            head_counts={};head_calls=[];A_readouts={}\n            handles.append(self.net.final_layer.register_forward_hook(lambda m,a,v:head_calls.append(1)))\n            pairs={};rows={};timings={mode:[] for mode in MODES};peaks={mode:[] for mode in MODES}'), ('external.restore();projection.restore();observed.clear()', 'external.restore();projection.restore();observed.clear();head_calls.clear()'), ('                    rows[mode]=list(observed)', "                    rows[mode]=list(observed);head_counts[mode]=len(head_calls)\n                    if mode.startswith('A_'):A_readouts[mode]=copy.deepcopy(self.last_A_readout)"), ("'actual_post_RF_original_direct_equal':True,", "'actual_post_RF_original_direct_equal':True,'C_recomputed_direct_equal':True,\n                'cached_readout_source_proof':self.cached_readout_proof,\n                'warmup_actual_output_head_calls':head_counts,'warmup_A_readouts':A_readouts,\n                'incremental_post_probe_cost_not_full_pair_or_clean_pipeline':True,")]
    for (old, new) in extra:
        assert changed.count(old) == 1
        changed = changed.replace(old, new)
    inverse = changed
    for (old, new) in reversed(extra):
        inverse = inverse.replace(new, old)
    inverse = inverse.replace(after2, before2).replace(after, before)
    assert inverse == source and ast.dump(ast.parse(inverse)) == ast.dump(ast.parse(source))
    ns = {**base.PartialGroupCollector.end.__globals__, 'MODES': MODES, 'METHODS': METHODS}
    exec(compile(changed, __file__ + '#source-exact-cost-complete-end', 'exec'), ns)
    return (ns['end'], {'inverse_AST_and_original_bytes_equal': True, 'explicit_sites': 6, 'original_end_sha256': hashlib.sha256(source.encode()).hexdigest(), 'complete_original_six_modes_three_repeats_and_rotated_order_preserved': True})


ActionCostCollector.end,END_PROOF=derive_end()


def compile_action_cost_collection(runtime,wc,rf,collector):
    result=base.compile_partial_collection(runtime,wc,rf,collector)
    collector.cached_readout,collector.cached_readout_proof=compile_cached_readout(runtime,wc)
    return result
