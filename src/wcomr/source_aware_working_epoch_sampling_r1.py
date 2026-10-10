"""Working-P epoch strategies in the original complete ordinary sampler.

This is a new owner, never a mutation of the frozen phase sampler. Actual
projection work, WC/RF execution, A readout and solver bytecode are preserved.
The borrowed D-only drift prior remains explicitly marked as a transfer.
"""
import ast
import functools
import hashlib
import inspect
from textwrap import dedent

from . import source_aware_partial_sampling as base
from .source_aware_phase_sampling import bind_globals
from .source_aware_partial_deployment import SourceAwarePartialDeployment
from .source_aware_working_epoch_control_r2 import WorkingEpochCPDController,STRATEGIES

METHODS=base.METHODS


class WorkingEpochDeployment(SourceAwarePartialDeployment):
    def commit(self,actual,base_last):
        returned=super().commit(actual,base_last)
        decision=self.controller.history[-1]
        self.history[-1]['source_policy']['working_epoch_basis']=self.controller.query_basis(decision)
        return returned

    def finish(self):
        result=super().finish()
        result['working_epoch_strategy']=self.controller.strategy
        result['P_future_drift_empirically_calibrated']=False
        return result


class WorkingEpochSamplingOwner(base.DynamicSamplingOwner):
    def __init__(self,model,*,method,context,runtime,wc,rf,calibration,spec):
        strategy=spec.get('working_epoch_strategy')
        if strategy not in STRATEGIES:
            raise ValueError('Explicit registered working-P strategy required')
        constructor=bind_globals(base.DynamicSamplingOwner.__init__,{
            'SourceAwareCPDController':functools.partial(WorkingEpochCPDController,strategy=strategy),
            'SourceAwarePartialDeployment':WorkingEpochDeployment})
        constructor(self,model,method=method,context=context,runtime=runtime,wc=wc,rf=rf,
                    calibration=calibration,spec=spec)

    def installation(self):
        return super().installation()+(self.controller.strategy,)


def valid_P_interval(record,strategy):
    before=record['decision']['state_before'][4]
    added=record['decision']['added_risk']
    expected=before+added if strategy==STRATEGIES[0] else added
    return record['accumulated_interval_proxy_after']==expected and expected>0


original=dedent(inspect.getsource(base.verify_batch))
before="or p['accumulated_interval_proxy_after']<p['decision']['state_before'][4]"
after="or not valid_P_interval(p,d['working_epoch_strategy'])"
if original.count(before)!=1:raise ValueError('Pinned original P interval verification site changed')
changed=original.replace(before,after)
inverse=changed.replace(after,before)
if inverse!=original or ast.dump(ast.parse(inverse))!=ast.dump(ast.parse(original)):
    raise ValueError('Complete ordinary verifier changed outside explicit P interval semantics')
namespace={**vars(base),'valid_P_interval':valid_P_interval}
exec(compile(changed,__file__+'#P-interval-verifier','exec'),namespace)
_verify_base=namespace['verify_batch']


def verify_batch(state):
    result=_verify_base(state)
    strategies=set();queries=P_queries=0
    for request in state['requests']:
        for row in request['paths']:
            d=row['collection_complete'].get('deployment')
            if d is None:continue
            strategy=d['working_epoch_strategy']
            if strategy not in STRATEGIES or d['P_future_drift_empirically_calibrated']:
                raise ValueError('Working P strategy or transferred prior role differs')
            strategies.add(strategy)
            for entry in d['history']:
                p=entry['source_policy'];decision=p['decision'];basis=p['working_epoch_basis']
                anchor,kind,work=decision['state_before'][:3]
                expected_anchor=work if kind=='P' else anchor
                expected={'true_D_anchor':anchor,'working_source_kind':kind,
                    'working_source_step':work,'query_anchor':expected_anchor,
                    'query_age':decision['step']-expected_anchor if expected_anchor is not None else None,
                    'rho_source':'D_ONLY_PRIOR_TRANSFERRED_TO_WORKING_P_AGE' if kind=='P' else 'D_ONLY_PRIOR',
                    'P_future_drift_empirically_calibrated':False,'strategy':strategy}
                if basis!=expected:
                    raise ValueError('Actual complete working-source query evidence differs')
                queries+=1;P_queries+=kind=='P'
                if entry['action']=='PP' and not valid_P_interval(p,strategy):
                    raise ValueError('P must preserve the registered positive interval contribution')
    if len(strategies)!=1:
        raise ValueError('One bound strategy per complete eight-method batch required')
    return {**result,'working_epoch_strategy':next(iter(strategies)),
            'explicit_working_epoch_queries_verified':queries,
            'P_source_transfer_queries_verified':P_queries,
            'actual_P_future_drift_or_endpoint_quality_claim':False}


derive=bind_globals(base.derive,{'verify_batch':verify_batch})
run_batch=bind_globals(base.run_batch,{'DynamicSamplingOwner':WorkingEpochSamplingOwner,'derive':derive})
audit_vectors=bind_globals(base.audit_vectors,{'verify_batch':verify_batch})
DERIVATION_PROOFS={
    'constructor_original_bytecode_preserved':True,
    'constructor_global_bindings':['SourceAwareCPDController','SourceAwarePartialDeployment'],
    'complete_batch_and_vector_audit_original_bytecode_preserved':True,
    'original_verifier_source_sha256':hashlib.sha256(original.encode()).hexdigest(),
    'verifier_inverse_AST_and_original_bytes_equal':True,
    'explicit_P_interval_verifier_sites':1,
    'new_query_metadata_and_strategy_installation_binding':True,
    'original_modules_and_running_payload_not_modified':True}
