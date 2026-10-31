"""Endpoint collection and released-artifact handoff, without GPU dispatch."""
import copy
from pathlib import Path
import time

from .cara_budget_search_journal_r1 import create_record,read_record
from .cara_fast_b36_capture_r1 import captured_file
from .cara_fast_spec_r1 import digest
from .cara_s_endpoint_artifacts_r1 import postrelease_manifest,PROPOSAL,ORIGINAL_SCORES
from .cara_s_endpoint_lifecycle_r1 import released_lifecycle
from .cara_s_endpoint_release_r1 import CARD,BINDING
from .cara_s_uniform_endpoint_execution_r1 import execute,inspect_original
from .gpu_budget_pool_v2 import atomic_json,sha
from .policy_price_terminal_r1 import record,require

SOURCE='src/wcomr/cara_s_endpoint_pipeline_r1.py'
COLLECTION='endpoint-collection.json'
RUNNER='endpoint-runner.json'
PRECISION='endpoint-model-precision.json'


def collect(adapter,output,context,*,before_request,precision):
    """The enclosing admitted runner owns the model, device, reset and storage."""
    output=Path(output);card=adapter.card
    require(context['scope_sha256']==card['scope_sha256']
            and context['physical_paths']==len(card['physical_matrix']) in (25,32)
            and context['CPU_fixture_only'] is adapter.cpu_validation
            and context['endpoint_binding_sha256']==card['endpoint_binding_sha256'],
            'Complete original endpoint collection context required')
    require(output.is_dir() and not (output/'B').exists() and not (output/COLLECTION).exists(),
            'Original collection exists; recover only')
    create_record(output/'endpoint-runner-intent.json',dict(context=context,source_sha256=sha(__file__),no_replay=True))
    create_record(output/PRECISION,precision)
    state=dict(scope_sha256=card['scope_sha256'],context_sha256=digest(context),status='COLLECTING',
        started_unix=time.time(),physical_paths=len(card['physical_matrix']),CPU_fixture_only=adapter.cpu_validation,
        collection_sha256=None,GPU_dispatch_allowed=False,scientific_accepted=False)
    atomic_json(output/RUNNER,state)
    try:
        collection=execute(adapter,output/'B',before_request=before_request,
                           save=lambda value:atomic_json(output/COLLECTION,value))
        state.update(status='COMPLETE_COLLECTION_NOT_RELEASED',collection_sha256=digest(collection))
        return collection
    except BaseException as error:
        state.update(status='FAILED_NO_REPLAY',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        state['ended_unix']=time.time();atomic_json(output/RUNNER,state)


def recover_collection(card,output,*,cpu_validation=False):
    output=Path(output);intent=read_record(output/'endpoint-runner-intent.json')
    require(intent['source_sha256']==sha(__file__) and intent['no_replay'] is True
            and intent['context']['scope_sha256']==card['scope_sha256'], 'Original collection intent differs')
    return inspect_original(card,output/COLLECTION,cpu_validation=cpu_validation)


def released_artifacts(lifecycle,expected_launch_sha256,settlement,*,cpu_validation=False,cpu_shape=None):
    """Do not open collection/precision/artifacts until the original release passes."""
    release=released_lifecycle(lifecycle,expected_launch_sha256,settlement,cpu_validation=cpu_validation)
    require(release['container_exit_success'],'Original successful settled release required')
    launch=record(lifecycle,'launch');registration=record(lifecycle,'registration')
    stage=Path(launch['stage']);output=stage.parents[1]/'outputs'/launch['run_id']
    require(registration['payload_sha256'][SOURCE]==sha(__file__),'Original pipeline source differs')
    capture=copy.deepcopy(lifecycle)
    files={'endpoint_card':stage/CARD,'endpoint_binding':stage/BINDING,'endpoint_proposal':stage/PROPOSAL,
           'original_scores':stage/ORIGINAL_SCORES,'precision':output/PRECISION,
           'collection':output/COLLECTION,'runner_terminal':output/RUNNER}
    for key,path in files.items():capture['files'][key]=captured_file(path)
    intent=read_record(output/'endpoint-runner-intent.json');runner=record(capture,'runner_terminal')
    require(intent['source_sha256']==sha(__file__) and intent['context']['launch_id']==launch['launch_id']
            and intent['context']['scope_sha256']==launch['scope_sha256'] and intent['no_replay'] is True
            and runner['status']=='COMPLETE_COLLECTION_NOT_RELEASED'
            and runner['context_sha256']==digest(intent['context']), 'Original complete runner intent differs')
    return postrelease_manifest(capture,expected_launch_sha256,settlement,record(capture,'endpoint_proposal'),
        record(capture,'endpoint_card'),record(capture,'endpoint_binding'),cpu_validation=cpu_validation,cpu_shape=cpu_shape)
