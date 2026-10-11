"""Complete four-parent/four-window, five-readout diagnostic per flow mode."""
import copy
import inspect
from textwrap import dedent

from . import e4c_matched_source_age_sampling_r1 as old
from .p_reference_same_state_owner_r1 import SameStateReferenceOwner, VARIANTS
from .cfg_guided_w1_deployment import alpha_at


def verify_batch(state,scope):
    # Reuse every original parent/source/teacher/suffix/condition check. The
    # original verifier is not an authority for the extra four readouts.
    base=old.verify_batch(state,scope)
    points=0
    for request in state['requests']:
        for row in request['paths']:
            for event in row['origins']:
                for branch in event['branches']:
                    for point in branch['age_points']:
                        records=point['five_reference_readouts']
                        if (tuple(r['variant'] for r in records)!=VARIANTS
                                or not point['all_candidates_same_actual_input_and_full_source']
                                or point['deployed_reference_unchanged']!='D_REFERENCE_SCALAR'
                                or len(point['serial_restore_guards'])!=5
                                or any(r['input_sha256']!=point['input_sha256']
                                       or r['source']!=branch['source'] or r['age']!=point['age']
                                       or r['step']!=point['step'] for r in records)
                                or len({r['source_cache_sha256'] for r in records})!=1
                                or len({r['true_D_full_state_sha256'] for r in records})!=1
                                or [r['deployed_after_scoring'] for r in records]!=[False]*4+[True]
                                or any(r['actual_head_calls']!=2+r['readout']['extra_heads'] for r in records)
                                or records[0]['actual_head_calls']!=2
                                or len(point['research_teacher_actual_head_events'])!=2
                                or any(len(r['actual_head_events'])!=r['actual_head_calls'] for r in records)
                                or records[-1]['guided_moments']!=point['same_state_guided_moments']):
                            raise ValueError('All five same-state readouts and complete restores required')
                        for r in records:
                            mode='OFF' if r['variant']=='OFFICIAL_C' else 'W1_ONE_PHASE'
                            if r['readout']['shared_alpha']!=alpha_at(mode,point['step']):
                                raise ValueError('Registered shared phase strength differs')
                            for proof in r['readout']['P_reference']:
                                if proof is not None and (r['source']!='P'
                                        or not r['variant'].startswith('P_REFERENCE')
                                        or proof['true_D_full_state_before_sha256']!=proof['true_D_full_state_after_sha256']):
                                    raise ValueError('P-reference provenance or true-D protection differs')
                        points+=1
    if points!=24 or scope['scope_counts']['total_pair_computations']!=344:
        raise ValueError('Whole24 points and344 actual pairs per flow required')
    return {**base,'same_state_readout_comparisons':120,
            'total_pair_computations':344,'total_CFG_calls':688,
            'diagnostics_leave_old_D_scalar_deployment_unchanged':True}


_source=dedent(inspect.getsource(old.compile_batch))
_before="scope['scope_counts']['total_pair_computations'] != 248"
_after="scope['scope_counts']['total_pair_computations'] != 344"
if _source.count(_before)!=1:raise ValueError('Original whole diagnostic scope precondition differs')
_changed=_source.replace(_before,_after)
if _changed.replace(_after,_before)!=_source:raise ValueError('Unregistered sampler scope edit')
_ns={**old.compile_batch.__globals__,'MatchedSourceAgeOwner':SameStateReferenceOwner,
     'verify_batch':verify_batch,'__file__':__file__}
exec(compile(_changed,__file__+'#complete-same-state-owner-binding','exec'),_ns)
compile_batch=_ns['compile_batch']
