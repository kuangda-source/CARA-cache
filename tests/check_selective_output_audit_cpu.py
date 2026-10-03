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
