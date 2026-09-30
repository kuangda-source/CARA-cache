"""Strict binary proxy VQA receipts; scene weighting, unknown bounds, no Joint."""
import hashlib
import re

SYSTEM = 'You are a helpful AI assistant that answers questions about videos. Answer with just YES or NO.'
BEGIN = "I'll show you a video with several frames. Please look carefully at all frames to understand what's happening in the video, then answer the question about the video with either YES or NO."


def validate_questions(questions):
    if not questions or len({q['uid'] for q in questions}) != len(questions):
        raise ValueError('Missing/duplicate original questions')
    for q in questions:
        if not isinstance(q['question'], str) or not q['question'].strip() or q['answer'] not in q['index2ans']:
            raise ValueError('Invalid original question')
        if {value.lower() for value in q['index2ans'].values()} != {'yes','no'}:
            raise ValueError('Nonbinary question')


def question_text(question):
    return BEGIN+'\n\nQuestion: '+question['question']+'\n\nPlease answer with YES or NO.'


def score_answer(question, raw):
    matched = re.fullmatch(r'\s*(YES|NO)[.!]?\s*', raw, flags=re.IGNORECASE)
    answer = matched.group(1).lower() if matched else None
    return {'uid':question['uid'], 'raw':raw, 'parsed_answer':answer,
            'parse_status':'VALID' if answer is not None else 'INVALID_OUTPUT',
            'expected_answer':question['index2ans'][question['answer']].lower(),
            'correct':answer == question['index2ans'][question['answer']].lower() if answer is not None else None}


def question_summary(answers, questions):
    validate_questions(questions)
    if [a['uid'] for a in answers] != [q['uid'] for q in questions]:
        raise ValueError('Incomplete/reordered original question coverage')
    recomputed = [score_answer(q,a['raw']) for a,q in zip(answers,questions)]
    if answers != recomputed:
        raise ValueError('Answer scoring receipt differs from raw response')
    correct = sum(a['correct'] is True for a in answers)
    unknown = sum(a['correct'] is None for a in answers)
    n = len(answers)
    return {'questions':n,'correct':correct,'invalid':unknown,
            'accuracy':correct/n if not unknown else None,
            'accuracy_lower_bound':correct/n,'accuracy_upper_bound':(correct+unknown)/n}


def arm_order(name):
    return ['reference','candidate'] if int(hashlib.sha256(name.encode()).hexdigest(),16)%2==0 else ['candidate','reference']


def summarize(rows, planned, questions_by_name):
    if [row['name'] for row in rows] != list(planned):
        raise ValueError('Incomplete/reordered original scene coverage')
    results=[];deltas=[];lowers=[];uppers=[]
    for row in rows:
        questions=questions_by_name[row['name']]
        reference=question_summary(row['reference']['answers'],questions)
        result={'name':row['name'],'reference':reference,'candidate_outcome':row['candidate_outcome']}
        if row['candidate_outcome']=='ACCEPTED':
            candidate=question_summary(row['candidate']['answers'],questions)
            lower=candidate['accuracy_lower_bound']-reference['accuracy_upper_bound']
            upper=candidate['accuracy_upper_bound']-reference['accuracy_lower_bound']
            delta=candidate['accuracy']-reference['accuracy'] if candidate['accuracy'] is not None and reference['accuracy'] is not None else None
            result.update(candidate=candidate,delta=delta,delta_lower_bound=lower,delta_upper_bound=upper)
            if delta is not None:deltas.append(delta)
            lowers.append(lower);uppers.append(upper)
        elif row['candidate_outcome'] not in ['TEXT_REJECTED','VIDEO_REJECTED']:
            raise ValueError('Unknown candidate outcome')
        results.append(result)
    mean=lambda values:sum(values)/len(values) if values else None
    return {'status':'SMALL_JUDGE_DEVELOPMENT_VQA_COMPLETE_NOT_STANDARD_JOINT',
            'planned_scenes':len(rows),'accepted_pairs':len(lowers),'rejected_candidates':len(rows)-len(lowers),
            'fully_parsed_pairs':len(deltas),'samples':results,
            'equal_scene_mean_delta':mean(deltas) if len(deltas)==len(lowers) else None,
            'equal_scene_delta_lower_bound':mean(lowers),'equal_scene_delta_upper_bound':mean(uppers),
            'scope':'Original scene denominator retained. Bounds account for invalid raw answers, not statistical confidence. Small reusable-CAL proxy, no physical correctness, overall quality, paper Joint, independent confirmation or clean-speed acceptance.'}
