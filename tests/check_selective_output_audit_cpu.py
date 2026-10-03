"""Real partial-receipt binding controls; never artifact or quality evidence."""
from copy import deepcopy
import importlib.util
from pathlib import Path


def run(receipt):
    p=Path(__file__).parents[1]/'scripts/audit_wc_selective_output_receipts.py'
    s=importlib.util.spec_from_file_location('selective_audit',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    m.binding(receipt);checks=['actual_running_six_card_scope_contract']
    for case in ('denominator','warm_mask','wrong_condition','teacher_source','small_layers','cadence'):
        r=deepcopy(receipt)
        if case=='denominator':r['planned_output_files']=4
        elif case=='warm_mask':r['fixed_mask']['dense_calls'][0]=False
        elif case=='wrong_condition':r['fixed_mask']['condition_id']='0'*64
        elif case=='teacher_source':r['fixed_mask']['source_receipt_sha256']='0'*64
        elif case=='small_layers':r['policies'][1]['sparse_layers']=[2,3,6]
        else:r['policies'][2]['every']=1
        try:m.binding(r)
        except AssertionError:checks.append('reject_'+case)
        else:raise AssertionError('Corrupted binding accepted: '+case)
    if receipt['status']!='SIX_SELECTIVE_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT':
        r=m.audit(receipt,Path('/CPU_CONTRACT_ONLY_NO_ARTIFACT_IO'))
        assert r['status']=='INCOMPLETE_SELECTIVE_SIX_CARD_NOT_ACCEPTED' and r['planned_outputs']==6 and not r['quality_acceptance']
        checks.append('partial_never_shrinks_six_denominator_or_accepts_quality')
    return {'status':'ACTUAL_SELECTIVE_BINDING_CPU_REJECTION_PASS_NOT_ARTIFACT_IO',
        'CPU_only':True,'checks':checks,'quality_acceptance':False,
        'limits':'Current actual receipt contracts and explicit corruptions; six actual files and policy-source reconstruction still require completed GPU originals.'}


def run_policy_controls(receipt):
    """Reject source/policy corruptions in actual completed GPU event records."""
    p=Path(__file__).parents[1]/'scripts/audit_wc_selective_output_receipts.py'
    s=importlib.util.spec_from_file_location('selective_policy_audit',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    assert receipt['status']=='SIX_SELECTIVE_OUTPUTS_COMPLETE_REQUIRE_INDEPENDENT_AUDIT'
    context,mask=m.binding(receipt)
    phases=receipt['measurement']['phases']
    assert len(phases)==4
    checks=[]
    for i,name in enumerate(('full_S','small_S','cadenced_S'),1):
        m.phase_provenance(phases[i],context,mask,sparse_allowed=True)
        checks.append('actual_'+name+'_policy_source_reconstruction')
    for case in ('wrong_layer_metadata','nonfinite_kernel_fraction','approximate_as_true_D',
                 'wrong_source_context','future_reference','changed_deep_mask',
                 'wrong_cadence_ordinal','missed_cadenced_D_refresh','missed_native_reset'):
        phase=deepcopy(phases[3 if 'cadence' in case else 2])
        rows=phase['refresh_provenance']['events']
        sparse=next(e for e in rows if e['sparse_layers'])
        if case=='wrong_layer_metadata':sparse['operator_metadata'][0]['layer']=6
        elif case=='nonfinite_kernel_fraction':sparse['operator_metadata'][0]['selected_fraction']=float('nan')
        elif case=='approximate_as_true_D':sparse['inserted_into_true_dense_history']=True
        elif case=='wrong_source_context':sparse['source']['context']=['other']
        elif case=='future_reference':sparse['true_dense_before'][0]['call']=72
        elif case=='changed_deep_mask':phase['trace'][sparse['call']-1]['deep_executed']=False
        elif case=='wrong_cadence_ordinal':sparse['selection_eligible_ordinal']+=1
        elif case=='missed_cadenced_D_refresh':
            dense=next(e for e in rows if e['selection_eligible'] and not e['selection_sparse_chosen'])
            dense['inserted_into_true_dense_history']=False
        else:rows[69]['native_cycle_reset']=False
        try:m.phase_provenance(phase,context,mask,sparse_allowed=True)
        except AssertionError:checks.append('reject_'+case)
        else:raise AssertionError('Corrupted GPU policy/source record accepted: '+case)
    return {'status':'ACTUAL_THREE_GPU_POLICY_SOURCE_CPU_REJECTION_PASS',
        'CPU_only':True,'checks':checks,'new_GPU_submission':False,'quality_acceptance':False,
        'limits':'Actual complete event records and deliberate corruptions; independent video/source/cost audits remain separate.'}
