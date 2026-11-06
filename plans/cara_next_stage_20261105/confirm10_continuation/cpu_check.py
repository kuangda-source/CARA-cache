"""Pure CPU checks for the continuation quote, hash contract and refusal row. No CUDA."""
import copy
import hashlib
import json
import math
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(HERE)]
from prepare import build, request_quote, ARMS
from postprocess import interval, require_inherited_scores, require_original_settlement, require_score_release, summarize, write_results
from plans.cara_next_stage_20261104.sensitivity.runner import assert_inherited_hashes, note_noncomplete

ORIGINAL = [
    'plans/cara_next_stage_20261105/confirm10/manifest.json',
    'plans/cara_next_stage_20261105/confirm10/quote.json',
    'reports/cara_generator_v1_confirm10_r1_20261105/collection.json',
    'reports/cara_generator_v1_confirm10_r1_20261105/central_settlement.json',
    'reports/cara_generator_v1_confirm10_r1_20261105/output_inventory.json',
    'reports/cara_generator_v1_confirm10_r1_20261105/partial_scores.json',
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    before = {name: sha(ROOT / name) for name in ORIGINAL}
    card = build()
    after = {name: sha(ROOT / name) for name in ORIGINAL}
    assert before == after
    disk = json.loads((HERE / 'manifest.json').read_text())
    quote = json.loads((HERE / 'quote.json').read_text())
    assert disk == card
    assert quote['hard_GPUh'] == 2.2 and quote['execution_authorized'] is False
    assert card['untouched_sources'] == before
    original_prices = json.loads((ROOT / 'plans/cara_next_stage_20261105/confirm10/quote.json').read_text())['request_prices_seconds']
    prices = {name: original_prices[name] for name in ARMS}
    raw, center, bounds, hard = request_quote(prices)
    exact = sum((Decimal('70.734852') + Decimal('6.772260') * n + Decimal('0.993956') * a)
        for n, a in ((36, 0), (17, 10), (18, 0), (16, 0), (21, 0))) * 5
    assert exact == Decimal('5475.089500')
    assert raw == 5475.0895 and center == 2.0062773472222224
    assert bounds == [1.7021057083333335, 2.1583631666666667] and hard == 2.2
    assert math.ceil(bounds[1] * 10) / 10 == 2.2
    upper = (Decimal('1.2') * exact + 1200) / 3600
    assert (upper / Decimal('0.1')).to_integral_value(rounding=ROUND_CEILING) * Decimal('0.1') == Decimal('2.2')
    assert bounds[1] > 2.1
    assert card['quote']['forecast_GPUh'] == center and card['quote']['request_sum_seconds'] == raw
    assert card['quote']['arithmetic_verification']['supplied_hard_GPUh_not_used'] == 2.1
    assert card['quote']['arithmetic_verification']['measured_partial_means_not_used'] is True
    assert card['quote']['anchors']['predicted_T_DD_seconds']['F17_A2_LIGHT_C'] == 131.65259999174998

    assert card['GPU_dispatch_ready'] is False and card['authority']['execution_authorized'] is False
    assert card['authority']['ledger_reservation_authorized'] is False
    assert card['claims_completion'] is False and card['original_ten_input_endpoint'] == 'NOT_EVALUABLE'
    assert [slot['id'] for slot in card['matrix']] == [f'CONFIRM10_{i:03d}' for i in range(27, 52)]
    assert card['counts']['total_requests'] == 25 and card['counts']['warm'] == 0 and card['counts']['LPIPS_pairs'] == 36
    assert card['excluded_cohort']['ids'] == [f'CONFIRM10_{i:03d}' for i in range(22, 27)]
    assert EXCLUDED_NOT_IN_MATRIX(card)
    original_manifest = json.loads((ROOT / 'plans/cara_next_stage_20261105/confirm10/manifest.json').read_text())
    assert card['roles'] == {name: original_manifest['roles'][name] for name in ARMS}
    assert card['mask_summary'] == {name: original_manifest['mask_summary'][name] for name in ARMS}
    assert len(card['inherited_outputs']['rows']) == 21
    assert len(card['inherited_score_rows']) == 16
    collection = json.loads((ROOT / ORIGINAL[2]).read_text())
    assert collection['status'] == 'FAILED_NO_RETRY'
    require_original_settlement(card)
    require_inherited_scores(card)

    saved = []
    row = dict(slot=dict(id='CONFIRM10_030', member='av_0b82886b-be71-49f9-83a3-346bc0134c4b', role='R16C', seed=0), status='RUNNING')
    try:
        note_noncomplete(dict(record_noncomplete_on_row=True), row, dict(status='TEXT_REJECTED', solver_steps=0, guided_pairs=0), lambda: saved.append(copy.deepcopy(row)))
    except ValueError as error:
        message = str(error)
    else:
        raise AssertionError('TEXT_REJECTED must stop the run')
    assert message == 'Rejected/incomplete request; retain denominator, no replacement'
    assert row['status'] == 'TEXT_REJECTED' and row['refusal']['solver_steps'] == 0 and saved
    assert row['slot']['member'] == 'av_0b82886b-be71-49f9-83a3-346bc0134c4b'
    untouched = dict(slot=dict(id='CONFIRM10_030', member='same'), status='RUNNING')
    try:
        note_noncomplete({}, untouched, dict(status='TEXT_REJECTED', solver_steps=0, guided_pairs=0), lambda: None)
    except ValueError:
        pass
    assert untouched['status'] == 'RUNNING' and 'refusal' not in untouched

    with tempfile.TemporaryDirectory(prefix='cara-confirm10-continuation-') as directory:
        root = Path(directory)
        fixture = copy.deepcopy(card)
        rows = []
        for item in fixture['inherited_outputs']['rows']:
            copied = copy.deepcopy(item)
            for key, suffix in (('latent_artifact', '.pt'), ('video_artifact', '.mp4')):
                path = root / (copied['slot']['id'] + suffix)
                path.write_bytes(copied['slot']['id'].encode() + suffix.encode())
                copied[key] = dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size)
            rows.append(copied)
        fixture['inherited_outputs']['rows'] = rows
        fixture['inherited_outputs']['output_root'] = str(root)
        videos = {row['slot']['id']: row['video_artifact']['sha256'] for row in rows}
        natives = {row['slot']['member']: row['video_artifact']['sha256'] for row in rows
            if row['slot']['role'] == 'NATIVE35' and row['slot']['section'] != 'warm'}
        for score in fixture['inherited_score_rows']:
            score['video_sha256'] = videos[score['slot']['id']]
            score['reference_sha256'] = natives[score['slot']['member']]
        assert_inherited_hashes(fixture)
        release = dict(GPU_released=True, mode_restored=True, cost_settled=True,
            original_processes_ended=True, container_exit_success=True, hard_limit_exceeded=False)
        collection_state = dict(status='COMPLETE_PENDING_RELEASE_SCORING', run_id=fixture['run_id'],
            scope_sha256=fixture['scope_sha256'], claims_completion=False,
            rows=[dict(slot=copy.deepcopy(slot), status='COMPLETE') for slot in fixture['matrix']])
        blocked = copy.deepcopy(release)
        blocked['container_exit_success'] = False
        try:
            require_score_release(fixture, blocked, collection_state)
        except ValueError as error:
            assert 'GPU/CPU release' in str(error)
        else:
            raise AssertionError('unreleased continuation must not score')
        rows[0]['video_artifact']['sha256'] = '0' * 64
        try:
            assert_inherited_hashes(fixture)
        except ValueError as error:
            assert 'not hash-reusable' in str(error)
        else:
            raise AssertionError('changed inherited bytes must fail')

        members = list(card['inputs_by_alias'].values())
        values = dict(F17_A2_LIGHT_C=.25, R16C=.24, R18C=.22, R21C=.20)
        rows = [dict(slot=dict(member=member, role=role), Alex=values[role], T_DD=100., mask_matches=True)
            for member in members for role in values]
        fixture_card = copy.deepcopy(card)
        fixture_card['bootstrap'] = dict(card['bootstrap'], replicates=1000)
        native = {member: 200. for member in members}
        summary = summarize(fixture_card, rows, native)
        assert summary['primary_success'] and summary['formal_scores'] == 36 and summary['scientific_inputs'] == 9
        assert abs(summary['contrasts'][0]['mean_delta'] + .03) < 1e-12
        for row in rows:
            if row['slot']['role'] == 'R18C':
                row['Alex'] = .255
        assert summarize(fixture_card, rows, native)['verdict'] == 'SECONDARY_NONINFERIOR'
        for row in rows:
            if row['slot']['role'] == 'R18C':
                row['Alex'] = .27
        assert summarize(fixture_card, rows, native)['verdict'] == 'INCONCLUSIVE'
        incomplete = summarize(fixture_card, rows[:16], native)
        assert incomplete['status'] == 'NOT_COMPLETE' and incomplete['claims_completion'] is False
        assert 'verdict' not in incomplete
        try:
            summarize(fixture_card, rows + [dict(slot=dict(member='av_snowy_1_0', role='R18C'), Alex=.2, T_DD=1., mask_matches=True)], native)
        except ValueError as error:
            assert 'C05' in str(error)
        else:
            raise AssertionError('C05 must stay out of the denominator')
        output = root / 'analysis' / 'complete_analysis.json'
        write_results(output, summary)
        text = (output.parent / 'COMPLETE_RESULTS.md').read_text()
        assert text.index('Frozen prediction comparison') < text.index('Verdict:')
        assert 'improved/9' in text and 'av_snowy_1_0 is not in this denominator' in text
        assert interval([-.04, .02], fixture_card['bootstrap']) == [-.04, .02]

    prereg = (HERE / 'PREREGISTRATION.md').read_text()
    handoff = (HERE / 'RUN_HANDOFF.md').read_text()
    for needle in ('5475.0895', '2.0062773472222224', '1.7021057083333335', '2.1583631666666667', '2.2',
            'CONFIRM10_027', 'CONFIRM10_051', 'av_snowy_1_0', 'NOT_EVALUABLE'):
        assert needle in prereg
    assert '4a1a7ed73478e166f72d62b27b1faf8b49c09737702f19f64cf2c67aa100b100' in handoff
    assert '不上卡' in prereg and 'GPU_dispatch_ready=false' in handoff
    assert 'k18' in prereg and 'P 探针' in prereg
    value = dict(passed=True, requests=25, formal=25, warm=0, scientific_inputs=9, planned_LPIPS_pairs=36,
        inherited_outputs=21, inherited_pairs=16, new_pairs=20,
        request_sum_seconds=raw, forecast_GPUh=center, range_GPUh=bounds, hard_GPUh=hard,
        scope_sha256=card['scope_sha256'], GPU_dispatch_ready=False, ledger_reservations=0, GPU_submissions=0,
        remote_calls=0, scientific_endpoint='NOT_RUN', original_files_unchanged=True)
    text = json.dumps(value, indent=2) + '\n'
    (HERE / 'cpu_check.json').write_text(text)
    report = ROOT / 'reports/cara_generator_v1_confirm10_continuation_r1_20261106'
    report.mkdir(parents=True, exist_ok=True)
    (report / 'cpu_acceptance.json').write_text(text)
    print(text)


def EXCLUDED_NOT_IN_MATRIX(card):
    excluded = set(card['excluded_cohort']['ids'])
    return not any(slot['id'] in excluded or slot['member'] == 'av_snowy_1_0' for slot in card['matrix'])


if __name__ == '__main__':
    main()
