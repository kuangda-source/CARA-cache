"""Complete/partial denominators, exact authority and unique original handles."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile


def run(stage, c, scope, receipts):
    from wcomr.p_reference_same_state_production_r1 import RUN, binding, CONFIG
    from wcomr.p_reference_same_state_execution_r1 import exact_authorization
    from wcomr.p_reference_same_state_terminal_r1 import inventory, original_gone
    supervisor = {'run_id': RUN, 'pid': 11, 'source_revision': 'EXPLICIT_CPU_FIXTURE_NOT_GPU',
        'config_sha256': 'EXPLICIT_CPU_FIXTURE', 'status': 'P_REFERENCE_EXITED_REQUIRES_COMPLETE_SCOPE_RAW_CPU_AUDIT',
        'planned_scope': c['scope_counts'], 'budget_after': {},
        'arms': [{'id': arm, 'pid': 100+i, 'planned_paths': 4, 'exit_code': 0}
                 for i, arm in enumerate(c['flow_arms'])]}
    original = {}
    for process in supervisor['arms']:
        arm = process['id']; original[arm] = {'run_id': RUN, 'pid': process['pid'], 'arm': arm,
            'flow': c['flow_arms'][arm], 'source_revision': supervisor['source_revision'],
            'config_sha256': supervisor['config_sha256'], 'batch': receipts[arm]}
    complete = inventory(scope, supervisor, original)
    assert (len(complete['parent_slots']), len(complete['event_slots']), len(complete['suffix_slots']), len(complete['point_slots'])) == (8, 8, 32, 48)
    assert all(x['status'] == 'RAW_READ_REQUIRED' for x in complete['point_slots'])
    partial = copy.deepcopy(original); partial['FLOW_ON']['batch']['requests'][1]['paths'][1]['origins'].pop()
    result = inventory(scope, supervisor, partial)
    assert len(result['point_slots']) == 48 and sum('point' not in p for p in result['point_slots']) == 6
    absent = copy.deepcopy(supervisor); absent['arms'][1].pop('pid')
    result = inventory(scope, absent, {'FLOW_OFF': original['FLOW_OFF']})
    assert len(result['parent_slots']) == 8 and sum(p['status'] == 'UNSTARTED_RETAINED' for p in result['parent_slots']) == 4
    assert len(result['point_slots']) == 48 and sum('point' not in p for p in result['point_slots']) == 24
    refusals = []
    for name in ('foreign_source', 'foreign_PID', 'duplicate_parent', 'foreign_event', 'duplicate_suffix', 'duplicate_point', 'changed_flow_scope'):
        s, sup, r = copy.deepcopy(scope), copy.deepcopy(supervisor), copy.deepcopy(original)
        on = r['FLOW_ON']; row = on['batch']['requests'][0]['paths'][1]
        if name == 'foreign_source': on['source_revision'] = 'FOREIGN'
        elif name == 'foreign_PID': on['pid'] = 999
        elif name == 'duplicate_parent': on['batch']['requests'][0]['paths'].append(copy.deepcopy(row))
        elif name == 'foreign_event': row['origins'][0]['event']['id'] = 'FOREIGN'
        elif name == 'duplicate_suffix': row['origins'][0]['branches'].append(copy.deepcopy(row['origins'][0]['branches'][0]))
        elif name == 'duplicate_point': row['origins'][0]['branches'][2]['age_points'].append(copy.deepcopy(row['origins'][0]['branches'][2]['age_points'][0]))
        else: s['flow_modes'] = [True]
        try: inventory(s, sup, r)
        except ValueError: refusals.append(name)
        else: raise AssertionError('Whole inventory accepted '+name)
    original_gone(supervisor, 11, lambda pid: False)
    for pid in (11, 100, 101):
        try: original_gone(supervisor, 11, lambda p: p == pid)
        except ValueError: pass
        else: raise AssertionError('Original live handle admitted for CPU')
    fixture = {'direct_user_authorization': True, 'card': c['card'], 'run_id': RUN,
        'scope_counts': c['scope_counts'], 'config_binding_sha256': binding(c),
        'forecast_complete_GPUh': c['forecast_complete_GPUh'], 'CPU_FIXTURE_NEVER_HUMAN_AUTHORITY': True}
    exact_authorization(c, fixture); approvals = []
    for key, bad in [('direct_user_authorization', False), ('card', 'E3'), ('run_id', 'OTHER'),
                     ('scope_counts', {}), ('config_binding_sha256', 'BAD'), ('forecast_complete_GPUh', 8.)]:
        r = copy.deepcopy(fixture); r[key] = bad
        try: exact_authorization(c, r)
        except ValueError: approvals.append(key)
        else: raise AssertionError('Different card approval accepted')
    path = Path(stage)/'scripts/select_and_launch_wc_p_reference_same_state_r1.py'
    spec = importlib.util.spec_from_file_location('P_REFERENCE_UNIQUE_HANDLES_CPU_FIXTURE', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    previous = subprocess.Popen; launch_cases = []
    try:
        for fail_post in (False, True):
            calls = []
            class Process:
                def __init__(self, command, **kwargs):
                    index = len(calls); calls.append((command, kwargs)); self.pid = 500+index
                    if fail_post and index == 1: raise OSError('EXPLICIT_CPU_POST_DISPATCH_FAILURE')
            subprocess.Popen = Process
            with tempfile.TemporaryDirectory(prefix='P_REFERENCE_HANDLE_CPU_') as folder:
                s = Path(folder); (s/CONFIG).write_text('{}')
                try: value = module.launch_handles(s, s, 'EXPLICIT_CPU_FIXTURE', c, 'CPU_PROD', 'CPU_SELECTED', 'CPU_PROTOCOL')
                except OSError:
                    assert fail_post
                    value = json.loads((s/'GPU-launch.json').read_text())
                    assert value['status'] == 'P_REFERENCE_POST_DISPATCH_FAILED_ORIGINAL_GPU_HANDLE_RETAINED'
                assert len(calls) == 2 and value['gpu_supervisor_pid'] == 500
                assert calls[1][0][-2:] == ['--original-supervisor-pid', '500']
                assert all(kwargs['env']['CUDA_VISIBLE_DEVICES'] == '' for _, kwargs in calls)
                assert not (s/'outputs').exists()
                launch_cases.append({'fail_post': fail_post, 'original_GPU_handle_preserved_no_restart': True})
    finally: subprocess.Popen = previous
    return {'complete_parent_slots': 8, 'complete_event_slots': 8, 'complete_suffix_slots': 32,
        'complete_point_slots': 48, 'inventory_refusals': refusals, 'authority_refusals': approvals,
        'original_live_handle_refusals': 3, 'isolated_launch_cases': launch_cases,
        'CPU_fixture_not_authorization_or_GPU_result': True}
