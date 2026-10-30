"""Complete calibration orchestration on registered production request routes.

CPU preparation only. The GPU guardian, admission and complete lifecycle reader
must be bound separately before this can become a production dispatch entry.
"""
import copy
from dataclasses import asdict
import fcntl
from pathlib import Path

import numpy as np

from .cara_budget_storage_r1 import StorageLimits, check_scope, generation_snapshot, check_path_metadata
from .cara_budget_search_r1 import SearchConfig, FIT_MEMBERS, SCHEDULE_SHA256, PROFILE_FINGERPRINT
from .cara_budget_search_journal_r1 import create_record, read_record, sync_directory, run_search, OriginalQueryUnknown
from .cara_budget_rgb_objective_r1 import save_endpoint, read_endpoint, full_rgb_mse, file_sha
from .cara_fast_spec_r1 import digest, profile_from, policy_from_mask


class Calibration:
    def __init__(self, *, root, card, config, context_sha256, RGB_shape, execute,
                 cpu_validation=False, create=False, storage_limits=None):
        if cpu_validation is not True:
            raise ValueError('Whole GPU calibration is not yet admitted; CPU preparation only')
        self.card=copy.deepcopy(card);self.profile=profile_from(card['profile'])
        if (digest({k:v for k,v in card.items() if k!='scope_sha256'})!=card['scope_sha256']
                or digest(card['schedule'])!=SCHEDULE_SHA256 or self.profile.fingerprint!=PROFILE_FINGERPRINT
                or tuple(card['FIT'])!=FIT_MEMBERS or not isinstance(config,SearchConfig)
                or config.sa_iterations<1 or config.hc_iterations<1
                or config.max_evaluations!=1+config.sa_iterations+config.hc_iterations*config.hc_neighbors):
            raise ValueError('Original grid and complete configured SA plus HC query budget required')
        if (len(context_sha256)!=64 or any(c not in '0123456789abcdef' for c in context_sha256)
                or len(RGB_shape)!=4 or list(RGB_shape[:2])!=[3,93]
                or any(type(n) is not int or n<=0 for n in RGB_shape)):
            raise ValueError('Bound context and complete RGB geometry required')
        self.root=Path(root);self.config=config;self.context=context_sha256;self.shape=list(RGB_shape)
        if storage_limits is not None and not isinstance(storage_limits,StorageLimits):
            raise ValueError('Explicit storage limits required')
        self.storage_limits=storage_limits
        self.execute=execute;self.physical_calls=0;self.allow_new=False
        self.binding=dict(CPU_fixture_only=True,scope_sha256=card['scope_sha256'],context_sha256=context_sha256,
            config=vars(config),RGB_shape=self.shape,source_sha256=file_sha(__file__),
            storage_limits=asdict(storage_limits) if storage_limits else None)
        if create:
            self.root.mkdir(mode=0o700);sync_directory(self.root.parent)
            create_record(self.root/'binding.json',self.binding);create_record(self.root/'calibration.lock',{})
        if read_record(self.root/'binding.json')!=self.binding:
            raise ValueError('Original complete calibration binding differs')

    def physical(self, name, member, role, timing, query=None):
        policy=query['policy'] if query else None
        slot=dict(id=name,member=member,role=role,seed=0,timing_enabled=timing,
            phase='CALIBRATION_CPU',audit_enabled=False,eligible_clean_time=False)
        identity=dict(context_sha256=self.context,original_scope_sha256=self.card['scope_sha256'],
            slot=slot,policy=policy,query_sha256=query['request_sha256'] if query else None,
            RGB_shape=self.shape,CPU_fixture_only=True)
        path=self.root/name
        if path.exists():
            if not (path/'complete.json').exists():
                raise OriginalQueryUnknown('Recover original physical attempt without replay: '+name)
            proof=read_record(path/'complete.json')
            if proof['identity']!=identity or proof['status']!='COMPLETE':
                raise ValueError('Original physical result differs')
            if self.storage_limits:
                if proof['generation_payload']!=generation_snapshot(path/'generation',self.storage_limits):
                    raise ValueError('Original retained generation payload differs')
                check_path_metadata(path,self.storage_limits)
                check_scope(self.root,self.storage_limits)
            rgb,artifact=read_endpoint(path/'endpoint',identity)
            if proof['RGB_sha256']!=artifact['RGB_sha256']:
                raise ValueError('Original physical RGB completion differs')
            return rgb,proof
        if not self.allow_new:
            raise ValueError('Recovery cannot create a new physical request')
        if self.storage_limits:check_scope(self.root,self.storage_limits,reserve_next=True)
        path.mkdir(mode=0o700);sync_directory(path.parent);create_record(path/'intent.json',identity)
        self.physical_calls+=1
        result,rgb,rng_sha=self.execute(slot,policy,path/'generation')
        if (result['status']!='COMPLETE' or result['solver_steps']!=36 or result['guided_pairs']!=36
                or result['CPU_fixture'] is not True):
            raise ValueError('Complete original full36 request required')
        expected_policy=policy if query else self.card['roles'][role].get('policy')
        if expected_policy:
            history=result['semantic_history']
            if ([h['actual'] for h in history]!=expected_policy['actions']
                    or any(h['fallback_reason'] is not None for h in history)):
                raise ValueError('Actual policy departed from the registered fixed D budget')
        if not isinstance(rng_sha,str) or len(rng_sha)!=64:
            raise ValueError('Complete post-request RNG witness required')
        generation=generation_snapshot(path/'generation',self.storage_limits) if self.storage_limits else None
        artifact=save_endpoint(path/'endpoint',identity,rgb)
        if self.storage_limits and (path/'endpoint/RGB.npy').stat().st_size>self.storage_limits.RGB_bytes_per_path:
            raise ValueError('Full RGB artifact exceeds its registered allowance')
        proof=dict(status='COMPLETE',identity=identity,RGB_sha256=artifact['RGB_sha256'],
            rng_sha256=rng_sha,solver_steps=36,guided_pairs=36,
            actual_D=19 if role in ('UNIFORM19_C','SEARCH_CANDIDATE') else 36,
            T_DD=result['T_DD'],T_request=result['T_request'],CPU_fixture_only=True)
        if self.storage_limits:
            proof['generation_payload']=generation
            check_path_metadata(path,self.storage_limits)
            check_scope(self.root,self.storage_limits)
        create_record(path/'complete.json',proof)
        if self.storage_limits:check_path_metadata(path,self.storage_limits)
        return rgb,proof

    @staticmethod
    def equivalent(left,right):
        if not np.array_equal(left[0],right[0]) or left[1]['rng_sha256']!=right[1]['rng_sha256']:
            raise ValueError('Native/allD or timingON/OFF output/RNG equivalence failed')

    def prepare(self):
        self.physical('warm-native',FIT_MEMBERS[0],'NATIVE35',False)
        self.physical('warm-uniform',FIT_MEMBERS[0],'UNIFORM19_C',True)
        self.teachers=[];self.uniform_off=[]
        for index,member in enumerate(FIT_MEMBERS):
            teacher=self.physical(f'teacher-FIT{index}',member,'NATIVE35',False)
            native_on=self.physical(f'native-ON-FIT{index}',member,'NATIVE35',True)
            all_d=self.physical(f'allD-ON-FIT{index}',member,'ALLD',True)
            self.equivalent(teacher,native_on);self.equivalent(teacher,all_d)
            self.teachers.append(teacher)
            self.uniform_off.append(self.physical(f'uniform-OFF-FIT{index}',member,'UNIFORM19_C',False))

    def evaluate(self,query):
        if (digest({k:v for k,v in query.items() if k!='request_sha256'})!=query['request_sha256']
                or query['context_sha256']!=self.context or tuple(query['FIT_members'])!=FIT_MEMBERS
                or query['generation_seed']!=0 or query['requested_steps']!=35
                or query['actual_updates']!=36 or query['D_pair_budget']!=19 or len(query['dense'])!=19
                or policy_from_mask(self.profile,query['dense'])!=query['policy']):
            raise ValueError('Original complete query identity required')
        candidates=[self.physical(f'query-{query["query_id"]:06d}-FIT{i}',m,'SEARCH_CANDIDATE',True,query)
                    for i,m in enumerate(FIT_MEMBERS)]
        if query['query_id']==1:
            if query['policy']!=self.card['roles']['UNIFORM19_C']['policy']:
                raise ValueError('First original query must be Uniform19')
            for off,on in zip(self.uniform_off,candidates):self.equivalent(off,on)
        # Both FIT requests and the initial timing control precede any objective.
        return dict(request_sha256=query['request_sha256'],rows=[dict(member=m,status='COMPLETE',
            RGB_MSE=full_rgb_mse(c[0],t[0]),candidate_RGB_sha256=c[1]['RGB_sha256'],
            teacher_RGB_sha256=t[1]['RGB_sha256'],complete_frames=93,CPU_fixture_only=True)
            for m,c,t in zip(FIT_MEMBERS,candidates,self.teachers)])

    def run(self, *, allow_new=False):
        with (self.root/'calibration.lock').open('r+b') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            calls_before=self.physical_calls
            self.allow_new=allow_new
            if self.storage_limits:check_scope(self.root,self.storage_limits)
            self.prepare()
            journal=self.root/'queries'
            if not journal.exists() and not allow_new:
                raise ValueError('Original query journal missing; recovery cannot create it')
            result=run_search(journal,self.card['schedule'],self.profile,self.config,
                fit_members=FIT_MEMBERS,context_sha256=self.context,evaluate=self.evaluate,
                create=not journal.exists(),allow_new_queries=allow_new)
            expected=10+2*self.config.max_evaluations
            completed=list(self.root.glob('*/complete.json'))
            names={'warm-native','warm-uniform'} | {
                f'{kind}-FIT{i}' for kind in ('teacher','native-ON','allD-ON','uniform-OFF') for i in range(2)}
            names.update(f'query-{q:06d}-FIT{i}' for q in range(1,self.config.max_evaluations+1) for i in range(2))
            complete=(result['configured_search_finished'] and {p.parent.name for p in completed}==names
                and result['completed_cohort_evaluations']==self.config.max_evaluations)
            # On recovery re-validate every saved candidate even when the journal
            # reuses returned objectives without invoking the evaluator callback.
            if complete:
                for row in result['queries']:
                    query=read_record(journal/f'query-{row["query_id"]:06d}.intent.json')
                    response=self.evaluate(query)
                    if {r['member']:r['RGB_MSE'] for r in response['rows']}!=row['RGB_MSE_by_member']:
                        raise ValueError('Original complete query objective differs from saved RGB')
            storage=check_scope(self.root,self.storage_limits) if self.storage_limits else None
            return dict(storage_accounting=storage,status='CALIBRATION_CPU_COMPLETE' if complete else 'CALIBRATION_CPU_INCOMPLETE',
                complete=complete,expected_physical_paths=expected,complete_physical_paths=len(completed),
                new_physical_calls=self.physical_calls-calls_before,search=result,CPU_fixture_only=True,
                GPU_dispatch_ready=False,scientific_freeze_written=False,GPU_submissions=0,ledger_written=False)


class ProductionRequestsCPU:
    """The full native, allD and sparse sampler routes with tiny CPU weights."""
    def __init__(self, *, card, inference, samples, common, ra_binding, host, before_request):
        self.card=card;self.before_request=before_request
        self.kwargs=dict(inference=inference,samples=samples,common=common,ra_binding=ra_binding,
                         host=host,cpu_validation=True)

    def __call__(self,slot,policy,output):
        import torch
        from . import clean_speed20_r1 as clean
        from .cara_fast_requests_r2 import Requests
        card=copy.deepcopy(self.card);card.pop('scope_sha256')
        if policy:
            card['roles']['SEARCH_CANDIDATE']=dict(kind='policy',requested_steps=35,policy=policy)
        card.update(physical_matrix=[slot],formal_matrix=[],CPU_FRAGMENT_ONLY=True,GPU_dispatch_ready=False)
        card['scope_sha256']=digest(card)
        captured=[];module=self.kwargs['common']['inference_module'];writer=module.save_img_or_video
        def save(video,path,fps):
            captured.append(video.detach().to(device='cpu',dtype=torch.float32).numpy().copy())
            return writer(video,path,fps)
        self.before_request()
        with clean.patched(module,'save_img_or_video',save):
            result=Requests(card=card,**self.kwargs)(slot,output)
        if len(captured)!=1:
            raise ValueError('Exactly one guardrail-passed pre-encoding RGB required')
        return result,captured[0],digest(torch.get_rng_state().tolist())
