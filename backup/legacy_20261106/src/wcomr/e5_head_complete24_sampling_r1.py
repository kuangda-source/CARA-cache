"""Whole six-path real-head block; four fresh blocks comprise the 24-path card.

The owner/readout/controller bodies are the complete-CPU-tested R4/legacy
objects. Only sample scope, registered ordering and actual input bindings
are derived here. Instrumented timings include checkpoints and observation.
"""
import ast
import hashlib
import inspect
from pathlib import Path
from textwrap import dedent

from . import partial_mlp_deployment_sampling as p0
from .source_aware_CPU_storage_sampling_r1 import CPUStorageSamplingOwner
from .early_head_elision_sampling_r4 import CurrentBirthEarlyHeadSamplingOwner, VERSION
from .e5_cross_version_policy_receipt_r1 import assert_policy_equivalent

AV='av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632'
MODES=('OFF','W1_ONE_PHASE','BETA1_ONE_PHASE')
METHODS=tuple(v+'_'+a for a in MODES for v in ('LEGACY','FAST'))
ARMS=tuple({'id':tag+'_R'+str(rep),'sample_name':name,'repetition':rep,
    'methods':list(METHODS if rep==1 else METHODS[::-1])}
    for rep in (1,2) for tag,name in (('AV',AV),('HUMAN','human_199')))


def validate_arm(arm):
    if arm not in ARMS or type(arm) is not dict:
        raise ValueError('One exact registered six-path block required')
    return arm['sample_name'],tuple(arm['methods'])


def verify_block(state,arm):
    name,methods=validate_arm(arm)
    if state['planned_parent_paths']!=6 or state['planned_origins']!=0 or len(state['requests'])!=1:
        raise ValueError('Complete six-path block required')
    request=state['requests'][0];rows=request['paths']
    if (request['sample_name']!=name or tuple(r['collect'] for r in rows)!=methods
            or len(request['prepared_input_calls'])!=6
            or any(r['prepared']!=request['prepared_input_calls'][0]['prepared']
                   for r in request['prepared_input_calls'])):
        raise ValueError('Whole ordered methods and identical original prepared inputs required')
    for row in rows:
        c=row['collection_complete'];d=c['deployment'];a=d['A_readout'];h=a['history']
        mode=row['collect'].split('_',1)[1];fast=row['collect'].startswith('FAST_')
        if (row['status']!='COMPLETE_PARENT_PATH' or len(row['guided_sha256'])!=36
                or len(row['solver_returns'])!=36 or len(h)!=36 or len(row['actions'])!=36
                or row['counters']!=list(range(0,70,2))+[0]
                or [p['step'] for p in row['P0_roundtrips']]!=[12,30,35,36]
                or not all(p['physical_state_restored'] and p['complete_additional_state_restored']
                           for p in row['P0_roundtrips'])
                or not row['all_modules_eval'] or not row['parameter_versions_unchanged']
                or row['conditions_before']!=row['conditions_after']
                or row['condition_fields_before']!=row['condition_fields_after']
                or a['teacher_calls'] or a['extra_candidate_deep_blocks']
                or [x['action'] for x in d['history']]!=row['actions']):
            raise ValueError('Complete unchanged solver/condition/source and healthy restore required')
        paid=len(c['actual_original_plus_candidate_heads'])
        if state['actual_native_leaf_profile_counts'].get(row['collect'],0)!=paid:
            raise ValueError('Actual native leaf calls disagree with paid source records')
        if fast:
            if (a['early_head_version']!=VERSION or paid!=a['total_head_calls']
                    or a['native_head_contract']['use_adaln_lora'] is not True
                    or a['native_head_contract']['use_wan_fp32_strategy'] is not True
                    or a['native_head_contract']['unpatchify']!='PINNED_NATIVE_UNPATCHIFY'
                    or a['native_head_contract']['checkpoint_wrapper']!='PINNED_NATIVE_NON_REENTRANT_SELECTIVE'
                    or any(x['early_head_version']!=VERSION for x in h)):
                raise ValueError('Real native R4 head/unpatchify/accounting contract differs')
            if any(any(x['original_head_elided']) for x in h if x['action']!='CC' or x['shared_alpha']!=1):
                raise ValueError('Elision outside actual alpha=1 C')
        elif paid!=72+a['extra_candidate_heads']:
            raise ValueError('Original paid head accounting differs')
        if mode=='OFF' and paid!=72:
            raise ValueError('OFF must remain the unchanged 72-head control')
        for x in d['history']:
            if x['action']!='DD' and x['true_D_before']!=x['true_D_after']:
                raise ValueError('C/P changed true D statistics')
            if x['action']=='PP' and (x['source_policy']['creation_floor_proxy_after']<=0
                    or any(s['RA_zero_risk_reset_allowed'] for s in x['working_sources'])):
                raise ValueError('P became zero-error or true D')
    pairs=[]
    for mode in MODES:
        left,right=[next(r for r in rows if r['collect']==v+'_'+mode) for v in ('LEGACY','FAST')]
        for key in ('guided_sha256','guided_list_sha256','final_latent_sha256','sample_return_sha256',
                    'solver_returns','actions','rng_after','condition_fields_before','condition_fields_after',
                    'actual_raw_solver_configuration'):
            if left[key]!=right[key]:raise ValueError('Real old/new outputs or decisions differ: '+key)
        if ('video_artifact' in left)!=('video_artifact' in right):
            raise ValueError('Paired guardrail/video status differs')
        # The independent reader compares all decoded frames. Container bytes
        # remain separately hashed; encoder metadata need not be identical.
        ld,rd=[r['collection_complete']['deployment'] for r in (left,right)]
        assert_policy_equivalent(ld['history'],rd['history'])
        for x,y in zip(ld['history'],rd['history']):
            for key in ('true_D_before','true_D_after','working_source_ages','working_sources','actual_projection_records'):
                if x[key]!=y[key]:raise ValueError('Real source/projection history differs: '+key)
        heads=[len(r['collection_complete']['actual_original_plus_candidate_heads']) for r in (left,right)]
        saved=sum(sum(x['original_head_elided']) for x in rd['A_readout']['history'])
        if heads[0]-heads[1]!=saved or mode=='OFF' and saved:
            raise ValueError('Actual paid heads disagree with elision')
        if mode!='OFF' and not saved:
            raise ValueError('Real block failed to exercise the registered elision')
        pairs.append({'mode':mode,'actual_legacy_heads':heads[0],'actual_new_heads':heads[1],
            'actual_elided_heads':saved,'exact_output_hashes_equal':True,
            'instrumented_wall_seconds':[r['instrumented_parent_pipeline_wall_seconds'] for r in (left,right)]})
    return {'complete_paths':6,'updates':216,'CFG_calls':432,'pairs':pairs,
        'source_policy_semantic_fields_equal':True,'clean_latency_or_quality_frontier_claim':False,
        'full_written_tensor_and_video_reads_still_required':True}


def compile_block(arm,*,calibration,policy_specs):
    name,methods=validate_arm(arm)
    base=dedent(inspect.getsource(p0.parent.run_batch))
    changed=base.replace('len(samples) != 4 or len(contexts) != 4',
                        'len(samples) != 1 or len(contexts) != 1')
    if changed==base or changed.replace('len(samples) != 1 or len(contexts) != 1',
                                       'len(samples) != 4 or len(contexts) != 4')!=base:
        raise ValueError('Original whole guarded parent scope changed')
    def owner(model,method,context,runtime,wc,rf):
        mode=method.split('_',1)[1];actual='A_CPD_'+mode
        cls=CurrentBirthEarlyHeadSamplingOwner if method.startswith('FAST_') else CPUStorageSamplingOwner
        return cls(model,method=actual,context=context,runtime=runtime,wc=wc,rf=rf,
                   calibration=calibration,spec=policy_specs[actual])
    source=dedent(inspect.getsource(p0._derive))
    old='source = dedent(inspect.getsource(parent.run_batch))';new='source = _e5_parent_source()'
    count='planned_parent_paths=52,planned_origins=0';new_count='planned_parent_paths=6,planned_origins=0'
    if source.count(old)!=1 or source.count(count)!=1:
        raise ValueError('Original P0 compiler scope changed')
    edited=source.replace(old,new).replace(count,new_count)
    inverse=edited.replace(new,old).replace(new_count,count)
    if inverse!=source or ast.dump(ast.parse(inverse))!=ast.dump(ast.parse(source)):
        raise ValueError('Unregistered parent/owner compiler edit')
    ns={**p0._derive.__globals__,'_e5_parent_source':lambda:changed,'METHODS':methods,
        '_owner':owner,'verify_batch':lambda state:verify_block(state,arm),'__file__':__file__}
    exec(compile(edited,__file__+'#whole-six-path-scope','exec'),ns)
    batch,proof=ns['_derive']()
    return batch,{**proof,'E5_scope_inverse_bytes_AST_equal':True,'arm':arm,
        'numerical_owner_modules_unchanged':['source_aware_CPU_storage_sampling_r1','early_head_elision_sampling_r4'],
        'source_file_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
