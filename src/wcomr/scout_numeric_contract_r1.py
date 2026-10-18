"""Exact scopes for the two scouts; this is a numerical CPU contract only."""
import os
from .scout_sampling_r1 import plans, matrix as rows

KIND=os.environ.get('WC_SCOUT_KIND')
if KIND not in ('CAL12','BANK24'):raise ValueError('An explicit registered scout kind is required')
CONFIG='plans/scouts_20261018/'+('SCOUT_CAL12_CARD.json' if KIND=='CAL12' else 'SCOUT_DEV6_BANK24_CARD.json')
METHODS=tuple(plans(KIND))
CPU_STATUS='SCOUT_'+KIND+'_COMPLETE_SAMPLING_CPU_PASS_NOT_GPU'


def matrix(scenes):return rows(KIND,scenes)


def validate_contract(c):
    count=12 if KIND=='CAL12' else 24
    if (c['methods']!=list(METHODS) or c['scope_counts']['total_paths']!=count
            or c['scope_counts']['guided_pairs']!=count*36 or c['scope_counts']['CFG_calls']!=count*72
            or c['scope_counts']['loads']!=1 or c['GPU_submissions']!=0
            or c['GPU_dispatch_ready'] is not False or c['quality_results'] is not None
            or any(r['seed']!=0 or r['num_steps']!=35 or r['guidance']!=7
                or r['num_output_frames']!=93 or r['resolution']!='432,768' for r in c['requests'])
            or len(c['requests'])!=(4 if KIND=='CAL12' else 6)):
        raise ValueError('Complete independent scout blueprint changed')
    if KIND=='CAL12' and c['plans']!={k:list(v) for k,v in plans(KIND).items()}:
        raise ValueError('Frozen G01 and single weighted-variation plan required')
    if not 0<c['budget']['forecast_complete_GPUh']<c['budget']['provisional_billed_limit_GPUh']<12:
        raise ValueError('The original whole scout budget boundary is required')
