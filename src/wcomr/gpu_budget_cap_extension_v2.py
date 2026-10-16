"""Apply an explicit human-approved cap increase without resetting the pool.

This helper never constructs approval, reserves a job, dispatches a process or
writes a compatibility ledger. It is separate from the frozen sampler source.
"""
import copy
import json
from pathlib import Path

from .gpu_budget_pool_v2 import BudgetPool, finite, sha


EVENT = 'EXTEND_CUMULATIVE_CAP_PRESERVE_ORIGIN_AND_ALL_JOBS'


def extend_cap(project, approval_file):
    project = Path(project).resolve()
    path = Path(approval_file).resolve()
    if not path.is_relative_to(project) or not path.is_file():
        raise ValueError('Original project-local direct human approval required')
    authority = json.loads(path.read_text())
    old = authority.get('previous_cumulative_cap_GPUh')
    new = authority.get('cumulative_cap_GPUh')
    origin = authority.get('budget_origin_used_GPUh')
    if (authority.get('approval_state') != 'HUMAN_APPROVED'
            or authority.get('budget_cap_extension_explicitly_approved') is not True
            or authority.get('direct_user_authorization') is not True
            or not authority.get('user_reply_quote') or not authority.get('approval_id')
            or not all(finite(v) for v in (old, new, origin))
            or not 0 <= origin < old < new):
        raise ValueError('An explicit increase approved by the human is required; a proposal is insufficient')
    authorization_sha = sha(path)
    pool = BudgetPool(project)
    with pool.transaction() as value:
        if value is None:
            raise ValueError('Do not initialize a new window while extending an existing pool')
        if (value['origin_used_gpu_hours'] != origin
                or any(value[k] != v for k, v in pool.accounting(value).items())):
            raise ValueError('Original window and settled/reserved accounting must be unchanged')
        prior = [e for e in value['events'] if e.get('type') == EVENT
                 and e.get('approval_id') == authority['approval_id']]
        if prior:
            if (len(prior) != 1 or prior[0]['authorization_sha256'] != authorization_sha
                    or prior[0]['previous_cap_GPUh'] != old or prior[0]['new_cap_GPUh'] != new
                    or value['cap_gpu_hours'] != new):
                raise ValueError('Conflicting original cap-extension approval')
            return dict(status='ORIGINAL_CAP_EXTENSION_ALREADY_APPLIED_NO_WRITE',
                        authorization_sha256=authorization_sha, pool=copy.deepcopy(value))
        if value['cap_gpu_hours'] != old:
            raise ValueError('Approval must name the actual current cumulative cap')
        value['cap_gpu_hours'] = new
        pool.commit(value, dict(type=EVENT, approval_id=authority['approval_id'],
            authorization_ref=str(path.relative_to(project)), authorization_sha256=authorization_sha,
            previous_cap_GPUh=old, new_cap_GPUh=new))
        return dict(status='APPROVED_CAP_EXTENDED_ORIGIN_AND_JOBS_PRESERVED',
                    authorization_sha256=authorization_sha, pool=copy.deepcopy(value))
