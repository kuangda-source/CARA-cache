import copy,hashlib,json
from pathlib import Path
import pytest
from wcomr.development_vqa_run import evaluate_cases,load_questions,validate_protocol


def fixture():
    q=[{'uid':'1','question':'Is the object moving?','answer':'A','index2ans':{'A':'yes','B':'no'}},
       {'uid':'2','question':'Is the light blue?','answer':'B','index2ans':{'A':'yes','B':'no'}}]
    cases=[{'name':'one','reference':{'outcome':'ACCEPTED','key':'r1'},'candidate':{'outcome':'ACCEPTED','key':'c1'}},
           {'name':'two','reference':{'outcome':'ACCEPTED','key':'r2'},'candidate':{'outcome':'VIDEO_REJECTED'}}]
    return q,cases


def test_original_questions_scored_once_rejection_and_invalid_preserved():
    q,cases=fixture();calls=[];snapshots=[];rows=[]
    def evaluate(arm,questions):
        calls.append(arm['key'])
        raw=['YES','NO'] if arm['key'].startswith('r') else ['no','YES and NO']
        return iter((answer,{'token':i}) for i,answer in enumerate(raw)),{'bound_video':'hash'}
    result=evaluate_cases(cases,{'one':q,'two':q},evaluate,rows,lambda:snapshots.append(copy.deepcopy(rows)))
    assert sorted(calls)==['c1','r1','r2']
    assert result['planned_scenes']==2 and result['accepted_pairs']==1 and result['rejected_candidates']==1
    assert result['equal_scene_mean_delta'] is None
    assert result['equal_scene_delta_lower_bound']==-1 and result['equal_scene_delta_upper_bound']==-.5
    assert rows[0]['candidate']['answers'][1]['raw']=='YES and NO'
    assert len(rows[1]['reference']['answers'])==2 and 'candidate' not in rows[1]
    assert any(len(s[0].get('candidate',{}).get('answers',[]))==1 for s in snapshots)


def test_forward_failure_preserves_partial_original_coverage_and_never_retries():
    q,cases=fixture();rows=[];calls=[];saved=[]
    def evaluate(arm,questions):
        calls.append(arm['key'])
        def outputs():
            yield 'YES',{'uid':'1'}
            raise RuntimeError('model forward failed')
        return outputs(),{}
    with pytest.raises(RuntimeError,match='forward'):
        evaluate_cases(cases,{'one':q,'two':q},evaluate,rows,lambda:saved.append(copy.deepcopy(rows)))
    assert len(calls)==1 and len(rows)==1
    arm=rows[0]['current_arm']
    assert len(rows[0][arm]['answers'])==1
    assert rows[0]['status']=='SCORING' and rows[0][arm]['answers']==saved[-1][0][arm]['answers']


def test_question_and_protocol_tampering_rejected_before_model_use(tmp_path):
    protocol=json.loads(Path('manifests/w1_development_vqa_protocol.json').read_text())
    validate_protocol(protocol)
    for key,val in [('max_gpu_seconds',901),('sampled_frame_indices',list(range(10))),('do_sample_frames_in_processor',True)]:
        wrong=copy.deepcopy(protocol);wrong[key]=val
        with pytest.raises(ValueError,match='protocol'):validate_protocol(wrong)
    q,_=fixture();directory=tmp_path/'questions';directory.mkdir();data=json.dumps(q).encode();path=directory/'a.json';path.write_bytes(data)
    p={'samples':['a'],'planned_reference_questions':2,'runtime_question_directory':'questions',
       'question_inputs':{'samples':[{'name':'a','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'root_count':2}]}}
    assert load_questions(tmp_path,p)=={'a':q}
    path.write_bytes(data.replace(b'moving',b'static'))
    with pytest.raises(ValueError,match='hash'):load_questions(tmp_path,p)


def complete_receipt():
    from wcomr.development_vqa_run import summarize_receipt
    q,cases=fixture();p=json.loads(Path('manifests/w1_development_vqa_protocol.json').read_text());p['samples']=['one','two'];rows=[]
    def evaluate(arm,questions):
        records=[{'uid':question['uid'],'generated_tokens':1,'generated_token_ids':[10+i],
                  'reached_token_cap':False,'seconds':.1} for i,question in enumerate(questions)]
        return iter(zip(['YES','NO'],records)),{'video_sha256':arm['video_sha256'],
            'metadata':{'frames_indices':p['sampled_frame_indices'],'total_num_frames':93,'fps':16,'video_backend':'decord'}}
    for case in cases:
        for arm in ['reference','candidate']:
            if case[arm]['outcome']=='ACCEPTED':case[arm]['video_sha256']=case['name']+arm
    questions={'one':q,'two':q};summary=evaluate_cases(cases,questions,evaluate,rows,lambda:None)
    receipt={'status':'W1_VQA_ALL_ORIGINAL8_QUESTIONS_ATTEMPTED','protocol':p,'rows':rows,'summary':summary}
    assert summarize_receipt(receipt,p,questions,cases)==summary
    return receipt,p,questions,cases


@pytest.mark.parametrize('corruption',['partial','raw','metadata','rejection','token_count'])
def test_terminal_summary_rejects_incomplete_or_changed_scientific_receipts(corruption):
    from wcomr.development_vqa_run import summarize_receipt
    r,p,questions,cases=complete_receipt()
    if corruption=='partial':r['status']='TECH_BLOCKED'
    if corruption=='raw':r['rows'][0]['reference']['answers'][0]['raw']='NO'
    if corruption=='metadata':r['rows'][0]['reference']['input']['metadata']['frames_indices']=[0,92]
    if corruption=='rejection':r['rows'][1]['candidate']={'answers':[]}
    if corruption=='token_count':r['rows'][0]['reference']['generation_records'][0]['generated_tokens']=2
    with pytest.raises(ValueError):summarize_receipt(r,p,questions,cases)
