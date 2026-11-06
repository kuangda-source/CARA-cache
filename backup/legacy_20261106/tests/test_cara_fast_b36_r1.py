"""Synthetic A metadata and B control boundaries; never actual A32 results."""
import copy
import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wcomr.cara_fast_b36_r1 import (
    COMMON_SOURCES,HANDOFF_FILES,bind_handoff,read_handoff,check_complete_B,formal_sources)
from wcomr.cara_fast_capture_r2 import captured_file
from wcomr.cara_fast_collection_r2 import freeze_selection
from wcomr.cara_fast_post_r2 import accept_scores
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_fast_terminal_r2 import released_terminal,settle_original,record
import test_cara_fast_post_r2 as original_post_fixture

ROOT = Path(__file__).resolve().parents[1]


def metadata_fixture(project, host='two_card', choice=0):
    """Reuse the accepted producer fixture, changing only explicit synthetic data."""
    source = inspect.getsource(original_post_fixture.fixture)
    assert source.count("host='two_card'") == 2
    source = source.replace("host='two_card'", 'host=selected_host')
    names = list(dict.fromkeys([*original_post_fixture.SCORER_SOURCES,*COMMON_SOURCES]))
    namespace = {**vars(original_post_fixture), 'selected_host':host, 'SCORER_SOURCES':names}
    exec(compile(source,__file__+'#synthetic-A-metadata','exec'),namespace)
    old = original_post_fixture.execution_fixtures.complete_fixture
    def controlled_A():
        card,state = old()
        preferred = {values[choice] for values in card['finite_grids'].values()}
        for row in state['rows']:
            if row['slot']['section'] == 'A_CALIBRATION':
                row['result']['T_DD'] = 200. if row['slot']['role'] in preferred else 250.
        return card,state
    gpu = original_post_fixture.execution_fixtures.ExecutionTests().gpu()
    if host == 'four_card':
        gpu.update(name='NVIDIA RTX 6000 Ada',compute_cap='8.9')
    with patch.object(original_post_fixture.execution_fixtures,'complete_fixture',controlled_A),\
            patch.object(original_post_fixture.execution_fixtures.ExecutionTests,'gpu',return_value=gpu):
        card,capture,pool,stage,_,_ = namespace['fixture'](project)
    settlement = settle_original(pool,capture,card)
    release = released_terminal(capture,card,settlement)
    manifest,manifest_sha,scores,execution = original_post_fixture.score_fixture(capture,card,settlement)
    accepted = accept_scores(capture,card,settlement,manifest,manifest_sha,scores,execution)
    frozen = freeze_selection(card,record(capture,'collection'),release,accepted,stage/'synthetic-frozen.json')
    assert all(frozen['selected'][family]['candidate'] == values[choice]
               for family,values in card['finite_grids'].items())
    raw = json.dumps(scores,sort_keys=True,separators=(',',':'))
    score_capture = dict(status='FAST_A32_SCORE_TERMINAL_CAPTURE',execution=execution,
        files=dict(scores=dict(exists=True,raw_utf8=raw,bytes=len(raw.encode()),sha256=digest(scores))))
    values = dict(capture=capture,settlement=settlement,manifest=manifest,
                  score_capture=score_capture,accepted_scores=accepted,frozen=frozen)
    inputs = stage/'handoff-inputs';inputs.mkdir()
    paths = {}
    for name,value in values.items():
        path = inputs/(name+'.json')
        path.write_text(json.dumps(value,sort_keys=True,separators=(',',':')))
        paths[name] = path
    package = read_handoff(paths)
    assert package['files']['manifest']['sha256'] == manifest_sha
    return card,package,paths


def replace_record(package,name,change):
    data = record(package,name)
    change(data)
    raw = json.dumps(data,sort_keys=True,separators=(',',':'))
    package['files'][name].update(raw_utf8=raw,bytes=len(raw.encode()),sha256=digest(data))


def complete_B_fixture(card,frozen,cpu_validation=True):
    schedules = {row['requested_steps']:row['actual_updates'] for row in card['schedules']}
    rows = []
    for slot in (slot for slot in card['physical_matrix'] if slot['phase'] == 'B'):
        role = card['roles'][slot['role']]
        concrete = frozen['selected'][role['family']]['candidate'] if role['kind']=='selection' else slot['role']
        updates = schedules[card['roles'][concrete]['requested_steps']]
        result = dict(slot_id=slot['id'],role=slot['role'],concrete_role=concrete,
            scope_sha256=card['scope_sha256'],CPU_fixture=cpu_validation,
            solver_steps=updates,guided_pairs=updates,audit_enabled=False,
            in_timing_guided_copies=0,in_timing_hashes=0,research_checkpoints=0,T_DD=1.,T_request=2.)
        rows.append(dict(slot=copy.deepcopy(slot),status='COMPLETE',result=result))
    return dict(phase='B',scope_sha256=card['scope_sha256'],status='TERMINAL',rows=rows)


class B36Tests(unittest.TestCase):
    def test_complete_handoff_same_device_and_all_candidate_branches(self):
        for host in ('four_card','two_card'):
            for choice in (0,1):
                with self.subTest(host=host,choice=choice),tempfile.TemporaryDirectory() as directory:
                    card,package,paths = metadata_fixture(Path(directory),host,choice)
                    before = paths['frozen'].read_bytes()
                    binding = bind_handoff(card,package,host=host,gpu_uuid='GPU-CPU-CONTROL')
                    self.assertEqual(paths['frozen'].read_bytes(),before)
                    self.assertTrue(binding['CPU_fixture_only'])
                    self.assertFalse(binding['authorizes_phase_B'])
                    state = complete_B_fixture(card,binding['frozen'])
                    check_complete_B(card,state,binding['frozen'],cpu_validation=True)
                    rows = formal_sources(card,binding,state,cpu_validation=True)
                    self.assertEqual(len(rows),32)
                    self.assertEqual(sum(row['reused_from_A'] for row in rows),8)
                    self.assertEqual(len({row['slot_id'] for row in rows}),32)

    def test_partial_live_unsettled_wrong_source_and_changed_decision_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            card,package,_ = metadata_fixture(Path(directory))
            for change in ('missing','byte_tamper','partial_A','live_score','unsettled',
                           'changed_decision','incomplete_scores','wrong_source'):
                with self.subTest(change=change):
                    bad = copy.deepcopy(package)
                    if change=='missing':bad['files'].pop('frozen')
                    elif change=='byte_tamper':bad['files']['frozen']['raw_utf8']+=' '
                    elif change=='partial_A':
                        replace_record(bad,'capture',lambda data:replace_record(data,'collection',lambda state:state['rows'].pop()))
                    elif change=='live_score':replace_record(bad,'score_capture',lambda data:data.update(status='FAST_A32_SCORE_LIVE_OPERATIONAL_ONLY'))
                    elif change=='unsettled':replace_record(bad,'settlement',lambda data:data['central_after']['jobs'][next(key for key in data['central_after']['jobs'] if key.startswith('cara-fast-'))].update(status='RESERVED_OR_RUNNING'))
                    elif change=='changed_decision':replace_record(bad,'frozen',lambda data:data['selected']['WC'].update(candidate='WC_T008'))
                    elif change=='incomplete_scores':replace_record(bad,'accepted_scores',lambda data:data['rows'].pop())
                    else:
                        replace_record(bad,'capture',lambda data:data['payload_actual_sha256'].update({COMMON_SOURCES[0]:'0'*64}))
                    with self.assertRaises((ValueError,KeyError)):
                        bind_handoff(card,bad,host='two_card',gpu_uuid='GPU-CPU-CONTROL')
            for host,uuid in [('four_card','GPU-CPU-CONTROL'),('two_card','GPU-DIFFERENT')]:
                with self.assertRaises(ValueError):bind_handoff(card,package,host=host,gpu_uuid=uuid)

    def test_partial_dirty_wrong_route_and_CPU_as_GPU_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            card,package,_ = metadata_fixture(Path(directory))
            binding = bind_handoff(card,package,host='two_card',gpu_uuid='GPU-CPU-CONTROL')
            for change in ('missing','reorder','failed','dirty','wrong_route','wrong_updates','CPU_as_GPU'):
                with self.subTest(change=change):
                    state = complete_B_fixture(card,binding['frozen'])
                    if change=='missing':state['rows'].pop()
                    elif change=='reorder':state['rows'].reverse()
                    elif change=='failed':state['rows'][0]['status']='TECH_FAILED'
                    elif change=='dirty':state['rows'][0]['result']['in_timing_hashes']=1
                    elif change=='wrong_route':state['rows'][0]['result']['concrete_role']='NATIVE24'
                    elif change=='wrong_updates':state['rows'][0]['result']['solver_steps']-=1
                    with self.assertRaises(ValueError):
                        check_complete_B(card,state,binding['frozen'],cpu_validation=change!='CPU_as_GPU')


if __name__=='__main__':
    unittest.main()
