"""The existing full guarded OFF/ON batch, with explicit P0 collector bindings.

Only collector/compiler/validator bindings, the112 branch count and diagnostic
cleanup differ. Inverse AST equality preserves the ordinary sampler and return.
"""
import ast
import copy
import hashlib
import inspect
import math
from pathlib import Path
from textwrap import dedent

import torch

from . import cfg_guided_w1_sampling as parent
from .partial_mlp_collection import PartialGroupCollector, PartialCollectedPair, compile_partial_collection
from .partial_mlp_collection import METHODS, MODES, LAYERS, DENSE_STEPS, SELECTED_STEPS
from .cfg_guided_w1_outputs import guided_velocity_moments
from .cfg_guided_w1_collection import tensor_sha
from .mid_coverage import tree_digest


def verify_partial_batch(state):
    if (state.get('planned_parent_paths')!=8 or state.get('planned_origins')!=8
            or state.get('planned_post_RF_branch_tensors')!=112 or len(state.get('requests',[]))!=4):
        raise ValueError('Complete four-scene P0 eight-parent/eight-origin/112-branch scope required')
    count=0
    for request in state['requests']:
        rows=request['paths']
        if len(rows)!=2 or [r['collect'] for r in rows]!=[False,True]:
            raise ValueError('Each complete scene needs P0 collection OFF/ON')
        for row in rows:
            if (row['status']!='COMPLETE_PARENT_PATH' or len(row['guided_sha256'])!=36
                    or len(row['solver_returns'])!=36
                    or row['actions']!=['DD' if s in DENSE_STEPS else 'CC' for s in range(1,37)]
                    or row['counters']!=list(range(0,70,2))+[0]
                    or [c['step'] for c in row['checkpoints']]!=list(parent.STATE_STEPS)
                    or any(row[k]!=rows[0][k] for k in parent.PARITY)
                    or row['video_artifact']['sha256']!=rows[0]['video_artifact']['sha256']
                    or not row['all_modules_eval'] or not row['parameter_versions_unchanged']
                    or row['conditions_before']!=row['conditions_after']):
                raise ValueError('Complete P0 OFF/ON parent or physical-state parity differs')
            if [o['step'] for o in row['origins']]!=(list(SELECTED_STEPS) if row['collect'] else []):
                raise ValueError('Complete two-origin scope missing')
            for o in row['origins']:
                if (o['scene']!=request['sample_name'] or o['action']!='CC'
                        or o['methods']!=list(METHODS) or o['layers']!=list(LAYERS) or o['block_size']!=128
                        or o['past_actual_D_projection_step']!=(7 if o['step']==12 else 25)
                        or not o['actual_post_RF_original_direct_equal'] or not o['full_D_same_origin_direct_equal']
                        or not o['complete_external_and_P0_restored'] or o['teacher_updates_deployment_anchor']
                        or o['warmups']!=1 or o['repeats']!=3
                        or list(o['velocity_sha256'])!=list(METHODS)
                        or any(len(v)!=2 for v in o['velocity_sha256'].values())
                        or set(o['group_cost_seconds'])!=set(MODES)
                        or any(len(v)!=3 or any(not math.isfinite(t) or t<=0 for t in v)
                               for v in o['group_cost_seconds'].values())
                        or o['new_policy_OR_partial_video_OR_clean_end_to_end_latency_claim']):
                    raise ValueError('Complete same-origin dense/partial outputs, source or group cost scope differs')
                tokens=math.prod(o['actual_probe_shapes'][0][:-1])
                if tokens!=math.prod(o['actual_probe_shapes'][1][:-1]):
                    raise ValueError('CFG token layout differs')
                for mode in MODES:
                    observed=o['warmup_Linear_and_projection_records'][mode]
                    n=tokens if mode.startswith('DENSE') else max(1,math.floor((tokens//128)*(.5 if mode.endswith('050') else .75)))*128
                    if len(observed['Linear_inputs'])!=16 or any(v['rows']!=n for v in observed['Linear_inputs']):
                        raise ValueError('Both real Linear row counts differ from registered actual P0 quota')
                    records=observed['projection_records']
                    if mode!='DENSE_REFERENCE' and (len(records)!=8 or any(r['actual_MLP_rows']!=n or r['fallback'] for r in records)):
                        raise ValueError('True P0 projection source or physical row count missing')
                count+=1
        if len(request['prepared_input_calls'])!=2 or request['prepared_input_calls'][0]['prepared']!=request['prepared_input_calls'][1]['prepared']:
            raise ValueError('Actual P0 parent prepared inputs differ')
    if count!=8:raise ValueError('All eight actual P0 origins required')
    return {'complete_parent_paths':8,'same_state_origins':8,'post_RF_branch_tensors':112,
            'parent_solver_updates':288,'parent_net_calls':576,'score_only_group_pairs':192,
            'actual_tensor_reload_and_complete_video_decode_required':True,
            'partial_video_OR_clean_pipeline_latency_OR_independent_confirmation_claim':False}


def _compile_batch():
    original=ast.parse(dedent(inspect.getsource(parent.run_batch))).body[0]
    node=copy.deepcopy(original)
    names={'GuidedW1Collector':'_P0Collector','CollectedSchedulePairExecutor':'_P0Pair',
           'compile_collection':'_compile_P0','verify_batch':'_verify_P0'}
    counts={k:0 for k in names};extra={'count':0,'bind':0,'close':0}
    class Replace(ast.NodeTransformer):
        def visit_Name(self,n):
            if n.id in names:counts[n.id]+=1;return ast.copy_location(ast.Name(id=names[n.id],ctx=n.ctx),n)
            return n
        def visit_keyword(self,n):
            if n.arg=='planned_post_RF_branch_tensors' and isinstance(n.value,ast.Constant) and n.value.value==64:
                extra['count']+=1;n.value=ast.Constant(value=112)
            return self.generic_visit(n)
        def visit_Assign(self,n):
            value=self.generic_visit(n)
            if len(value.targets)==1 and isinstance(value.targets[0],ast.Name) and value.targets[0].id=='collector':
                extra['bind']+=1
                return [value,ast.parse("collector.scene_index = config['sample_names'].index(sample.name)").body[0]]
            if ast.unparse(value)=="capture['velocity'] = velocity":
                return [value,ast.parse('collector.velocity = velocity').body[0]]
            return value
        def visit_Expr(self,n):
            if ast.unparse(n)=='hooks.close()':
                extra['close']+=1
                return [ast.parse('collector.close()').body[0],n]
            return self.generic_visit(n)
    node=Replace().visit(node)
    if counts!={'GuidedW1Collector':1,'CollectedSchedulePairExecutor':1,'compile_collection':1,'verify_batch':1} or extra!={'count':1,'bind':1,'close':1}:
        raise ValueError('Existing complete P0 batch source transformation sites differ')
    inverse=copy.deepcopy(node);reverse={v:k for k,v in names.items()}
    class Undo(ast.NodeTransformer):
        def visit_Name(self,n):
            if n.id in reverse:return ast.copy_location(ast.Name(id=reverse[n.id],ctx=n.ctx),n)
            return n
        def visit_keyword(self,n):
            if n.arg=='planned_post_RF_branch_tensors' and isinstance(n.value,ast.Constant) and n.value.value==112:n.value=ast.Constant(value=64)
            return self.generic_visit(n)
        def visit_Assign(self,n):
            if len(n.targets)==1 and isinstance(n.targets[0],ast.Attribute) and isinstance(n.targets[0].value,ast.Name) and n.targets[0].value.id=='collector' and n.targets[0].attr in ('scene_index','velocity'):return None
            return self.generic_visit(n)
        def visit_Expr(self,n):
            if ast.unparse(n)=='collector.close()':return None
            return self.generic_visit(n)
    inverse=Undo().visit(inverse)
    if ast.dump(inverse,include_attributes=False)!=ast.dump(original,include_attributes=False):
        raise ValueError('P0 complete pipeline changed outside explicit collector bindings and cleanup')
    namespace={**vars(parent),'_P0Collector':PartialGroupCollector,'_P0Pair':PartialCollectedPair,
               '_compile_P0':compile_partial_collection,'_verify_P0':verify_partial_batch}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),
                 str(Path(__file__))+'#P0-complete-batch','exec'),namespace)
    return namespace['run_batch'],{'complete_batch_inverse_AST_equal':True,
             'parent_batch_source_sha256':hashlib.sha256(Path(parent.__file__).read_bytes()).hexdigest(),
             'explicit_rebindings':counts,'explicit_additional_state_cleanup_sites':extra,
             'full_sampler_and_guarded_return_body_preserved':True,'real_execution_or_quality_claim':False}


run_partial_batch,P0_SAMPLING_COMPILER_PROOF=_compile_batch()


def audit_partial_vectors(state,root,loader,expected_shape):
    verify_partial_batch(state);root=Path(root).resolve();files=[];moments={m:[] for m in MODES}
    def read(art):
        p=Path(art['path']).resolve()
        if not p.is_relative_to(root) or p.suffix!='.pt':raise ValueError('Actual P0 tensor outside bound output')
        raw=p.read_bytes()
        if len(raw)!=art['bytes'] or hashlib.sha256(raw).hexdigest()!=art['sha256']:raise ValueError('Actual P0 tensor changed or truncated')
        value=loader(p,map_location='cpu',weights_only=True)
        if {k:tree_digest(v) for k,v in value.items()}!=art['tensor_sha256']:raise ValueError('P0 physical tensor hash differs')
        files.append({'path':str(p),'bytes':len(raw),'sha256':art['sha256']});return value
    def finite(v):return isinstance(v,torch.Tensor) and v.dtype==torch.float32 and list(v.shape)==expected_shape and bool(torch.isfinite(v).all())
    def same(x,y):
        if isinstance(x,dict):return x.keys()==y.keys() and all(same(x[k],y[k]) for k in x)
        if isinstance(x,list):return len(x)==len(y) and all(same(a,b) for a,b in zip(x,y))
        if type(x) is float:return isinstance(y,(int,float)) and math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-12)
        return x==y
    for request in state['requests']:
        parents=[]
        for row in request['paths']:
            v=read(row['vector_artifact'])
            if set(v)!={'guided','final_latent'} or len(v['guided'])!=36 or not all(finite(t) for t in v['guided']+[v['final_latent']]):
                raise ValueError('Complete288 parent guided and eight latents required')
            if [tree_digest(t) for t in v['guided']]!=row['guided_sha256']:raise ValueError('Actual P0 parent output differs')
            parents.append(v)
            for o in row['origins']:
                bundle=read(o['artifact'])
                if list(bundle)!=list(METHODS) or any(type(p) is not tuple or len(p)!=2 or not all(finite(t) for t in p) for p in bundle.values()):
                    raise ValueError('Complete112 same-origin branch outputs required')
                if {k:[tensor_sha(t) for t in pair] for k,pair in bundle.items()}!=o['velocity_sha256']:raise ValueError('P0 origin tensor identity differs')
                c,u=bundle['ORIGINAL']
                if not torch.equal(c+7*(c-u),v['guided'][o['step']-1]):raise ValueError('Actual original CFG source order differs')
                if not all(torch.equal(a,b) for a,b in zip(bundle['DENSE_REFERENCE'],bundle['DENSE_WITH_P0'])):raise ValueError('Actual P0 dense control not equal')
                for mode in MODES:
                    m=guided_velocity_moments(scene=o['scene'],state='step'+str(o['step']),original=bundle['ORIGINAL'],proposed=bundle[mode],dense=bundle['DENSE_REFERENCE'])
                    if not same(m,o['moments'][mode]):raise ValueError('Actual P0 direct guided moments differ')
                    moments[mode].append(m)
        if not all(torch.equal(a,b) for a,b in zip(parents[0]['guided']+[parents[0]['final_latent']],parents[1]['guided']+[parents[1]['final_latent']])):raise ValueError('Physical P0 OFF/ON outputs differ')
    if len(files)!=16 or any(len(v)!=8 for v in moments.values()) or {str(p.resolve()) for p in root.rglob('*.pt')}!={r['path'] for r in files}:
        raise ValueError('Complete P0 artifact and per-method origin scope required')
    return {'actual_parent_guided_reloaded':288,'actual_parent_latents_reloaded':8,
            'actual_post_RF_branch_tensors_reloaded':112,'actual_full36_OFF_ON_direct_equal':True,
            'actual_original_CFG_recovery_direct_equal':True,'actual_full_D_control_direct_equal':True,
            'files':files,'moments':moments,'partial_video_OR_clean_pipeline_latency_claim':False}
