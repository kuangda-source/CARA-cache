"""E1 fixed diagnostic scope on the unchanged current-birth physical sampler.

Only the declared request/method loops and verification scope are smaller.
All owner implementations, guardrails, physical checkpoints and arithmetic
remain original. Metadata observers never retain owners or tensor references.
"""
import ast
import hashlib
import inspect
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

import torch

from . import partial_mlp_deployment_sampling as p0
from . import source_aware_partial_sampling as base
from . import source_aware_working_epoch_sampling_r1 as working
from . import source_aware_current_birth_sampling_r2 as original
from . import source_aware_CPU_storage_sampling_r1 as storage
from .source_aware_phase_sampling import bind_globals
from .cpu_owned_state_snapshot import storage_inventory

AV='av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632'
HUMAN='human_199'
TARGET={'sample_name':HUMAN,'method':'A_CPD_BETA1_ONE_PHASE'}
PREFIX=[{'sample_name':AV,'method':'A_CPD_BETA1_ONE_PHASE'},
        {'sample_name':HUMAN,'method':'A_CPD_W1_ONE_PHASE'},TARGET]
ARMS=[{'id':'ORIGINAL_COLD','storage':'ORIGINAL_GPU_DEEPCOPY','paths':[TARGET]},
      {'id':'CPU_COLD','storage':'CPU_OWNED_STORAGE_SERIAL_RESTORE_R1','paths':[TARGET]},
      {'id':'ORIGINAL_PREFIX','storage':'ORIGINAL_GPU_DEEPCOPY','paths':PREFIX},
      {'id':'CPU_PREFIX','storage':'CPU_OWNED_STORAGE_SERIAL_RESTORE_R1','paths':PREFIX}]


def validate_arm(arm):
    if arm not in ARMS:raise ValueError('Only one exact registered E1 arm allowed')
    names=list(dict.fromkeys(p['sample_name'] for p in arm['paths']))
    methods={n:tuple(p['method'] for p in arm['paths'] if p['sample_name']==n) for n in names}
    return names,methods


def _transform(source,changes):
    changed=source
    for before,after in changes:
        if changed.count(before)!=1:raise ValueError('Pinned E1 scope transformation changed: '+before[:80])
        changed=changed.replace(before,after,1)
    inverse=changed
    for before,after in reversed(changes):
        if inverse.count(after)!=1:raise ValueError('E1 transformation inverse ambiguous')
        inverse=inverse.replace(after,before,1)
    if inverse!=source or ast.dump(ast.parse(inverse))!=ast.dump(ast.parse(source)):
        raise ValueError('E1 changed arithmetic or ordinary physical pipeline')
    return changed,{'explicit_sites':len(changes),'inverse_bytes_and_AST_equal':True,
        'original_function_source_sha256':hashlib.sha256(source.encode()).hexdigest()}


def make_verifier(arm):
    names,methods=validate_arm(arm);count=len(arm['paths'])
    source=dedent(inspect.getsource(base.verify_batch))
    changes=[("state.get('planned_parent_paths')!=32 or len(state.get('requests',[]))!=4",
              "state.get('planned_parent_paths')!=_E1_PATH_COUNT or len(state.get('requests',[]))!=len(_E1_NAMES)"),
             ("tuple(r['collect'] for r in rows)!=METHODS or len(request['prepared_input_calls'])!=8",
              "tuple(r['collect'] for r in rows)!=_E1_METHODS[request['sample_name']] or len(request['prepared_input_calls'])!=len(rows)"),
             ("or p['accumulated_interval_proxy_after']<p['decision']['state_before'][4]",
              "or not valid_P_interval(p,d['working_epoch_strategy'])"),
             ("'complete_paths':32,'solver_updates':1152,'normal_net_calls':2304",
              "'complete_paths':_E1_PATH_COUNT,'solver_updates':36*_E1_PATH_COUNT,'normal_net_calls':72*_E1_PATH_COUNT")]
    changed,proof=_transform(source,changes)
    ns={**vars(base),'_E1_NAMES':names,'_E1_METHODS':methods,'_E1_PATH_COUNT':count,
        'valid_P_interval':working.valid_P_interval}
    exec(compile(changed,__file__+'#registered-scope-verifier','exec'),ns)
    epoch=bind_globals(working.verify_batch,{'_verify_base':ns['verify_batch']})
    current=bind_globals(original.verify_batch,{'working':SimpleNamespace(verify_batch=epoch)})
    def verify(state):
        if [q['sample_name'] for q in state.get('requests',[])]!=names:
            raise ValueError('All E1 registered samples must remain in order')
        result=current(state)
        if result['working_epoch_strategy']!='WORKING_P_AGE_KEEP_INTERVAL':
            raise ValueError('E1 original failure strategy required')
        return {**result,'E1_arm':arm['id'],'scope_derivation':proof,
            'current_birth_and_working_epoch_semantic_checks_preserved':True}
    return verify


def memory():
    if not torch.cuda.is_initialized():return {'status':'CPU_ONLY_NO_CUDA_INITIALIZATION'}
    free,total=torch.cuda.mem_get_info()
    return {'allocated_bytes':torch.cuda.memory_allocated(),'reserved_bytes':torch.cuda.memory_reserved(),
        'free_bytes':free,'total_bytes':total,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),
        'peak_reserved_bytes':torch.cuda.max_memory_reserved()}


def compile_batch(arm,*,calibration,policy_specs,sink):
    names,methods=validate_arm(arm)
    if set(policy_specs)!=set(original.METHODS):
        raise ValueError('Original complete method parameter bindings remain required')
    if any(v['working_epoch_strategy']!='WORKING_P_AGE_KEEP_INTERVAL' for v in policy_specs.values()):
        raise ValueError('E1 strategy or source calibration differs')
    owner_class=original.CurrentBirthSamplingOwner if arm['storage']=='ORIGINAL_GPU_DEEPCOPY' else storage.CurrentBirthSamplingOwner
    active={}
    def emit(event,**data):
        try:observed=memory()
        except (RuntimeError,OSError) as error:observed={'status':'OBSERVATION_UNKNOWN','error':str(error)}
        sink({'arm':arm['id'],'event':event,**active,**data,'memory':observed})
    class ObservedOwner(owner_class):
        def checkpoint(self,physical,gate,config):
            # Inventory contains only scalars, never saved tensor references.
            inventory=storage_inventory(self.own_state())
            emit('BEFORE_ADDITIONAL_STATE',step=self.step,physical_gate=gate,
                additional_owned_storage=inventory)
            try:
                result=owner_class.checkpoint(self,physical,gate,config)
            except BaseException as error:
                emit('ADDITIONAL_STATE_FAILED',step=self.step,error_type=type(error).__name__,error=str(error));raise
            emit('AFTER_ADDITIONAL_RESTORE_AND_RELEASE',step=self.step,
                additional_owned_storage=storage_inventory(self.own_state()))
            return result
    def factory(model,method,context,runtime,wc,rf):
        active.update(sample_name=context[0].rsplit(':',1)[-1],method=method)
        return ObservedOwner(model,method=method,context=context,runtime=runtime,wc=wc,rf=rf,
            calibration=calibration,spec=policy_specs[method])
    source=dedent(inspect.getsource(p0.parent.run_batch))
    start=source.index('                collector = GuidedW1Collector(')
    end=source.index('                factory,proof = compile_velocity',start)
    old_owner=source[start:end]
    new_owner="""                collector = _owner(model,collect,context,runtime,wc,rf_module)
                executor = collected = collector
                core = collector.compiler
"""
    changes=[('len(samples) != 4 or len(contexts) != 4','len(samples) != len(_E1_NAMES) or len(contexts) != len(_E1_NAMES)'),
        ("Complete guarded four-request guided-W1 calibration batch required","Complete guarded E1 fixed diagnostic path batch required"),
        ('planned_parent_paths=8,planned_origins=8,planned_post_RF_branch_tensors=64',
         'planned_parent_paths=_E1_PATH_COUNT,planned_origins=0,planned_post_RF_branch_tensors=0'),
        ("calibration_collection_policy='UNIFORM_SHARED_D6'","calibration_collection_policy='E1_REGISTERED_CURRENT_BIRTH_DIAGNOSTIC'"),
        ('selected_steps=list(SELECTED_STEPS)','selected_steps=[]'),
        ('for collect in (False,True):',"for collect in _E1_METHODS[sample.name]:"),
        ("label = sample.name+('_COLLECT_ON' if collect else '_COLLECT_OFF')","label = sample.name+'_'+collect"),
        (old_owner,new_owner),("row['origins'] = collector.records","row['origins'] = []"),
        ("row.setdefault('capture_gates',[]).append({'step':step,**gate})",
         "row.setdefault('capture_gates',[]).append({'step':step,**gate})\n                        row.setdefault('P0_roundtrips',[]).append({'step':step,**collector.checkpoint(snapshot,gate,config)})"),
        ('verdict=verify_batch(state)','verdict=_verify_batch(state)'),
        ('                    hooks.close()','                    collector.close()\n                    hooks.close()')]
    changed,proof=_transform(source,changes)
    def observed_gate(inventory,**kwargs):
        emit('BEFORE_PHYSICAL_CAPTURE_GATE',physical_inventory=inventory)
        try:return p0.parent.capture_gate(inventory,**kwargs)
        except BaseException as error:
            emit('PHYSICAL_GATE_FAILED',error_type=type(error).__name__,error=str(error));raise
    ns={**vars(p0.parent),'_owner':factory,'_E1_NAMES':names,'_E1_METHODS':methods,
        '_E1_PATH_COUNT':len(arm['paths']),'_verify_batch':make_verifier(arm),'capture_gate':observed_gate}
    exec(compile(changed,__file__+'#guarded-current-birth-diagnostic','exec'),ns)
    batch=ns['run_batch']
    def run(*args,**kwargs):
        if kwargs['config']['sample_names']!=names:
            raise ValueError('Exact E1 request subset/order required')
        return batch(*args,**kwargs)
    return run,{**proof,'E1_arm':arm['id'],'paths':len(arm['paths']),
        'owner_arithmetic_and_checkpoint_body_unchanged':True,'observation_retains_no_tensors_or_owner_objects':True}


def audit_vectors(state,arm,root,loader,expected_shape):
    verdict=make_verifier(arm)(state);root=Path(root).resolve();files=[]
    for request in state['requests']:
        for row in request['paths']:
            art=row['vector_artifact'];path=Path(art['path']).resolve()
            if (not path.is_relative_to(root) or path.suffix!='.pt' or path.stat().st_size!=art['bytes']
                    or hashlib.sha256(path.read_bytes()).hexdigest()!=art['sha256']):
                raise ValueError('Truncated or changed E1 vector file')
            values=loader(path,map_location='cpu',weights_only=True)
            if (set(values)!={'guided','final_latent'} or len(values['guided'])!=36
                    or any(list(t.shape)!=expected_shape or t.dtype!=torch.float32 or not bool(torch.isfinite(t).all())
                           for t in values['guided']+[values['final_latent']])
                    or {k:p0.tree_digest(v) for k,v in values.items()}!=art['tensor_sha256']
                    or [p0.tree_digest(t) for t in values['guided']]!=row['guided_sha256']):
                raise ValueError('Actual E1 guided/final tensor identity differs')
            files.append(art)
    return {'verdict':verdict,'actual_guided_reloaded':36*len(files),'actual_final_latents_reloaded':len(files),
        'files':files,'not_real_video_quality_or_speed_claim':True}
