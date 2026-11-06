"""Two complete full128 strategy controls, without real model calibration."""
from pathlib import Path
import torch

from wcomr import source_aware_working_epoch_sampling_r1 as working
from wcomr.source_aware_phase_sampling import bind_globals
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.source_aware_cpd_control import Costs
from wcomr.cfg_ra_joint_control import Calibration


def run(runtime,tensor_loader,artifact_root):
    from importlib.util import spec_from_file_location,module_from_spec
    p=Path(__file__).with_name('check_source_aware_partial_sampling_cpu_r1.py')
    spec=spec_from_file_location('accepted_dynamic_fixture',p)
    original=module_from_spec(spec);spec.loader.exec_module(original)
    calibration=Calibration('SYNTHETIC_CREATION_PHASE_FULL36_RA_PRIOR',
        {(a,s):1. for a in range(1,36) for s in range(a+1,37)},
        {s:1. for s in range(1,37)})
    baseline={'threshold':.07,'costs':Costs('SYNTHETIC_REFERENCE_RA_FULL_PAIR',1.,4.),'partial_prior':None}
    partial={'threshold':2.,'costs':Costs('SYNTHETIC_CPD_FULL_PAIR',3.,4.,1.),
        'partial_prior':CreationPhasePrior('SYNTHETIC_CREATION_PHASE_FLOOR',.005,.3,
            early_creation_floor=.005,late_creation_floor=.02)}
    dense={'threshold':2.,'costs':Costs('SYNTHETIC_ACTUAL_D_CHEAPEST',4.,1.),'partial_prior':None}
    results=[];P_queries=early=late=0
    for strategy in working.STRATEGIES:
        specs={m:{**dict(baseline if m in ('SOURCE_RA','DYNAMIC_NO_P')
                         else dense if m=='DENSE_CONTROL' else partial),
                  'working_epoch_strategy':strategy} for m in working.METHODS}
        fixture=bind_globals(original.fixture,{'dynamic':working})
        exercise=fixture(calibration,specs)
        value=original.load('check_full_sampling').run(runtime,exercise=lambda **kw:
            exercise(runtime=Path(runtime),tensor_loader=tensor_loader,
                artifact_root=Path(artifact_root)/strategy,**kw))
        for check in value['checks']:
            check['working_epoch_strategy']=strategy
            if check['status']!='PASS':continue
            assert check['verdict']['working_epoch_strategy']==strategy
            P_queries+=check['verdict']['P_source_transfer_queries_verified']
            for request in check['receipt']['requests']:
                for row in request['paths']:
                    d=row['collection_complete'].get('deployment')
                    if d is None:continue
                    last_floor=0.
                    for entry in d['history']:
                        p=entry['source_policy'];decision=p['decision'];actual=p['creation_floor_proxy_after']
                        if decision['action']=='P':
                            expected=.005 if decision['step']<25 else .02
                            assert actual==expected and working.valid_P_interval(p,strategy)
                            early+=decision['step']<25;late+=decision['step']>=25;last_floor=expected
                        elif decision['action']=='D':
                            assert actual==0.;last_floor=0.
                        else:assert actual==last_floor
            # Additional mutation controls preserve all original eight faults.
            import copy
            for fault in ('wrong_working_query_anchor','false_P_future_calibration','zero_rebased_interval'):
                bad=copy.deepcopy(check['receipt'])
                d=bad['requests'][-1]['paths'][2]['collection_complete']['deployment']
                entry=next(v for v in d['history'] if v['action']=='PP')
                if fault=='wrong_working_query_anchor':entry['source_policy']['working_epoch_basis']['query_anchor']=-99
                elif fault=='false_P_future_calibration':d['P_future_drift_empirically_calibrated']=True
                else:entry['source_policy']['accumulated_interval_proxy_after']=0.
                try:working.verify_batch(bad)
                except ValueError:check.setdefault('working_epoch_mutation_refusals',[]).append(fault)
                else:raise AssertionError('Invalid working-source evidence accepted: '+fault)
            assert len(check['working_epoch_mutation_refusals'])==3
        results.extend(value['checks'])
    assert len(results)==8 and early>0 and late>0 and P_queries>0
    assert not torch.cuda.is_initialized()
    return {'checks':results,'registered_strategies':list(working.STRATEGIES),
        'creation_phase_early_P_pairs':early,'creation_phase_late_P_pairs':late,
        'explicit_P_source_transfer_queries':P_queries,
        'P_birth_floor_and_actual_D_history_preserved':True,
        'working_epoch_sampler_binding_proofs':working.DERIVATION_PROOFS,
        'original_full128_scope_retained_per_strategy':True,
        'complete_executed_paths':256,'same_synthetic_creation_phase_inputs':True}
