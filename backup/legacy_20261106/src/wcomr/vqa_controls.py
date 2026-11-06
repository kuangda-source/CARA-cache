"""Input-control coverage and agreement, without counterfactual quality labels."""
import hashlib
from wcomr.development_vqa import score_answer

CONDITIONS=['matched_repeat','blank','cyclic_mismatch']


def condition_order(name):
    offset=int(hashlib.sha256(name.encode()).hexdigest(),16)%3
    return CONDITIONS[offset:]+CONDITIONS[:offset]


def summarize_controls(rows, protocol, baseline, questions):
    if [row['name'] for row in rows] != protocol['samples']:
        raise ValueError('Original8 control coverage differs')
    base={row['name']:row['reference'] for row in baseline['rows']}
    totals={condition:{'questions':0,'valid':0,'invalid':0,'parsed_changed':0,
                       'raw_changed':0,'yes':0,'no':0} for condition in CONDITIONS}
    scenes=[]
    for row in rows:
        name=row['name'];q=questions[name];records=base[name]['answers']
        if row['status']!='ALL_CONDITIONS_COMPLETE' or row['condition_order']!=condition_order(name):
            raise ValueError('Incomplete/changed control order')
        if set(row['conditions'])!=set(CONDITIONS):
            raise ValueError('Unexpected control conditions')
        if [answer['uid'] for answer in records] != [question['uid'] for question in q]:
            raise ValueError('Baseline question coverage differs')
        scene={'name':name,'conditions':{}}
        for condition in CONDITIONS:
            observed=row['conditions'][condition]
            expected_source=protocol['mismatch_source'][name] if condition=='cyclic_mismatch' else name
            if observed['source_name'] != expected_source or (condition=='cyclic_mismatch' and expected_source==name):
                raise ValueError('Control source mapping differs')
            if observed['status']!='ALL_ORIGINAL_QUESTIONS_COMPLETE' or [answer['uid'] for answer in observed['answers']] != [question['uid'] for question in q]:
                raise ValueError('Incomplete/reordered control questions')
            if condition=='matched_repeat' and observed['input']['sampled_tensor_sha256']!=base[name]['input']['sampled_tensor_sha256']:
                raise ValueError('Matched repeat decoded input differs')
            stats={'questions':len(q),'valid':0,'invalid':0,'parsed_changed':0,'raw_changed':0,'yes':0,'no':0}
            for question,answer,old in zip(q,observed['answers'],records):
                parsed=score_answer(question,answer['raw'])
                expected={k:parsed[k] for k in ['uid','raw','parsed_answer','parse_status']}
                if answer!=expected:raise ValueError('Control parser differs from raw')
                valid=answer['parsed_answer'] is not None
                stats['valid']+=valid;stats['invalid']+=not valid
                stats['parsed_changed']+=valid and answer['parsed_answer']!=old['parsed_answer']
                stats['raw_changed']+=answer['raw']!=old['raw']
                if valid:stats[answer['parsed_answer']]+=1
            scene['conditions'][condition]=stats
            for key,val in stats.items():totals[condition][key]+=val
        scenes.append(scene)
    if any(t['questions']!=protocol['expected_question_count_per_condition'] for t in totals.values()):
        raise ValueError('Original total control count differs')
    if sum(t['questions'] for t in totals.values())!=protocol['expected_total_generated_answers']:
        raise ValueError('Complete control answer count differs')
    if any(t['invalid'] for t in totals.values()):decision='INCONCLUSIVE_PARSE_INVALID'
    elif totals['matched_repeat']['parsed_changed']:decision='REPEAT_INSTABILITY_IN_SCOPE'
    elif any(totals[c]['parsed_changed']==0 for c in ['blank','cyclic_mismatch']):decision='CONTENT_INSENSITIVITY_SUSPECT_IN_SCOPE'
    else:decision='REPEAT_STABLE_AND_RESPONDS_TO_CONTENT_NOT_PHYSICAL_VALIDITY'
    return {'status':'ORIGINAL8_INPUT_CONTROLS_COMPLETE_NOT_QUALITY_VALIDATION','decision':decision,
            'planned_scenes':len(rows),'generated_answers':sum(t['questions'] for t in totals.values()),
            'conditions':totals,'scenes':scenes,
            'scope':'All original8/42 questions x3 input conditions. Comparisons are response changes against original WC judge answers, not counterfactual quality accuracy, physical truth, independent confirmation or method acceptance.'}
