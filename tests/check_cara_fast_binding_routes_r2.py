"""Exercise the changed audit boundary; reuse the old model/runtime CPU fixture."""
import copy
import json
from pathlib import Path

import numpy as np
import torch
from wcomr import clean_speed20_r1 as clean
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_requests_r2 import Requests
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.wc_time_diagnostics_r1 import capture

ROOT = Path(__file__).resolve().parents[1]
SPEC = 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json'


def body(inference, selected, wc, rf, common, unused_initial, profile, root,
         native, flow, inference_module, host, samples):
    import check_wc_time_card_r1 as fixture
    card = load_card(ROOT, SPEC)
    binding = json.loads((ROOT/'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json').read_text())
    model = inference.pipe.model
    net = model.net
    net.__class__ = fixture.load('check_fair_sampling_cpu').native_toy_class(
        Path(common['runtime']), type(net), dict(vars(wc)))
    net.timestep_scale = .001
    initial = CompleteStateRoundtrip(net, model.sample_scheduler, torch.zeros(1))
    kwargs = dict(inference=inference,samples=samples,card=card,common=common,
                  ra_binding=binding,host=host,cpu_validation=True)
    frozen = dict(scope_sha256=card['scope_sha256'],phase_A_GPU_released=True,
                  CPU_FIXTURE_ONLY=True,
                  selected={family:dict(candidate=values[0]) for family,values in card['finite_grids'].items()})
    originals = (model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)
    last_frame = [None]
    original_writer = inference_module.save_img_or_video

    def writer(video, path, fps):
        last_frame[0] = np.array(video, copy=True)
        return original_writer(video, path, fps)

    def restored():
        assert (model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward) == originals
        assert '_cara_paper_timing_active_r1' not in vars(model)

    def equal(left, right, *, guided):
        a, b = left['result'], right['result']
        assert torch.equal(a['final_latent'], b['final_latent'])
        assert np.array_equal(left['RGB'], right['RGB'])
        assert torch.equal(left['RNG'], right['RNG'])
        if guided:
            assert len(a['guided']) == len(b['guided']) == 36
            assert all(torch.equal(x,y) for x,y in zip(a['guided'],b['guided']))

    diagnostics = {}
    clean_results = {}
    paths = 0
    with clean.patched(inference_module,'save_img_or_video',writer):
        runner = Requests(**kwargs,frozen=frozen)
        for slot in (s for s in card['physical_matrix'] if s['section']=='A_DIAGNOSTIC'):
            initial.restore()
            with capture(inference, True) as witness:
                result = runner(slot, root/slot['id'])
            paths += 1
            assert result['status']=='COMPLETE' and result['in_timing_guided_copies']==36
            assert not result['eligible_clean_time'] and result['audit_enabled']
            diagnostics[(slot['member'],slot['role'],slot['timing_enabled'])] = dict(
                result=copy.deepcopy(result),RGB=last_frame[0].copy(),RNG=torch.get_rng_state().clone(),
                input_RNG=copy.deepcopy(witness))
            restored()
        for member in card['FIT']:
            for role in ('NATIVE35','ALLD','WC_T006'):
                left, right = (diagnostics[(member,role,enabled)] for enabled in (False,True))
                equal(left,right,guided=True)
                assert left['input_RNG']==right['input_RNG']
            equal(diagnostics[(member,'NATIVE35',True)],diagnostics[(member,'ALLD',True)],guided=True)
            assert diagnostics[(member,'ALLD',True)]['result']['actions']==['DD']*36
        anchors = [s for s in card['physical_matrix'] if s['section']=='A_ANCHOR']
        # Execute one clean path for every concrete non-control role. The full
        # registered68 denominator is checked separately without replaying it.
        selected_slots = anchors[:]
        first = card['FIT'][0]
        for role in ['SHARED25_C','F19_C','F19_A1','UNIFORM19_C',
                     'WC_T006','WC_T008','RA_T1','RA_T15','NATIVE22','NATIVE24']:
            selected_slots.append(next(s for s in card['physical_matrix']
                if s['member']==first and s['role']==role and s['eligible_clean_time']))
        for slot in selected_slots:
            initial.restore()
            result = runner(slot, root/slot['id'])
            paths += 1
            assert result['status']=='COMPLETE' and not result['audit_enabled']
            assert all(result[k]==0 for k in ('in_timing_guided_copies','in_timing_hashes','research_checkpoints'))
            assert 'guided' not in result and result['eligible_clean_time']
            assert 0<result['T_DD']<=result['core_seconds']<=result['T_request']
            record = dict(result=copy.deepcopy(result),RGB=last_frame[0].copy(),RNG=torch.get_rng_state().clone(),slot=slot)
            clean_results[(slot['member'],slot['role'])] = record
            if slot['role']=='NATIVE35':
                equal(record,diagnostics[(slot['member'],'NATIVE35',True)],guided=False)
            if card['roles'][slot['role']]['kind']=='policy':
                assert [h['actual'] for h in result['semantic_history']]==card['roles'][slot['role']]['policy']['actions']
            restored()
        representatives = ['NATIVE35','F19_A1','RA_T15','NATIVE24']
        for role in representatives:
            on = clean_results[(first,role)]
            initial.restore()
            result = Requests(**kwargs,frozen=frozen)(on['slot'],root/('OFF_'+role),timing=False)
            paths += 1
            off = dict(result=result,RGB=last_frame[0].copy(),RNG=torch.get_rng_state().clone())
            equal(on,off,guided=False)
            assert on['result'].get('semantic_history')==off['result'].get('semantic_history')
            assert on['result'].get('actions')==off['result'].get('actions')
            restored()
        failures = []
        for role in ('F19_A1','WC_T008','RA_T15','NATIVE24'):
            slot = clean_results[(first,role)]['slot']
            initial.restore()
            entry = Requests(**kwargs,frozen=frozen)
            def fail(*args,**kwargs):
                raise OSError('DECLARED_WRITER_FAILURE')
            with clean.patched(inference_module,'save_img_or_video',fail):
                try:
                    entry(slot,root/('FAIL_'+role))
                except OSError:
                    failures.append(role)
                else:
                    raise AssertionError('Writer failure swallowed')
            restored()
            try:
                entry(slot,root/'retry')
            except ValueError:
                pass
            else:
                raise AssertionError('Failed slot replayed')
        bslot = next(s for s in card['physical_matrix'] if s['phase']=='B')
        try:
            Requests(**kwargs)(bslot,root/'missing-freeze')
        except ValueError:
            pass
        else:
            raise AssertionError('Unfrozen phaseB accepted')
        try:
            Requests(**{**kwargs,'cpu_validation':False})
        except ValueError:
            pass
        else:
            raise AssertionError('Unbound production context accepted')
    initial.restore()
    return [dict(flow=flow,registered_physical_positions=68,actual_successful_tiny_paths=paths,
                 diagnostic_paths=12,clean_paths=12,clean_OFF_ON_pairs=4,
                 writer_failure_and_no_replay_roles=failures,
                 full_diagnostic_gate_equal=True,clean_native_matches_audited_native=True,
                 clean_research_counters_zero=True,production_context_required=True,
                 phaseB_freeze_required=True,Cosmos_weights_loaded=False)]


def run(runtime, artifact_root, host, samples):
    import check_wc_time_card_r1 as fixture
    fixture.body = body
    return fixture.run(runtime, artifact_root, host, samples)
