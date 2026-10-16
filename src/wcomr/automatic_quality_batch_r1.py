"""Complete six-dimension batch core; the production driver owns model/GPU gates.

This module imports no model and grants no execution or budget permission.
Every original position exists before a scorer is entered. JSONL events allow
read-only reconstruction after interruption without resuming unknown work.
"""
from collections import Counter
import copy
import hashlib
import json
import math
import os
from pathlib import Path
from statistics import mean
import time
import traceback

from .automatic_quality_r1 import DIMENSIONS, fingerprint, is_sha, sampling_spec, summarize, text_sha


class ResourceUnavailable(Exception):
    """Explicit missing scoring resource, distinct from a metric implementation error."""


class JournalWriteError(Exception):
    """A receipt write failed; stop work rather than silently losing a row."""


class JsonlSink:
    def __init__(self, path):
        self.path = Path(path)
        self.handle = self.path.open('x', encoding='utf-8')

    def __call__(self, event):
        self.handle.write(json.dumps(event, ensure_ascii=False, allow_nan=False, separators=(',', ':'))+'\n')
        self.handle.flush()
        os.fsync(self.handle.fileno())

    def close(self):
        self.handle.close()


def read_journal(path):
    """Keep a crash-truncated trailing write separate; never repair the original."""
    path = Path(path); before = path.stat(); raw = path.read_bytes(); after = path.stat()
    if (before.st_ino,before.st_size,before.st_mtime_ns) != (after.st_ino,after.st_size,after.st_mtime_ns):
        raise ValueError('Original scoring journal changed while reading')
    events = []; trailing = None; lines = raw.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if not line.endswith(b'\n'):
            if i != len(lines)-1: raise ValueError('Nonterminal incomplete original journal line')
            trailing = dict(bytes=len(line),sha256=hashlib.sha256(line).hexdigest())
            break
        try: events.append(json.loads(line))
        except (UnicodeDecodeError,json.JSONDecodeError) as error:
            raise ValueError('Complete original journal line is corrupt') from error
    return dict(events=events, original_path=str(path), original_bytes=len(raw),
        original_sha256=hashlib.sha256(raw).hexdigest(), incomplete_original_tail=trailing,
        original_file_modified=False, new_work_started=False)


def key(row):
    return tuple(row[k] for k in ('case_id', 'method', 'dimension'))


def initial_rows(bundle):
    if (bundle['fingerprint'] != fingerprint({k: v for k, v in bundle.items() if k != 'fingerprint'})
            or bundle['registered_generation_positions'] != 160
            or bundle['registered_metric_positions'] != 960
            or tuple(bundle['dimensions']) != DIMENSIONS
            or len(bundle['cases']) != 16 or len(bundle['methods']) != 10
            or len(set(bundle['methods'])) != 10 or len(bundle['rows']) != 960
            or bundle['scorer_fingerprint'] != fingerprint(bundle['evaluator_identity'])):
        raise ValueError('Keep the original complete160/six-dimension960 input identity')
    cases = {c['id']: c for c in bundle['cases']}
    groups = {c['prompt_id'] for c in cases.values()}
    if len(cases) != 16 or len(groups) != 8:
        raise ValueError('Keep all eight original two-seed prompt groups')
    for group in groups:
        members = [c for c in cases.values() if c['prompt_id'] == group]
        if (sorted(c['seed'] for c in members) != [17, 43]
                or any(type(c['seed']) is not int or type(c['static_eligible']) is not bool for c in members)
                or len({c['prompt'] for c in members}) != 1
                or len({c['static_eligible'] for c in members}) != 1):
            raise ValueError('Seed, prompt and static eligibility must remain paired')
    expected = {(c, m, d) for c in cases for m in bundle['methods'] for d in DIMENSIONS}
    observed = {key(r) for r in bundle['rows']}
    if len(observed) != 960 or observed != expected:
        raise ValueError('Missing, duplicated or substituted metric position')
    rows = []
    for planned in bundle['rows']:
        case = cases[planned['case_id']]
        if (planned['prompt'] != case['prompt'] or text_sha(planned['prompt']) != case['prompt_sha256']
                or planned['prompt_sha256'] != case['prompt_sha256']
                or planned['seed'] != case['seed'] or planned['prompt_id'] != case['prompt_id']
                or planned['scorer_fingerprint'] != bundle['scorer_fingerprint']
                or planned['expected_sampling'] != sampling_spec(planned['dimension'])):
            raise ValueError('Preserve actual original prompt/seed/evaluator/sampling per position')
        status = planned['input_status']
        if status not in ('READY_TO_SCORE', 'VIDEO_UNAVAILABLE', 'NOT_APPLICABLE_STATIC_SCOPE'):
            raise ValueError('Unknown source availability state')
        eligible = planned['dimension'] != 'temporal_flickering' or case['static_eligible']
        if (not eligible) != (status == 'NOT_APPLICABLE_STATIC_SCOPE'):
            raise ValueError('Do not score a new or missing static cohort')
        if status == 'READY_TO_SCORE' and (not planned['video_path'] or not is_sha(planned['video_sha256'])):
            raise ValueError('Each ready position needs original video path and SHA')
        rows.append(dict(zip(('case_id', 'method', 'dimension'), key(planned)),
            status='NOT_REACHED' if status == 'READY_TO_SCORE' else status, value=None))
    return rows


def validate_result(planned, result):
    if (not isinstance(result, dict) or key(result) != key(planned) or result['status'] != 'SCORED'
            or any(result.get(k) != planned[k] for k in ('video_sha256', 'prompt_sha256', 'scorer_fingerprint'))
            or result.get('observed_sampling') != planned['expected_sampling']
            or result.get('unweighted_original_per_video_result') is not True
            or not result.get('metric_source_sha256')
            or not all(is_sha(v) for v in result['metric_source_sha256'].values())
            or not isinstance(result.get('decoder_evidence'), dict) or not result['decoder_evidence']):
        raise ValueError('Actual per-video source, selection and evaluator evidence required')
    value = result['value']
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('Finite original per-video scalar required')
    if planned['dimension'] == 'dynamic_degree':
        if value not in (False, True, 0, 1):
            raise ValueError('Dynamic degree remains binary and descriptive')
    elif isinstance(value, bool):
        raise ValueError('A boolean cannot substitute a quality score')
    if planned['dimension'] == 'MUSIQ_LONGER512':
        frames = result.get('frame_scores', [])
        if (len(frames) != 93 or any(isinstance(v, bool) or not isinstance(v, (int, float))
                or not math.isfinite(v) for v in frames)
                or not math.isclose(mean(frames), value, rel_tol=1e-11, abs_tol=1e-12)):
            raise ValueError('The original MUSIQ raw mean needs all93 frame scores')
    json.dumps(result, allow_nan=False)
    return copy.deepcopy(result)


def failure(error):
    return dict(error_type=type(error).__name__, error=str(error),
                traceback=''.join(traceback.format_exception(type(error), error, error.__traceback__)))


def execute(bundle, comparisons, factory, emit, *, clock=time.monotonic, bootstrap_repetitions=4096):
    """One model context per eligible dimension; retain all960 slots on errors.

    ``factory`` must yield the CPU-accepted, resource-checked original scorer
    inside the already admitted production task. ``emit`` must durably append
    each event and must raise on write failure; no retry or restart is implied.
    """
    rows = initial_rows(bundle)
    comparisons = [list(pair) for pair in comparisons]
    summarize(bundle, rows, comparisons, bootstrap_repetitions=bootstrap_repetitions)
    frozen = bundle['fingerprint']; indices = {key(r): i for i, r in enumerate(rows)}
    started = clock(); lifecycle = []; stopped = None; sequence = 0

    def record(event):
        nonlocal sequence
        event = dict(event, sequence=sequence, input_bundle_fingerprint=frozen)
        try:
            emit(copy.deepcopy(event))
        except Exception as error:
            raise JournalWriteError('Original scoring journal write failed') from error
        sequence += 1

    record(dict(kind='SCOPE', rows=rows, dimensions=list(DIMENSIONS), registered_metric_positions=960,
                comparisons=comparisons, bootstrap_repetitions=bootstrap_repetitions))
    for dimension in DIMENSIONS:
        selected = [r for r in bundle['rows'] if r['dimension'] == dimension and r['input_status'] == 'READY_TO_SCORE']
        if not selected:
            info = dict(dimension=dimension, status='NO_ELIGIBLE_INPUTS_NO_SCORER_ENTERED', attempted=0)
            lifecycle.append(info)
            record(dict(kind='DIMENSION_END', lifecycle=info))
            continue
        info = dict(dimension=dimension, status='ENTERING', attempted=0, accepted=0)
        lifecycle.append(info); entered = False; begin = clock()
        try:
            with factory(dimension) as scorer:
                entered = True; info['status'] = 'VALIDATING_SCORER'
                if scorer.dimension != dimension or scorer.scorer_fingerprint != bundle['scorer_fingerprint']:
                    raise ValueError('The loaded scorer belongs to another dimension or evaluation identity')
                info['status'] = 'SCORING'; info['enter_wall_seconds'] = clock()-begin
                for planned in selected:
                    attempted = copy.deepcopy(planned); raw = None; tick = clock()
                    try:
                        raw = scorer.score(attempted)
                        if fingerprint(attempted) != fingerprint(planned):
                            raise ValueError('The scorer changed its original input position')
                        actual = validate_result(planned, raw)
                        info['accepted'] += 1
                    except Exception as error:
                        actual = dict(zip(('case_id', 'method', 'dimension'), key(planned)),
                            status='RESOURCE_UNAVAILABLE' if isinstance(error, ResourceUnavailable) else 'METRIC_FAILED',
                            value=None, **failure(error))
                        if raw is not None:
                            try: actual['original_return_json'] = json.dumps(raw, allow_nan=False, sort_keys=True)
                            except (TypeError, ValueError): actual['original_return_repr'] = repr(raw)
                    actual['metric_wall_seconds'] = clock()-tick
                    rows[indices[key(planned)]] = actual; info['attempted'] += 1
                    # This write intentionally sits outside metric exception handling.
                    record(dict(kind='ROW', row=actual))
                info['status'] = 'ROWS_FINISHED_RELEASING'
            info['status'] = 'CONTEXT_RELEASED'
        except BaseException as error:
            state = ('INTERRUPTED' if not isinstance(error, Exception) else
                     'JOURNAL_WRITE_FAILURE' if isinstance(error, JournalWriteError) else
                     'SCORER_IDENTITY_FAILURE' if info['status']=='VALIDATING_SCORER' else
                     'CONTEXT_RELEASE_FAILURE' if entered else 'SCORER_ENTER_FAILURE')
            info.update(error=failure(error), status=state)
            if not isinstance(error, Exception) or isinstance(error, JournalWriteError):
                raise
            if entered:
                # Successful raw rows stay raw evidence. Stop loading further
                # models after cleanup/record failure; never hide unknown state.
                stopped = failure(error)
                raise
            for planned in selected:
                actual = dict(zip(('case_id', 'method', 'dimension'), key(planned)),
                    status='RESOURCE_UNAVAILABLE' if isinstance(error, ResourceUnavailable) else 'METRIC_FAILED',
                    value=None, **failure(error))
                rows[indices[key(planned)]] = actual
                record(dict(kind='ROW', row=actual))
        finally:
            info['whole_context_wall_seconds'] = clock()-begin
            record(dict(kind='DIMENSION_END', lifecycle=info))
    if bundle['fingerprint'] != frozen or fingerprint({k: v for k, v in bundle.items() if k != 'fingerprint'}) != frozen:
        raise ValueError('The frozen complete input bundle changed during scoring')
    summary = summarize(bundle, rows, comparisons, bootstrap_repetitions=bootstrap_repetitions)
    counts = dict(Counter(r['status'] for r in rows))
    result = dict(status='N10_FULL960_BATCH_FINISHED_FAILURES_RETAINED',
        input_bundle_fingerprint=frozen, registered_generation_positions=160, registered_metric_positions=960,
        rows=rows, lifecycle=lifecycle, metric_status_counts=counts, summary=summary,
        all_ready_positions_scored=all(r['status']=='SCORED' for r, p in zip(rows,bundle['rows']) if p['input_status']=='READY_TO_SCORE'),
        whole_scoring_wall_seconds=clock()-started, generation_latency_claim=False,
        weighted_quality_total=None, new_generation_paths=0, stopped=stopped)
    record(dict(kind='FINAL', result=result))
    return result


def reconstruct(bundle, events):
    """Read-only replay of a known original journal; never resumes computation."""
    expected = initial_rows(bundle); lookup = {key(r): i for i, r in enumerate(expected)}
    if not isinstance(events, list) or not events:
        raise ValueError('The original scope event is missing')
    seen = set(); final = None; lifecycle = []; comparisons = None; repetitions = None
    for i, event in enumerate(events):
        if event['sequence'] != i or event['input_bundle_fingerprint'] != bundle['fingerprint']:
            raise ValueError('Original journal sequence or input identity differs')
        kind = event['kind']
        if (i == 0) != (kind == 'SCOPE') or final is not None:
            raise ValueError('One original scope and at most one final event required')
        if kind == 'SCOPE':
            if (event['rows'] != expected or event['dimensions'] != list(DIMENSIONS)
                    or event['registered_metric_positions'] != 960):
                raise ValueError('Journal scope was truncated or substituted')
            comparisons, repetitions = event['comparisons'], event['bootstrap_repetitions']
            summarize(bundle, expected, comparisons, bootstrap_repetitions=repetitions)
        elif kind == 'ROW':
            row = event['row']; identity = key(row)
            if identity not in lookup or identity in seen:
                raise ValueError('Duplicate or foreign score journal event')
            planned = bundle['rows'][lookup[identity]]
            if planned['input_status'] != 'READY_TO_SCORE':
                raise ValueError('An ineligible or unavailable video acquired a score event')
            if row['status'] == 'SCORED': validate_result(planned,row)
            elif row['status'] not in ('RESOURCE_UNAVAILABLE','METRIC_FAILED') or row.get('value') is not None:
                raise ValueError('Unknown or zero-filled journal failure')
            seen.add(identity); expected[lookup[identity]] = copy.deepcopy(row)
        elif kind == 'DIMENSION_END':
            info = event['lifecycle']
            if info['dimension'] not in DIMENSIONS or info['dimension'] in {r['dimension'] for r in lifecycle}:
                raise ValueError('Foreign or duplicated scorer lifecycle')
            lifecycle.append(copy.deepcopy(info))
        elif kind == 'FINAL':
            final = event['result']
            if (final['status'] != 'N10_FULL960_BATCH_FINISHED_FAILURES_RETAINED'
                    or final['rows'] != expected or final['input_bundle_fingerprint'] != bundle['fingerprint']
                    or final['lifecycle'] != lifecycle
                    or final['registered_generation_positions'] != 160 or final['registered_metric_positions'] != 960
                    or final['metric_status_counts'] != dict(Counter(r['status'] for r in expected))
                    or final['all_ready_positions_scored'] != all(r['status']=='SCORED' for r, p in zip(expected,bundle['rows']) if p['input_status']=='READY_TO_SCORE')
                    or final['summary'] != summarize(bundle,expected,comparisons,bootstrap_repetitions=repetitions)
                    or final['generation_latency_claim'] is not False or final['weighted_quality_total'] is not None
                    or final['new_generation_paths'] != 0 or final['stopped'] is not None):
                raise ValueError('Final summary hid an original row or lifecycle failure')
        else:
            raise ValueError('Unknown original journal record')
    return dict(status='ORIGINAL_FINAL_JOURNAL_REBUILT' if final is not None else 'ORIGINAL_INTERRUPTED_JOURNAL_REBUILT_NOT_RESUMED',
        registered_metric_positions=960, rows=expected, lifecycle=lifecycle, final=final,
        metric_status_counts=dict(Counter(r['status'] for r in expected)), new_work_started=False)
