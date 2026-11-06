"""Bound original inputs and persist complete single-question development scoring."""
import hashlib
import json
import math
from pathlib import Path
from wcomr.development_vqa import SYSTEM, BEGIN, validate_questions, arm_order, score_answer, summarize


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_bound(path, expected):
    if sha256(path) != expected:
        raise ValueError('Input hash mismatch: ' + str(path))
    return json.loads(Path(path).read_text())


def validate_protocol(p):
    expected = {'system': SYSTEM, 'begin_user': BEGIN, 'fps_requested': 2.0,
                'actual_sampled_frames': 10, 'sampled_frame_indices': [0,10,20,31,41,51,61,72,82,92],
                'source_frames': 93, 'source_fps': 16, 'max_pixels': 602112,
                'image_patch_size': 16, 'video_backend': 'decord',
                'do_sample_frames_in_processor': False, 'max_gpu_seconds': 900,
                'judge_repo': 'Qwen/Qwen3-VL-2B-Instruct',
                'judge_revision': '89644892e4d85e24eaac8bacfd4f463576704203',
                'generation': {'dtype': 'bfloat16', 'attention': 'sdpa', 'do_sample': False,
                               'max_new_tokens': 1024, 'seed': 0}}
    if any(p.get(k) != v for k,v in expected.items()):
        raise ValueError('Frozen VQA protocol differs')


def load_questions(project, protocol):
    inputs = protocol['question_inputs']['samples']
    if [item['name'] for item in inputs] != protocol['samples']:
        raise ValueError('Original question membership differs')
    result = {}
    for item in inputs:
        path = Path(project)/protocol['runtime_question_directory']/(item['name']+'.json')
        if path.stat().st_size != item['bytes']:
            raise ValueError('Original question size differs')
        questions = load_bound(path, item['sha256'])
        validate_questions(questions)
        if len(questions) != item['root_count']:
            raise ValueError('Original question count differs')
        result[item['name']] = questions
    if sum(map(len,result.values())) != protocol['planned_reference_questions']:
        raise ValueError('Original total question count differs')
    return result


def evaluate_cases(cases, questions_by_name, evaluate_video, rows, save):
    """Each question once; rejected candidates retain original scene/question rows.

    evaluate_video returns an iterator and provenance. Saving every raw answer
    preserves actual partial coverage if timeout/forward/decode fails mid-arm.
    """
    for case in cases:
        name = case['name']; questions = questions_by_name[name]
        outcome = case['candidate']['outcome']
        row = {'name':name, 'candidate_outcome':outcome, 'status':'SCORING',
               'arm_order':arm_order(name), 'reference':{'answers':[]}}
        if outcome == 'ACCEPTED': row['candidate'] = {'answers':[]}
        elif outcome not in ['TEXT_REJECTED','VIDEO_REJECTED']:
            raise ValueError('Unknown candidate outcome')
        if case['reference']['outcome'] != 'ACCEPTED':
            raise ValueError('Reference must retain original accepted video')
        rows.append(row); save()
        for arm in row['arm_order']:
            if arm == 'candidate' and outcome != 'ACCEPTED': continue
            row['current_arm'] = arm; save()
            outputs, provenance = evaluate_video(case[arm], questions)
            row[arm]['input'] = provenance; row[arm]['generation_records'] = []; save()
            iterator = iter(outputs)
            for question in questions:
                raw, record = next(iterator)
                row[arm]['answers'].append(score_answer(question, raw))
                row[arm]['generation_records'].append(record); save()
            try: next(iterator)
            except StopIteration: pass
            else: raise ValueError('Unexpected extra generated answer')
            row[arm]['status'] = 'ALL_ORIGINAL_QUESTIONS_SCORED'; save()
        row['status'] = 'SCORING_COMPLETE'; row.pop('current_arm',None); save()
    return summarize(rows, [case['name'] for case in cases], questions_by_name)


def summarize_receipt(receipt, protocol, questions, cases):
    validate_protocol(protocol)
    if receipt['protocol'] != protocol or receipt['status'] != 'W1_VQA_ALL_ORIGINAL8_QUESTIONS_ATTEMPTED':
        raise ValueError('Incomplete or changed VQA protocol/receipt')
    rows=receipt['rows']
    if [r['name'] for r in rows] != protocol['samples'] or [c['name'] for c in cases] != protocol['samples']:
        raise ValueError('Original scene coverage differs')
    for row,case in zip(rows,cases):
        if row['status'] != 'SCORING_COMPLETE' or row['arm_order'] != arm_order(row['name']) or row['candidate_outcome'] != case['candidate']['outcome']:
            raise ValueError('Original outcomes/order/complete coverage differs')
        for arm in ['reference','candidate']:
            if case[arm]['outcome'] != 'ACCEPTED':
                if arm in row:raise ValueError('Rejected candidate imputed')
                continue
            scored=row[arm];provenance=scored['input'];metadata=provenance['metadata']
            if scored['status'] != 'ALL_ORIGINAL_QUESTIONS_SCORED' or provenance['video_sha256'] != case[arm]['video_sha256']:
                raise ValueError('Video provenance or question status differs')
            if metadata['frames_indices'] != protocol['sampled_frame_indices'] or metadata['total_num_frames'] != 93 or metadata['fps'] != 16 or metadata['video_backend'] != 'decord':
                raise ValueError('Timestamped input provenance differs')
            records=scored['generation_records']
            if [r['uid'] for r in records] != [q['uid'] for q in questions[row['name']]]:
                raise ValueError('Original generated question coverage differs')
            for record in records:
                if record['generated_tokens'] != len(record['generated_token_ids']) or record['generated_tokens'] > 1024 or record['reached_token_cap'] != (record['generated_tokens']>=1024) or not math.isfinite(record['seconds']) or record['seconds']<0:
                    raise ValueError('Generation token/time receipt differs')
    result=summarize(rows,protocol['samples'],questions)
    if receipt['summary'] != result:
        raise ValueError('Summary differs from original raw answers')
    return result
