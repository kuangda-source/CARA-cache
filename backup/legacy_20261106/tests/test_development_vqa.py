import ast,copy,hashlib
from pathlib import Path
import pytest
from wcomr.development_vqa import SYSTEM,BEGIN,question_text,score_answer,question_summary,summarize,arm_order


def questions():
    return [{'uid':'q1','question':'Does the object move?','answer':'B','index2ans':{'A':'yes','B':'no'}},
            {'uid':'q2','question':'Is the light red?','answer':'A','index2ans':{'A':'yes','B':'no'}}]


def test_original_prompt_has_no_labels_and_matches_pinned_templates():
    source=Path('vendor/WorldCache/Evaluation/PAI-Eval/pbench/prompts/evaluation_prompt.py').read_text()
    tree=ast.parse(source)
    selected=[n for n in tree.body if (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ['system_template_binary_v0','begin_user_template_binary_v0'] for t in n.targets)) or (isinstance(n,ast.FunctionDef) and n.name=='user_template_binary_v0')]
    namespace={};exec(compile(ast.Module(body=selected,type_ignores=[]),'<pinned-prompts>','exec'),namespace)
    q=questions()[0]
    assert SYSTEM==namespace['system_template_binary_v0'] and BEGIN==namespace['begin_user_template_binary_v0']
    assert question_text(q)==BEGIN+'\n\n'+namespace['user_template_binary_v0'](q,is_reasoning=False)
    q['answer']='A';q['uid']='changed';assert 'changed' not in question_text(q)
    assert question_text(q)==question_text(questions()[0])


def test_strict_parser_rejects_explanations_and_preserves_unknown_bounds():
    q=questions()
    assert score_answer(q[0],' NO. ')['correct'] is True
    for raw in ['I know the answer is yes','YES NO','unknown','', 'YES because it moves']:
        assert score_answer(q[0],raw)['correct'] is None
    answers=[score_answer(q[0],'NO'),score_answer(q[1],'not clear')]
    s=question_summary(answers,q);assert s['accuracy'] is None and s['accuracy_lower_bound']==.5 and s['accuracy_upper_bound']==1.
    with pytest.raises(ValueError,match='coverage'):question_summary(answers[:1],q)
    bad=copy.deepcopy(answers);bad[1]['correct']=False
    with pytest.raises(ValueError,match='raw'):question_summary(bad,q)


def test_scene_denominator_question_order_and_rejected_video_are_retained():
    q=questions();valid=[score_answer(q[0],'NO'),score_answer(q[1],'YES')]
    other=[score_answer(q[0],'YES'),score_answer(q[1],'NO')]
    rows=[{'name':'a','candidate_outcome':'ACCEPTED','reference':{'answers':valid},'candidate':{'answers':other}},
          {'name':'b','candidate_outcome':'VIDEO_REJECTED','reference':{'answers':valid}}]
    s=summarize(rows,['a','b'],{'a':q,'b':q});assert s['planned_scenes']==2 and s['accepted_pairs']==1 and s['rejected_candidates']==1 and s['equal_scene_mean_delta']==-1.
    with pytest.raises(ValueError,match='scene'):summarize(rows[:1],['a','b'],{'a':q,'b':q})
    assert sorted(arm_order('a'))==['candidate','reference'] and arm_order('a')==arm_order('a')
