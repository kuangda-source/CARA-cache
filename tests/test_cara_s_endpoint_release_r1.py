"""Synthetic endpoint terminal packets and actual temporary-ledger I/O only."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wcomr import cara_s_endpoint_lifecycle_r1 as lifecycle
from wcomr import cara_s_endpoint_release_r1 as endpoint
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_s_uniform_endpoint_binding_r1 import map_physical_slots
from wcomr.cara_s_uniform_endpoint_execution_r1 import request_card
from wcomr.gpu_budget_pool_v2 import BudgetPool, SCHEMA, sha
from wcomr.policy_price_terminal_r1 import record
from test_cara_budget_lifecycle_r1 import fixture, put

ROOT = Path(__file__).resolve().parents[1]


def encoded_sha(value):
    return hashlib.sha256((json.dumps(value, indent=2) + '\n').encode()).hexdigest()


def endpoint_fixture(alias=False):
    proposal = json.loads((ROOT / 'plans/cara_next_stage_20261028/mainline/r2/S_UNIFORM_BUDGET_ENDPOINT32_PROPOSAL_R1_20261031.json').read_text())
    base = load_card(ROOT, 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    policy = proposal['new_policies']['SU19_CFG_C'] if alias else base['roles']['UNIFORM19_C']['policy']
    bound = map_physical_slots(proposal, policy)
    bound.update(CPU_fixture_only=True, proposal_scope_sha256=proposal['scope_sha256'],
                 original_freeze_sha256='b' * 64,
                 original_calibration=dict(launch_id='CPU-ORIGINAL-BUDGET-NOT-ENDPOINT', CPU_fixture_only=True))
    bound['binding_sha256'] = digest(bound)
    card = request_card(proposal, bound, base)
    extra = {lifecycle.SOURCE: sha(lifecycle.__file__), endpoint.SOURCE: sha(endpoint.__file__),
             endpoint.EXECUTION_SOURCE: sha(ROOT / endpoint.EXECUTION_SOURCE),
             endpoint.CARD: encoded_sha(card), endpoint.BINDING: encoded_sha(bound)}
    capture, _, job = fixture(host='two_card', gpu_uuid=proposal['gpu_uuid'],
                             run_id='CPU-ENDPOINT-' + str(len(card['physical_matrix'])),
                             billed_limit_GPUh=5.25, extra_sources=extra)
    authority = record(capture, 'authorization')
    authority.update(scope_sha256=card['scope_sha256'], new_endpoint_authorization=True,
        card_kind='CARA_SU19_BUDGET_ENDPOINT', physical_paths=len(card['physical_matrix']),
        endpoint_binding_sha256=bound['binding_sha256'], original_budget_freeze_sha256=bound['original_freeze_sha256'])
    auth_sha = put(capture, 'authorization', authority)
    job.update(scope_sha256=card['scope_sha256'], authorization_sha256=auth_sha)
    reservation_sha = put(capture, 'central_reservation', dict(central_ledger_host='four_card', job=job))
    launch = record(capture, 'launch')
    launch.update(scope_sha256=card['scope_sha256'], authorization_sha256=auth_sha,
        central_reservation_sha256=reservation_sha, physical_paths=len(card['physical_matrix']),
        endpoint_binding_sha256=bound['binding_sha256'], original_budget_freeze_sha256=bound['original_freeze_sha256'])
    expected = put(capture, 'launch', launch)
    bill = record(capture, 'billing'); bill['scope_sha256'] = card['scope_sha256']
    bill_sha = put(capture, 'billing', bill)
    guardian = record(capture, 'guardian')
    guardian.update(status='CARA_ENDPOINT_GUARDIAN_TERMINAL_R1', scope_sha256=card['scope_sha256'], billing_sha256=bill_sha)
    put(capture, 'guardian', guardian)
    pending = record(capture, 'pending_release'); pending['scope_sha256'] = card['scope_sha256']
    put(capture, 'pending_release', pending)
    put(capture, 'endpoint_card', card); put(capture, 'endpoint_binding', bound)
    rows = []
    for slot in card['physical_matrix']:
        result = dict(slot_id=slot['id'], role=slot['role'], concrete_role=slot['role'],
            scope_sha256=card['scope_sha256'], CPU_fixture=True, solver_steps=36, guided_pairs=36,
            audit_enabled=False, in_timing_guided_copies=0, in_timing_hashes=0, research_checkpoints=0,
            T_DD=.5, T_request=1.)
        policy = card['roles'][slot['role']].get('policy')
        if policy: result['semantic_history'] = [dict(actual=a, fallback_reason=None) for a in policy['actions']]
        rows.append(dict(slot=slot, status='COMPLETE', result=result))
    collection = dict(phase='B', status='TERMINAL', scope_sha256=card['scope_sha256'], rows=rows)
    put(capture, 'collection', collection)
    put(capture, 'runner_terminal', dict(scope_sha256=card['scope_sha256'], collection_sha256=digest(collection)))
    return capture, expected, job, card, bound


class EndpointRelease(unittest.TestCase):
    def setUp(self):
        self.capture, self.expected, self.job, self.card, self.bound = endpoint_fixture()
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.pool = BudgetPool(self.temp.name)
        value = dict(schema=SCHEMA, cap_gpu_hours=226., origin_used_gpu_hours=50., origin_gpu_jobs_launched=10,
            jobs={'old-unknown-16.5': dict(status='RESERVED_OR_RUNNING', gpu_uuid='GPU-OLD', billed_limit_GPUh=16.5),
                  self.job['job_id']: self.job}, events=[])
        value.update(self.pool.accounting(value)); self.pool.path.parent.mkdir(parents=True)
        self.pool.path.write_text(json.dumps(value))

    def settle(self):
        launch, bill = lifecycle.financial_terminal(self.capture, self.expected, cpu_validation=True)
        before = self.pool.read()
        after = self.pool.settle(launch['run_id'], bill['actual_GPUh'], self.capture['files']['billing']['sha256'])
        return dict(central_ledger_host='four_card', launch_id=launch['launch_id'],
                    billing_sha256=self.capture['files']['billing']['sha256'], central_before=before, central_after=after)

    def release(self, settlement=None):
        return endpoint.released_collection(self.capture, self.expected, settlement or self.settle(),
                                            self.card, self.bound, cpu_validation=True)

    def change(self, key, fn):
        value = record(self.capture, key); fn(value); put(self.capture, key, value)

    def no_collection(self, fn):
        original = endpoint.record
        def guarded(capture, name):
            if name == 'collection': raise AssertionError('Collection opened before release/identity gate')
            return original(capture, name)
        with patch.object(endpoint, 'record', side_effect=guarded):
            with self.assertRaises(ValueError): fn()

    def test_success32_unique_bill_and_no_scoring_authority(self):
        first = self.settle(); second = self.settle()
        self.assertEqual(first['central_after'], second['central_after'])
        result = self.release(second)
        self.assertEqual(result['physical_paths'], 32)
        self.assertEqual(result['lifecycle']['actual_GPUh'], .05)
        self.assertEqual(second['central_after']['reserved_gpu_hours'], 16.5)
        self.assertFalse(result['scoring_dispatch_allowed'])
        self.assertFalse(result['artifact_identity_accepted'])
        self.assertFalse(result['scientific_accepted'])

    def test_alias25_keeps_complete_scope(self):
        self.capture, self.expected, self.job, self.card, self.bound = endpoint_fixture(True)
        ledger = self.pool.read(); ledger['jobs'] = {'old-unknown-16.5': ledger['jobs']['old-unknown-16.5'], self.job['job_id']: self.job}
        ledger.update(self.pool.accounting(ledger)); self.pool.path.write_text(json.dumps(ledger))
        self.assertEqual(self.release()['physical_paths'], 25)
        self.assertEqual(len(self.card['formal_matrix']), 24)

    def test_failed_container_still_settles_without_collection(self):
        self.capture['container']['state'].update(ExitCode=137, OOMKilled=True)
        self.change('guardian', lambda g: g.update(container_exit_code=137, error_type='CPU_SIMULATED_OOM',
            container_terminal_witness={**g['container_terminal_witness'], 'container': self.capture['container']}))
        receipt = self.settle()
        self.assertEqual(receipt['central_after']['jobs'][self.job['job_id']]['actual_GPUh'], .05)
        self.no_collection(lambda: self.release(receipt))

    def test_missing_collection_does_not_block_financial_settlement(self):
        self.capture['files']['collection'] = dict(exists=False)
        self.assertEqual(self.settle()['central_after']['reserved_gpu_hours'], 16.5)

    def test_live_original_handle_refuses_finance(self):
        self.capture['process_observations']['runner']['original_live'] = True
        self.no_collection(self.release)

    def test_unknown_container_refuses_finance(self):
        self.change('guardian', lambda g: g['container_terminal_witness'].update(complete=False))
        self.no_collection(self.release)

    def test_unsettled_before_collection(self):
        receipt = self.settle(); receipt['central_after'] = receipt['central_before']
        self.no_collection(lambda: self.release(receipt))

    def test_unrestored_mode_before_collection(self):
        self.change('guardian', lambda g: g['mode_restoration'].update(restored=False))
        self.no_collection(self.release)

    def test_live_lock_before_collection(self):
        self.capture['own_UUID_lock_free'] = False
        self.no_collection(self.release)

    def test_wrong_collection_order(self):
        self.change('collection', lambda c: c['rows'].reverse())
        with self.assertRaisesRegex(ValueError, 'ordered'): self.release()

    def test_partial_collection(self):
        self.change('collection', lambda c: c['rows'][7].update(status='TECH_FAILED'))
        with self.assertRaisesRegex(ValueError, 'Incomplete'): self.release()

    def test_changed_runner_digest(self):
        self.change('runner_terminal', lambda c: c.update(collection_sha256='a' * 64))
        with self.assertRaisesRegex(ValueError, 'runner collection'): self.release()

    def test_changed_bound_card_refused_before_collection(self):
        self.change('endpoint_card', lambda c: c.update(extra='changed'))
        self.no_collection(self.release)

    def test_changed_original_launch_sha_refused(self):
        self.expected = '0' * 64
        self.no_collection(self.release)

    def test_cpu_fixture_cannot_certify_production(self):
        receipt = self.settle()
        with self.assertRaisesRegex(ValueError, 'CPU fixtures'):
            endpoint.released_collection(self.capture, self.expected, receipt, self.card, self.bound)

    def test_old_liability_cannot_be_erased(self):
        receipt = self.settle()
        receipt['central_after']['jobs']['old-unknown-16.5']['billed_limit_GPUh'] = 0
        self.no_collection(lambda: self.release(receipt))

    def test_original_active_budget_reader_not_modified(self):
        original = (ROOT / 'src/wcomr/cara_budget_lifecycle_r1.py').read_text()
        adapted = Path(lifecycle.__file__).read_text()
        adapted = adapted.replace('Read-only endpoint allocation closure', 'Read-only prospective calibration closure')
        adapted = adapted.replace('complete-endpoint scientific acceptance', 'complete-search scientific acceptance')
        adapted = adapted.replace('src/wcomr/cara_s_endpoint_lifecycle_r1.py', 'src/wcomr/cara_budget_lifecycle_r1.py')
        adapted = adapted.replace('CARA_ENDPOINT_GUARDIAN_TERMINAL_R1', 'BUDGET_CALIBRATION_GUARDIAN_TERMINAL')
        adapted = adapted.replace('complete_endpoint_accepted=False', 'complete_search_accepted=False')
        self.assertEqual(ast.dump(ast.parse(original)), ast.dump(ast.parse(adapted)))


if __name__ == '__main__': unittest.main()
