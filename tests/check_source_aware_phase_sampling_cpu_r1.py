"""Same full128 control scope with synthetic creation-phase floors."""
from pathlib import Path
import torch

from wcomr import source_aware_phase_sampling as phase
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.source_aware_cpd_control import Costs
from wcomr.cfg_ra_joint_control import Calibration


def run(runtime, tensor_loader, artifact_root):
    from importlib.util import spec_from_file_location, module_from_spec
    p = Path(__file__).with_name('check_source_aware_partial_sampling_cpu_r1.py')
    spec = spec_from_file_location('accepted_dynamic_fixture', p)
    original = module_from_spec(spec); spec.loader.exec_module(original)
    calibration = Calibration('SYNTHETIC_CREATION_PHASE_FULL36_RA_PRIOR',
        {(a,s):1. for a in range(1,36) for s in range(a+1,37)},
        {s:1. for s in range(1,37)})
    baseline = {'threshold':.07, 'costs':Costs('SYNTHETIC_REFERENCE_RA_FULL_PAIR',1.,4.),
                'partial_prior':None}
    partial = {'threshold':2., 'costs':Costs('SYNTHETIC_CPD_FULL_PAIR',3.,4.,1.),
        'partial_prior':CreationPhasePrior('SYNTHETIC_CREATION_PHASE_FLOOR',.005,.3,
            early_creation_floor=.005, late_creation_floor=.02)}
    dense = {'threshold':2., 'costs':Costs('SYNTHETIC_ACTUAL_D_CHEAPEST',4.,1.),
             'partial_prior':None}
    specs = {m:dict(baseline if m in ('SOURCE_RA','DYNAMIC_NO_P')
                    else dense if m=='DENSE_CONTROL' else partial) for m in phase.METHODS}
    fixture = phase.bind_globals(original.fixture, {'dynamic':phase})
    exercise = fixture(calibration,specs)
    value = original.load('check_full_sampling').run(runtime,exercise=lambda **kw:
        exercise(runtime=Path(runtime),tensor_loader=tensor_loader,
                 artifact_root=artifact_root,**kw))
    early = late = 0
    for check in value['checks']:
        if check['status'] != 'PASS': continue
        for request in check['receipt']['requests']:
            for row in request['paths']:
                deployment = row['collection_complete'].get('deployment')
                if deployment is None: continue
                last_floor = 0.
                for entry in deployment['history']:
                    record = entry['source_policy']
                    step = record['decision']['step']
                    action = record['decision']['action']
                    actual = record['creation_floor_proxy_after']
                    if action == 'P':
                        expected = .005 if step < 25 else .02
                        assert actual == expected
                        early += step < 25; late += step >= 25
                        last_floor = expected
                    elif action == 'D':
                        assert actual == 0.; last_floor = 0.
                    else: assert actual == last_floor
    assert early > 0 and late > 0 and not torch.cuda.is_initialized()
    value.update(creation_phase_early_P_pairs=early,creation_phase_late_P_pairs=late,
        P_birth_floor_and_only_D_reset_verified_in_all_success_histories=True,
        phase_sampler_binding_proofs=phase.DERIVATION_PROOFS,
        unchanged_complete_full128_scope=True, synthetic_phase_floor_values=[.005,.02])
    return value
