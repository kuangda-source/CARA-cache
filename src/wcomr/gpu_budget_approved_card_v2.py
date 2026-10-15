"""Admission of specifically approved >=12 GPUh cards into the existing pool.

The original under12 reserve/settle implementation remains unchanged. This
extension reads an exact approval file, preserves the pool origin/cap, and
reserves the entire approved limit in the same short transaction.
"""
import copy
import json
from pathlib import Path
import time

from .gpu_budget_pool_v2 import BudgetPool, finite, sha


class ApprovedCardBudgetPool(BudgetPool):
    def reserve_specific_whole_card(self, job, gpu, authorization_file):
        job = copy.deepcopy(job)
        path = Path(authorization_file).resolve()
        if not path.is_relative_to(self.project) or sha(path) != job.get('authorization_sha256'):
            raise ValueError('Original project-local whole-card approval file and SHA required')
        authority = json.loads(path.read_text())
        forecast, limit = job['forecast_GPUh'], job['billed_limit_GPUh']
        if (not finite(forecast) or not finite(limit) or not 0 < forecast <= limit or limit < 12
                or authority.get('kind') != 'SPECIFIC_WHOLE_CARD_APPROVAL'
                or authority.get('direct_user_authorization') is not True
                or not authority.get('user_reply_quote') or not job.get('job_id')
                or not job.get('launch_id') or not job.get('scope_counts')
                or not job.get('config_sha256') or not job.get('source_revision')
                or not job.get('production_CPU_sha256') or not job.get('bound_input_fingerprint')):
            raise ValueError('A specific full >=12GPUh approval, source, CPU, scope and whole cost are required')
        pairs = (
            ('source_revision', 'source_revision'), ('launch_id', 'launch_id'),
            ('whole_card_run', 'run_id'), ('gpu_uuid', 'gpu_uuid'),
            ('config_sha256', 'config_sha256'), ('production_CPU_sha256', 'production_CPU_sha256'),
            ('bound_input_fingerprint', 'bound_input_fingerprint'), ('scope_counts', 'scope_counts'),
            ('forecast_complete_GPUh', 'forecast_GPUh'), ('billed_limit_GPUh', 'billed_limit_GPUh'),
            ('cumulative_cap_GPUh', 'cumulative_cap_GPUh'), ('budget_origin_used_GPUh', 'budget_origin_used_GPUh'),
        )
        if any(authority.get(a) != job.get(b) for a, b in pairs):
            raise ValueError('Approved complete card differs from the proposed reservation')
        if (gpu['uuid'] != job['gpu_uuid'] or 'A6000' not in gpu['name']
                or gpu['compute_cap'] != '8.6' or not finite(gpu['memory_used_mib'])
                or not 0 <= gpu['memory_used_mib'] <= 1024 or gpu['pids']):
            raise ValueError('Fresh idle actual UUID required for the approved complete card')
        with self.transaction() as value:
            if value is None or value.get('budget_overrun_recorded'):
                raise ValueError('Pool unavailable or overrun requires reconciliation')
            if (value['cap_gpu_hours'] != job['cumulative_cap_GPUh']
                    or value['origin_used_gpu_hours'] != job['budget_origin_used_GPUh']):
                raise ValueError('Approval cannot reset the original pool origin or change its cap')
            if job['job_id'] in value['jobs']:
                raise ValueError('Original approved job already exists; never dispatch it twice')
            if limit > self.accounting(value)['available_gpu_hours'] + 1e-10:
                raise ValueError('Whole approved reservation exceeds the actual cumulative balance')
            if any(j['status'] == 'RESERVED_OR_RUNNING' and j['gpu_uuid'] == job['gpu_uuid']
                   for j in value['jobs'].values()):
                raise ValueError('Actual UUID already belongs to an original job')
            job.update(status='RESERVED_OR_RUNNING', kind='V2_SPECIFIC_WHOLE_CARD_APPROVAL',
                       reserved_unix=time.time(), authorization_ref=str(path.relative_to(self.project)))
            value['jobs'][job['job_id']] = job
            self.commit(value, dict(type='RESERVE_SPECIFICALLY_APPROVED_WHOLE_JOB',
                job_id=job['job_id'], authorization_sha256=job['authorization_sha256']))
            return copy.deepcopy(value)
