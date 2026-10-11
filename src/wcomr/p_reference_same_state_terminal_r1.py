"""Exact registered parent/suffix/age denominators survive partial execution."""
import ast
from pathlib import Path
from types import SimpleNamespace

from .p_reference_same_state_production_r1 import RUN, ARMS, COUNTS, VARIANTS


def pure_verifier(stage):
    package = Path(stage)/'src/wcomr'
    def function(name, identifier, namespace):
        tree = ast.parse((package/name).read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == identifier)
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(package/name)+'#pure-post-verifier', 'exec'), namespace)
        return namespace[identifier]
    base = function('e4c_matched_source_age_sampling_r1.py', 'verify_batch', {})
    native = ast.parse((package/'cfg_guided_w1_deployment.py').read_text())
    assignment = next(n for n in native.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'METHODS' for t in n.targets))
    alpha = function('cfg_guided_w1_deployment.py', 'alpha_at', {'METHODS': ast.literal_eval(assignment.value)})
    return function('p_reference_same_state_sampling_r1.py', 'verify_batch',
        {'old': SimpleNamespace(verify_batch=base), 'VARIANTS': tuple(VARIANTS), 'alpha_at': alpha})


def original_gone(supervisor, pid, exists):
    if (supervisor['pid'] != pid or supervisor['run_id'] != RUN
            or supervisor['status'] != 'P_REFERENCE_EXITED_REQUIRES_COMPLETE_SCOPE_RAW_CPU_AUDIT'
            or supervisor['planned_scope'] != COUNTS or len(supervisor['arms']) != 2
            or [a['id'] for a in supervisor['arms']] != list(ARMS)
            or exists(pid) or any(exists(a['pid']) for a in supervisor['arms'] if 'pid' in a)
            or 'wc_p_reference_same_state_inflight' in supervisor['budget_after']):
        raise ValueError('Original complete P-reference handles must exit and settle first')


def inventory(scope, supervisor, receipts):
    if (scope['whole_scope_counts'] != COUNTS or scope['flow_modes'] != [False, True]
            or [e['birth_step'] for e in scope['events']] != [13, 25, 12, 27]
            or scope['candidate_variants'] != VARIANTS
            or supervisor['run_id'] != RUN or supervisor['planned_scope'] != COUNTS
            or [a['id'] for a in supervisor['arms']] != list(ARMS)):
        raise ValueError('Complete original two-flow registered scope required')
    parents = []; events = []; suffixes = []; points = []
    if set(receipts)-set(ARMS): raise ValueError('Foreign flow receipt')
    for process in supervisor['arms']:
        arm = process['id']; receipt = receipts.get(arm); indexed = {}
        if receipt is not None:
            if (receipt['pid'] != process['pid'] or receipt['run_id'] != RUN
                    or receipt['arm'] != arm or receipt['flow'] != ARMS[arm]
                    or receipt['source_revision'] != supervisor['source_revision']
                    or receipt['config_sha256'] != supervisor['config_sha256']):
                raise ValueError('Original arm PID/source/config changed')
            for q in receipt['batch'].get('requests', []):
                if q['sample_name'] not in scope['sample_names']: raise ValueError('Foreign parent request')
                for row in q['paths']:
                    key = (q['sample_name'], row['collect'])
                    if type(row['collect']) is not bool or key in indexed: raise ValueError('Duplicate parent')
                    indexed[key] = row
        for sample in scope['sample_names']:
            for collect in (False, True):
                row = indexed.get((sample, collect))
                item = {'arm': arm, 'flow': ARMS[arm], 'sample_name': sample, 'collect': collect,
                    'status': row.get('status', 'ATTEMPTED_NO_ROW_RETAINED') if row else
                        'ATTEMPTED_NO_ROW_RETAINED' if 'pid' in process else 'UNSTARTED_RETAINED'}
                if row is not None: item['row'] = row
                parents.append(item)
                if not collect: continue
                existing = {e['event']['id']: e for e in row.get('origins', [])} if row else {}
                declared = [e for e in scope['events'] if e['sample_name'] == sample]
                if row is not None and len(existing) != len(row.get('origins', [])):
                    raise ValueError('Duplicate diagnostic event')
                if set(existing)-{e['id'] for e in declared}: raise ValueError('Foreign diagnostic event')
                for event in declared:
                    value = existing.get(event['id'])
                    events.append({'arm': arm, 'event_id': event['id'],
                        'status': value['status'] if value else 'MISSING_REGISTERED_EVENT_RETAINED'})
                    branches = {b['label']: b for b in value['branches']} if value else {}
                    if value and (len(branches) != len(value['branches'])
                            or set(branches)-set(scope['suffix_arms'])):
                        raise ValueError('Duplicate or foreign registered suffix')
                    for label in scope['suffix_arms']:
                        branch = branches.get(label)
                        suffixes.append({'arm': arm, 'event_id': event['id'], 'label': label,
                            'status': branch['status'] if branch else 'MISSING_REGISTERED_SUFFIX_RETAINED'})
                        source = 'P' if label == 'P_BIRTH_C4' else 'D' if label == 'D_BIRTH_C4' else None
                        if source is None: continue
                        saved = {p['age']: p for p in branch['age_points']} if branch else {}
                        if branch and (len(saved) != len(branch['age_points']) or set(saved)-{1, 2, 4}):
                            raise ValueError('Duplicate or foreign age point')
                        for age in scope['teacher_ages']:
                            point = saved.get(age)
                            entry = {'arm': arm, 'flow': ARMS[arm], 'sample_name': sample,
                                'event_id': event['id'], 'source': source, 'age': age,
                                'status': 'RAW_READ_REQUIRED' if point else 'MISSING_REGISTERED_POINT_RETAINED'}
                            if point: entry['point'] = point
                            points.append(entry)
    if (len(parents), len(events), len(suffixes), len(points)) != (8, 8, 32, 48):
        raise ValueError('Original complete denominators changed')
    return {'parent_slots': parents, 'event_slots': events, 'suffix_slots': suffixes, 'point_slots': points}
