"""Bounded blocks of the unchanged current-birth sampler and qualified scope.

No controller, forward, readout, physical checkpoint or density change. The
CPU-only control uses the original additional-state owner and original prepare
writer timing to measure the wiring/storage delta on identical Toy weights.
"""
import inspect
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

from . import e1_memory_diagnostic_sampling_r1 as proof_tools
from . import source_aware_partial_sampling as base
from . import source_aware_working_epoch_sampling_r1 as working
from . import source_aware_current_birth_sampling_r2 as original
from . import source_aware_CPU_storage_sampling_r1 as storage
from .source_aware_phase_sampling import bind_globals
from .prepared_input_persistence_r1 import bind_prepared_input_persistence
from .e3_complete64_block_scope_r1 import validate_scope,validate_block


def make_verifier(block,scope):
    names,methods=validate_block(block,scope);count=len(block['paths'])
    source=dedent(inspect.getsource(base.verify_batch))
    changes=[("state.get('planned_parent_paths')!=32 or len(state.get('requests',[]))!=4",
              "state.get('planned_parent_paths')!=_PATH_COUNT or len(state.get('requests',[]))!=len(_NAMES)"),
        ("tuple(r['collect'] for r in rows)!=METHODS or len(request['prepared_input_calls'])!=8",
         "tuple(r['collect'] for r in rows)!=_METHODS[request['sample_name']] or len(request['prepared_input_calls'])!=len(rows)"),
        ("or p['accumulated_interval_proxy_after']<p['decision']['state_before'][4]",
         "or not valid_P_interval(p,d['working_epoch_strategy'])"),
        ("'complete_paths':32,'solver_updates':1152,'normal_net_calls':2304",
         "'complete_paths':_PATH_COUNT,'solver_updates':36*_PATH_COUNT,'normal_net_calls':72*_PATH_COUNT")]
    changed,proof=proof_tools._transform(source,changes)
    ns={**vars(base),'_NAMES':names,'_METHODS':methods,'_PATH_COUNT':count,
        'valid_P_interval':working.valid_P_interval}
    exec(compile(changed,__file__+'#registered-block-verifier','exec'),ns)
    epoch=bind_globals(working.verify_batch,{'_verify_base':ns['verify_batch']})
    current=bind_globals(original.verify_batch,{'working':SimpleNamespace(verify_batch=epoch)})
    def verify(state):
        if [q['sample_name'] for q in state.get('requests',[])]!=names:
            raise ValueError('All paths in the exact declared E3 block required')
        result=current(state)
        for request in state['requests']:
            for row in request['paths']:
                deployment=row['collection_complete'].get('deployment')
                if deployment is not None and deployment['working_epoch_strategy']!=block['strategy']:
                    raise ValueError('E3 block source strategy differs')
        return {**result,'E3_block':block['id'],'original64_scientific_positions':64,
            'declared_block_paths':count,'scope_derivation':proof}
    return verify


def compile_batch(block,scope,*,calibration,policy_specs,CPU_original_control=False):
    names,methods=validate_block(block,scope)
    if CPU_original_control and proof_tools.torch.cuda.is_initialized():
        raise ValueError('Original-owner pairing control is CPU-only')
    if set(policy_specs)!=set(original.METHODS) or any(v.get('working_epoch_strategy')!=block['strategy'] for v in policy_specs.values()):
        raise ValueError('Complete unchanged parameters for the selected source strategy required')
    owner=original.CurrentBirthSamplingOwner if CPU_original_control else storage.CurrentBirthSamplingOwner
    def factory(model,method,context,runtime,wc,rf):
        spec=policy_specs[method]
        if method=='SOURCE_RA':
            return base.SourceRAOwner(model,context=context,runtime=runtime,wc=wc,rf=rf,
                calibration=calibration,threshold=spec['threshold'])
        return owner(model,method=method,context=context,runtime=runtime,wc=wc,rf=rf,
            calibration=calibration,spec=spec)
    source=dedent(inspect.getsource(proof_tools.p0.parent.run_batch))
    start=source.index('                collector = GuidedW1Collector(')
    end=source.index('                factory,proof = compile_velocity',start)
    old_owner=source[start:end]
    new_owner="""                collector = _owner(model,collect,context,runtime,wc,rf_module)
                executor = collected = collector
                core = collector.compiler
"""
    changes=[('len(samples) != 4 or len(contexts) != 4','len(samples) != len(_NAMES) or len(contexts) != len(_NAMES)'),
        ('Complete guarded four-request guided-W1 calibration batch required','Complete guarded E3 registered block required'),
        ('planned_parent_paths=8,planned_origins=8,planned_post_RF_branch_tensors=64',
         'planned_parent_paths=_PATH_COUNT,planned_origins=0,planned_post_RF_branch_tensors=0'),
        ("calibration_collection_policy='UNIFORM_SHARED_D6'","calibration_collection_policy='E3_REGISTERED_CURRENT_BIRTH_BLOCK'"),
        ('selected_steps=list(SELECTED_STEPS)','selected_steps=[]'),
        ('for collect in (False,True):','for collect in _METHODS[sample.name]:'),
        ("label = sample.name+('_COLLECT_ON' if collect else '_COLLECT_OFF')","label = sample.name+'_'+collect"),
        (old_owner,new_owner),("row['origins'] = collector.records","row['origins'] = []"),
        ("row.setdefault('capture_gates',[]).append({'step':step,**gate})",
         "row.setdefault('capture_gates',[]).append({'step':step,**gate})\n                        row.setdefault('P0_roundtrips',[]).append({'step':step,**collector.checkpoint(snapshot,gate,config)})"),
        ('verdict=verify_batch(state)','verdict=_verify_batch(state)'),
        ('                    hooks.close()','                    collector.close()\n                    hooks.close()')]
    changed,proof=proof_tools._transform(source,changes)
    ns={**vars(proof_tools.p0.parent),'_owner':factory,'_NAMES':names,'_METHODS':methods,
        '_PATH_COUNT':len(block['paths']),'_verify_batch':make_verifier(block,scope)}
    exec(compile(changed,__file__+'#ordinary-registered-E3-block','exec'),ns)
    batch=ns['run_batch']
    def run(*args,**kwargs):
        if kwargs['config']['sample_names']!=names:
            raise ValueError('Exact E3 request subset and order required')
        if not CPU_original_control:
            return bind_prepared_input_persistence(batch,state=kwargs['state'],save=kwargs['save'])(*args,**kwargs)
        return batch(*args,**kwargs)
    return run,{**proof,'E3_block':block['id'],'scope_counts':validate_scope(scope),
        'block_paths':len(block['paths']),'source_RA_owner_unchanged':True,
        'CPU_original_control_not_production_selected':CPU_original_control,
        'original_physical_pre_snapshot_two_copy_gate_unchanged':True,
        'CPU_storage_owner_and_prepare_metadata_binding_only':not CPU_original_control}


def audit_vectors(state,block,scope,root,loader,expected_shape):
    # Reuse the full accepted file reader; substitute only its exact block verifier.
    def verifier(_):return make_verifier(block,scope)
    reader=bind_globals(proof_tools.audit_vectors,{'make_verifier':verifier})
    result=reader(state,block,Path(root),loader,expected_shape)
    result['E3_block']=block['id'];return result
