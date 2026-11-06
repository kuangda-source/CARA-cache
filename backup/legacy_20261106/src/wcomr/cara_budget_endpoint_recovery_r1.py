"""Recover a complete synchronous CPU callback without invoking generation.

Only the pinned CPU evaluator is supported. Its entire callback runs under the
journal flock; acquiring that lock excludes a live producer. This is not a GPU
process/guardian terminal reader and cannot authorize any new query.
"""
from pathlib import Path
import platform
import time

from . import cara_budget_search_journal_r1 as journal
from . import cara_budget_search_r1 as controller
from . import cara_fast_spec_r1 as specification
from .policy_generator_r1 import interval_grammar
from .cara_budget_rgb_objective_r1 import file_sha, read_endpoint, full_rgb_mse
from .cara_fast_spec_r1 import digest, profile_from, policy_from_mask


def expected_identity(card, binding, member, kind, request=None):
    sample=next(row for row in card['inputs'] if row['name']==member)
    return dict(context_sha256=binding['context_sha256'],original_scope_sha256=card['scope_sha256'],
        member=member,frozen_input_sha256=digest(sample),generation_seed=0,
        requested_steps=35,actual_updates=36,RGB_shape=binding['RGB_shape'],kind=kind,
        query_sha256=request['request_sha256'] if request else None,
        policy_fingerprint=request['policy']['fingerprint'] if request else None,CPU_fixture_only=True)


def recover_complete_cpu_query(directory, endpoint_root, *, card, expected_binding,
                               expected_endpoint_binding, query_id):
    profile=profile_from(card['profile'])
    source={name:file_sha(path) for name,path in (
        ('controller',controller.__file__),('journal',journal.__file__),
        ('specification',specification.__file__),('grammar',interval_grammar.__file__))}
    if (digest({k:v for k,v in card.items() if k!='scope_sha256'})!=card['scope_sha256']
            or digest(card['schedule'])!=controller.SCHEDULE_SHA256
            or profile.fingerprint!=controller.PROFILE_FINGERPRINT
            or tuple(card['FIT'])!=controller.FIT_MEMBERS
            or expected_binding['schema']!='CARA_BUDGET_SEARCH_QUERY_JOURNAL_R1'
            or expected_binding['source_sha256']!=source
            or expected_binding['python_version']!=platform.python_version()
            or expected_binding['schedule_sha256']!=digest(card['schedule'])
            or expected_binding['profile_fingerprint']!=profile.fingerprint
            or expected_binding['FIT_members']!=card['FIT']):
        raise ValueError('Pinned original CPU search/card/source binding required')
    controller.SearchConfig(**expected_binding['config'])
    binding=expected_endpoint_binding
    evaluator=Path(__file__).with_name('cara_budget_endpoint_requests_r1.py')
    shape=binding['RGB_shape']
    if (binding['CPU_fixture_only'] is not True or binding['evaluator_source_sha256']!=file_sha(evaluator)
            or binding['original_scope_sha256']!=card['scope_sha256']
            or binding['context_sha256']!=expected_binding['context_sha256']
            or len(shape)!=4 or shape[:2]!=[3,93] or any(type(n) is not int or n<=0 for n in shape)
            or type(query_id) is not int or query_id<1):
        raise ValueError('Exact synchronous CPU endpoint binding required')
    root=Path(endpoint_root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Original endpoint directory required')
    with journal.QueryJournal(directory,expected_binding) as owner:
        if journal.read_record(root/'binding.json')!=binding:
            raise ValueError('Original endpoint context differs')
        request=journal.read_record(owner.path(query_id,'intent'))
        if (request['query_id']!=query_id or tuple(request['FIT_members'])!=controller.FIT_MEMBERS
                or request['generation_seed']!=0 or request['requested_steps']!=35
                or request['actual_updates']!=36 or request['D_pair_budget']!=19
                or len(request['dense'])!=19 or 24 not in request['dense']
                or policy_from_mask(profile,request['dense'])!=request['policy']):
            raise ValueError('Original fixed19D complete cohort request required')
        returned=owner.path(query_id,'return')
        if returned.exists():
            payload=owner.read_return(request)
            if payload['kind']!='RETURNED':
                raise ValueError('Original callback error is terminal; never replace it')
            return dict(status='ORIGINAL_RETURN_ALREADY_PRESENT',response=payload['response'],
                        new_return_written=False,new_generation_calls=0,GPU_dispatch_ready=False)
        if query_id!=owner.persisted_intents:
            raise ValueError('Only the last unresolved original intent can be recovered')
        arrays=[];evidence={}
        # Validate all four complete artifacts before calculating any MSE.
        for index,member in enumerate(controller.FIT_MEMBERS):
            pair=[]
            for candidate in (False,True):
                name=f'query-{query_id:06d}-FIT{index}' if candidate else f'teacher-FIT{index}'
                physical=root/name
                if physical.is_symlink() or not physical.is_dir():
                    raise journal.OriginalQueryUnknown('Missing original physical endpoint: '+name)
                identity=expected_identity(card,binding,member,'CANDIDATE' if candidate else 'NATIVE',request if candidate else None)
                proof=journal.read_record(physical/'result.json')
                if (journal.read_record(physical/'intent.json')!=identity or proof['identity']!=identity
                        or proof['status']!='COMPLETE' or proof['solver_steps']!=36 or proof['guided_pairs']!=36
                        or proof['actual_D']!=(19 if candidate else 36) or proof['RGB_captures']!=1
                        or proof['CPU_fixture_only'] is not True or proof['actual_model_weights']
                        or proof['policy_exact_without_fallback']!=candidate):
                    raise ValueError('Complete original CPU request proof differs: '+name)
                rgb,receipt=read_endpoint(physical/'endpoint',identity)
                pair.append((rgb,receipt))
                evidence[name]=dict(result_sha256=file_sha(physical/'result.json'),
                    endpoint_complete_sha256=file_sha(physical/'endpoint/complete.json'),
                    RGB_sha256=receipt['RGB_sha256'])
            arrays.append((member,pair))
        rows=[]
        for member,((teacher,native),(rgb,observed)) in arrays:
            rows.append(dict(member=member,status='COMPLETE',RGB_MSE=full_rgb_mse(rgb,teacher),
                candidate_RGB_sha256=observed['RGB_sha256'],teacher_RGB_sha256=native['RGB_sha256'],
                complete_frames=93,CPU_fixture_only=True))
        response=dict(request_sha256=request['request_sha256'],rows=rows)
        recovery=dict(kind='COMPLETE_SYNCHRONOUS_CPU_ENDPOINTS_UNDER_ORIGINAL_JOURNAL_LOCK',
            observed_unix=time.time(),reader_source_sha256=file_sha(__file__),
            endpoint_binding_sha256=digest(binding),original_artifacts=evidence,
            new_generation_calls=0,GPU_process_terminal_verified=False)
        owner.persist_return(request,dict(kind='RETURNED',response=response,recovery=recovery))
        return dict(status='ORIGINAL_COMPLETE_CPU_CALLBACK_RECOVERED',response=response,recovery=recovery,
                    new_return_written=True,new_generation_calls=0,GPU_dispatch_ready=False)
