import copy
import pytest
from wcomr.development_vqa import score_answer
from wcomr.vqa_controls import CONDITIONS,condition_order,summarize_controls


def fixture():
    q=[{'uid':'a','question':'Does the object move?','answer':'A','index2ans':{'A':'yes','B':'no'}},
       {'uid':'b','question':'Is the water frozen?','answer':'B','index2ans':{'A':'yes','B':'no'}}]
    names=['one','two'];protocol={'samples':names,'mismatch_source':{'one':'two','two':'one'},'expected_question_count_per_condition':4,'expected_total_generated_answers':12}
    baseline={'rows':[{'name':name,'reference':{'answers':[score_answer(q[0],'YES'),score_answer(q[1],'NO')],
        'input':{'sampled_tensor_sha256':name+'hash'}}} for name in names]}
    rows=[]
    for name in names:
        conditions={}
        for condition in CONDITIONS:
            raw=['YES','NO'] if condition=='matched_repeat' else ['NO','NO']
            answers=[]
            for question,text in zip(q,raw):
                parsed=score_answer(question,text);answers.append({k:parsed[k] for k in ['uid','raw','parsed_answer','parse_status']})
            conditions[condition]={'status':'ALL_ORIGINAL_QUESTIONS_COMPLETE','source_name':protocol['mismatch_source'][name] if condition=='cyclic_mismatch' else name,'input':{'sampled_tensor_sha256':name+'hash'},'answers':answers}
        rows.append({'name':name,'status':'ALL_CONDITIONS_COMPLETE','condition_order':condition_order(name),'conditions':conditions})
    return rows,protocol,baseline,{name:q for name in names}


def test_stable_repeated_and_content_sensitive_counts_are_not_quality_accuracy():
    rows,p,b,q=fixture();s=summarize_controls(rows,p,b,q)
    assert s['decision']=='REPEAT_STABLE_AND_RESPONDS_TO_CONTENT_NOT_PHYSICAL_VALIDITY'
    assert s['generated_answers']==12 and s['conditions']['matched_repeat']['parsed_changed']==0
    assert s['conditions']['blank']['parsed_changed']==2 and s['conditions']['cyclic_mismatch']['parsed_changed']==2
    assert 'accuracy' not in s['conditions']['blank'] and 'correct' not in s['conditions']['blank']


@pytest.mark.parametrize('kind,decision',[('invalid','INCONCLUSIVE_PARSE_INVALID'),('repeat','REPEAT_INSTABILITY_IN_SCOPE'),('insensitive','CONTENT_INSENSITIVITY_SUSPECT_IN_SCOPE')])
def test_controls_do_not_overclaim_parse_repeat_or_content_failures(kind,decision):
    rows,p,b,q=fixture()
    if kind=='insensitive':rows[0]['conditions']['blank']['answers']=copy.deepcopy(rows[0]['conditions']['matched_repeat']['answers']);rows[1]['conditions']['blank']['answers']=copy.deepcopy(rows[1]['conditions']['matched_repeat']['answers'])
    else:
        c='blank' if kind=='invalid' else 'matched_repeat';raw='YES and NO' if kind=='invalid' else 'NO';parsed=score_answer(q['one'][0],raw)
        rows[0]['conditions'][c]['answers'][0]={k:parsed[k] for k in ['uid','raw','parsed_answer','parse_status']}
    assert summarize_controls(rows,p,b,q)['decision']==decision


@pytest.mark.parametrize('kind',['partial','question_order','source_fixed_point','tensor','raw_parse'])
def test_changed_original_input_coverage_or_parser_is_rejected(kind):
    rows,p,b,q=fixture()
    if kind=='partial':rows.pop()
    if kind=='question_order':rows[0]['conditions']['blank']['answers'].reverse()
    if kind=='source_fixed_point':rows[0]['conditions']['cyclic_mismatch']['source_name']='one'
    if kind=='tensor':rows[0]['conditions']['matched_repeat']['input']['sampled_tensor_sha256']='changed'
    if kind=='raw_parse':rows[0]['conditions']['blank']['answers'][0]['parsed_answer']='yes'
    with pytest.raises(ValueError):summarize_controls(rows,p,b,q)
