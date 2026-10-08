#!/usr/bin/env python3
"""Reconstruct full four-cell CPU controls with standard-library hashes."""
import gzip
import hashlib
import json
from pathlib import Path

TRACE = ('inputs', 'outputs', 'deep', 'banks', 'solver_outputs')
LABELS = ['OFF1','OFF2','BASE_first','CFG1_second','CFG0_first','PAIRED_second',
          'PAIRED_first','CFG0_second','CFG1_first','BASE_second']
ENCODED = ['OFF1','BASE_first','CFG0_first','PAIRED_first','CFG1_first']


def digest(value):
    h = hashlib.sha256()
    def walk(v):
        if isinstance(v, dict):
            for key in sorted(v): h.update(str(key).encode()); walk(v[key])
        elif isinstance(v, (list, tuple)):
            h.update(type(v).__name__.encode())
            for x in v: walk(x)
        elif v is None or type(v) in (str, int, float, bool): h.update(repr(v).encode())
        else: raise TypeError(type(v))
    walk(value)
    return h.hexdigest()


def check_components(c, inventory, fingerprint=None, output=None):
    assert set(c) == inventory and bool(c)
    assert all(type(v) is str and len(v) == 64 and set(v) <= set('0123456789abcdef') for v in c.values())
    if fingerprint is not None: assert digest(c) == fingerprint
    if output is not None: assert c['output'] == output


def configuration(c, components):
    assert set(c) == {'raw_values','raw_sha256','numerical_values','numerical_sha256','default_name_metadata'}
    assert c['raw_sha256'] == digest(c['raw_values']) == components['solver._internal_dict']
    assert c['numerical_values'] == {k:v for k,v in c['raw_values'].items() if k != '_use_default_values'}
    assert c['numerical_sha256'] == digest(c['numerical_values'])
    assert c['default_name_metadata'] == c['raw_values'].get('_use_default_values')
    return c


def main():
    prefix = 'reports/wc_w3_cfg_budget_core_cpu_r1_20261008_'
    read = lambda n: json.loads(gzip.decompress(Path(prefix+n+'_native.gz').read_bytes()))
    result, receipt, manifest = read('result_json'), read('receipt_json'), read('manifest_json')
    capture = json.loads(Path(prefix+'terminal_capture.json').read_text())
    assert receipt['exit_code'] == 0 and receipt['source_revision'] == capture['source_revision']
    assert result['status'] == 'CFG_BUDGET_AFFECTED_CORE_CPU_PASS_NOT_GPU'
    assert result['CUDA_initialized'] is False and result['GPU_submissions'] == 0
    assert capture['budget_unchanged'] and receipt['new_payload_after_sha256'] == manifest['new_payload_sha256']
    assert receipt['base_payload_after_sha256'] == receipt['staged_base_after_sha256'] == manifest['base_payload_sha256']
    for n, h in manifest['new_payload_sha256'].items(): assert hashlib.sha256(Path(n).read_bytes()).hexdigest() == h
    successes = [x for x in result['checks'] if x['error'] is None]
    failures = [x for x in result['checks'] if x['error'] is not None]
    assert len(successes)==4 and len(failures)==5
    assert {x['case'] for x in failures} == {'failure_cfg0_action','failure_second_action','failure_paired_writer','failure_paired_guardrail','failure_parent_mask'}
    registration=json.loads(Path('manifests/wc_w3_cfg_budget_matched_cpu_preregistration_20261008.json').read_text())
    parent=registration['parent_action_mask'];assert len(parent)==72
    scopes = []
    for check in successes:
        state = check['receipt']; assert len(state['requests']) == 1
        assert (state['planned_parent_phases'],state['planned_suffix_controls'],state['planned_encoded_outputs']) == (1,10,6)
        row = state['requests'][0]; inventory = set(row['final_components'])
        assert {'output','cpu_rng','python_rng','numpy_rng','cuda_rng','explicit_generators','solver._internal_dict','solver._step_index','net.cnt'} <= inventory
        check_components(row['final_components'], inventory, output=row['final_latent_sha256'])
        conf = configuration(row['final_solver_configuration'], row['final_components'])
        assert ['D' if n else 'C' for n in row['deep']]==parent
        assert all(len(row[k]) == (36 if k == 'solver_outputs' else 72) for k in TRACE)
        assert row['prepare_calls'] == 1 and row['flags_before'] == row['flags_after']
        assert row['sample_return_sha256'] == row['final_latent_sha256']
        by = {x['label']:x for x in row['children']}; assert list(by) == LABELS and len(row['children']) == 10
        for label, child in by.items():
            rec = child['record']; report = rec['action_report']; events = report['suffix_events']
            mode='OFF' if label.startswith('OFF') else label.split('_')[0]
            swaps={'OFF':[],'BASE':[],'CFG0':[[45,47]],'CFG1':[[46,48]],'PAIRED':[[45,47],[46,48]]}[mode]
            expected=list(parent)
            for current,donor in swaps:expected[current-1]='D';expected[donor-1]='C'
            assert child['status']=='COMPLETE_SUFFIX_NOT_RV_LABEL' and child['action']==mode and rec['parent_restored']
            assert rec['completed_updates']==22 and rec['planned_remaining_updates']==14
            assert all(len(child[k])==(14 if k=='solver_outputs' else 28) for k in TRACE)
            actual=list(parent[:44])+['D' if n else 'C' for n in child['deep']]
            assert actual==expected==report['actual_actions'] and len(actual)==72
            assert [sum(n=='D' for n in actual[slot::2]) for slot in (0,1)]==report['per_CFG_full_counts']==[18,17]
            msha=lambda values:hashlib.sha256(''.join(values).encode()).hexdigest()
            assert report['parent_mask_sha256']==msha(parent) and report['actual_mask_sha256']==msha(expected)
            assert report['quota_matched_per_CFG'] and report['budget_matched']
            assert report['plan']==(None if mode=='OFF' else {'mode':mode,'parent_mask':parent,'prefix_calls':44,'maximum_age_solver_steps':32})
            assert report['planned_action_changes']==2*len(swaps)
            assert report['remaining_policy']==('ORIGINAL_WC_ADAPTIVE_REFERENCE' if mode=='OFF' else 'OFFLINE_FIXED_PARENT_MASK_WITH_REGISTERED_CFG_POSITION_EXCHANGES')
            assert report['current_truth_used_for_decision'] is False and report['RV_label'] is False
            assert report['paid_mask_decisions']==(0 if mode=='OFF' else sum(e['paid_probe'] for e in events))
            assert report['native_tail_proposal_preservation_required'] is False
            assert report['tail_native_proposal_disagreements']==[e['call'] for e in events if e.get('tail_native_proposal_disagreement')]
            check_components(rec['final_state_components'], inventory, rec['final_state_sha256'], child['final_latent_sha256'])
            assert configuration(child['final_solver_configuration'],rec['final_state_components']) == conf
            for at in ('pre45','pre46'):
                point = child[at]
                check_components(point['components'], inventory, point['fingerprint'])
                assert configuration(point['solver_configuration'],point['components']) == conf and all(point['own_history'])
            assert child['pre45'] == by['BASE_first']['pre45'] and child['inputs'][:2] == by['BASE_first']['inputs'][:2]
            assert [e['call'] for e in events] == list(range(45,73)) and events[-3]['native_cycle_reset']
            assert child['deep'][-2:] == [2,2]
            for event, deep in zip(events,child['deep']):
                assert deep in (0,2) and event['actual_action'] == ('D' if deep else 'C')
                assert event['cfg_slot'] == (event['call']-1)%2 and event['solver_step'] == (event['call']-1)//2+1
                assert event['current_deep_truth_used'] is False
                if mode=='OFF':assert event['requested'] is None and (not event['paid_probe'] or event['selected_skip']==event['native_skip'])
                elif event['paid_probe']:
                    assert event['requested']==event['planned_action']==expected[event['call']-1]
                    assert event['selected_skip']==(expected[event['call']-1]=='C')
                    if expected[event['call']-1]=='C' or event['call'] in sum(swaps,[]):assert 1<=event['age_solver_steps']<=32
                else:assert event['call'] in (71,72) and expected[event['call']-1]=='D'
        for a, b in [('OFF1','OFF2')] + [(n+'_first',n+'_second') for n in ('BASE','CFG0','CFG1','PAIRED')]:
            assert all(by[a][k] == by[b][k] for k in TRACE+('final_latent_sha256','pre45','pre46','final_solver_configuration'))
            assert by[a]['record']['final_state_components'] == by[b]['record']['final_state_components']
            assert by[a]['record']['action_report'] == by[b]['record']['action_report']
        for label in ('OFF1','OFF2','BASE_first','BASE_second'):
            assert all(by[label][k] == row[k][22 if k == 'solver_outputs' else 44:] for k in TRACE)
            assert by[label]['record']['final_state_components'] == row['final_components']
        for a,b in [('BASE_first','CFG1_first'),('CFG0_first','PAIRED_first')]:
            assert by[a]['pre46'] == by[b]['pre46'] and all(by[a][k][:1] == by[b][k][:1] for k in ('outputs','deep','banks'))
        decoded = {x['label']:x for x in row['decoded_children']}; assert list(decoded) == ENCODED
        assert decoded['OFF1']['artifact']['sha256'] == decoded['BASE_first']['artifact']['sha256'] == row['artifact']['sha256']
        assert [by[n+'_first']['deep'][:4] for n in ('BASE','CFG0','CFG1','PAIRED')]==[[0,0,2,2],[2,0,0,2],[0,2,2,0],[2,2,0,0]]
        if check['case']=='native_tail_proposal_disagreement':
            assert all(by[n+'_first']['record']['action_report']['tail_native_proposal_disagreements']==[69,70] for n in ('BASE','CFG0','CFG1','PAIRED'))
        scopes.append({'flow':check['flow'],'case':check['case'],'parents':1,'suffixes':10,'mock_outputs':6,
                       'full_component_count':len(inventory),'strict_repeat_groups':5,'raw_solver_dictionary_bound':True,'separate_CFG_quotas':[18,17],'full_total':35})
    refusals = sum(len(x['mutation_refusals']) for x in successes)
    assert refusals == result['mutation_refusals'] == 104
    out = {'status':'CFG_BUDGET_CORE_CPU_NATIVE_AND_INDEPENDENT_RAW_SCOPE_RECONSTRUCTION_PASS_NOT_GPU',
           'source_revision':receipt['source_revision'],'original_result_sha256':receipt['result_sha256'],
           'complete_successful_parents':4,'complete_successful_suffixes':40,'successful_mock_outputs':24,
           'failed_attempts_retained':5,'mutation_refusals':refusals,'reconstructed_scopes':scopes,
           'actual_CPU_wall_seconds':result['CPU_wall_seconds'],'budget_unchanged':True,
           'CUDA_initialized':False,'GPU_submissions':0,'real_video_or_quality_evidence':False,'native_proposals_forced_only_in_CPU_fixture':True,'real_mask_feasibility_verified':False}
    p = Path('reports/wc_w3_cfg_budget_core_cpu_r1_independent_audit_20261008.json')
    with p.open('x') as f: f.write(json.dumps(out, indent=2) + '\n')
    print(json.dumps({k:out[k] for k in ('status','complete_successful_suffixes','mutation_refusals','actual_CPU_wall_seconds')}))


if __name__ == '__main__': main()
