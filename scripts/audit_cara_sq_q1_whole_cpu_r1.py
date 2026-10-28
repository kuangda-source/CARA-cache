"""Accept Q1 orchestration/source fixtures, never GPU admission or science."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def accept(capture, profile):
    def require(condition,message):
        if not condition:raise ValueError(message)
    state, result = capture['container_state'],capture['result']
    require(state['Status']=='exited' and not state['Running'] and state['ExitCode']==0
            and not state['OOMKilled'] and not state['Error'],'CPU container is not cleanly terminal')
    require(capture['source_hashes_equal'] and capture['runtime_hashes_equal'],'Source or runtime hashes differ')
    expected = dict(DeviceRequests=None,NanoCpus=2_000_000_000,Memory=8*2**30,
        MemorySwap=8*2**30,CpusetCpus='4,5',NetworkMode='none',ReadonlyRootfs=True)
    require(capture['host_config']==expected,'GPU/network/CPU/memory resource boundary differs')
    require(capture['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d',
            'Registered CPU image differs')
    require(result['status']=='SQ_Q1_WHOLE_ENTRY_CPU_PASS_FIXTURES_NOT_REAL_CUDA'
            and result['profile']==profile,'CPU proof identity differs')
    scope = ROOT/'plans/cara_next_stage_20261028/sq/Q1_WHOLE_SCOPE_R1.json'
    require(result['scope']==json.loads(scope.read_text()),'Complete frozen Q1 scope differs')
    tests = result['fixture_checks']
    require(tests['tests']==20 and tests['errors']==tests['failures']==0 and not tests['real_model'],
            'Affected source/orchestration fixtures incomplete')
    fixture = result['production_entry_fixture']
    require(fixture['complete'] and fixture['states']==12 and fixture['scope_counts']==result['scope']['scope_counts'],
            'Whole fixture denominator differs')
    require(fixture['actual_head_calls']=={k:dict(started=n,completed=n)
            for k,n in (('warm',4),('controls',26),('formal',192))},'Actual extra/formal head calls differ')
    require(not fixture['actual_model_weights'] and fixture['selection_on_complete_fixture_only']
            and result['complete_fixture_selection_cells']==8,'Fixture upgraded to actual model/selection evidence')
    selected = result['selected_experiment_settings']
    require(selected['use_wan_fp32_strategy'] is True and selected['conditional_frame_timestep']==.1,
            'Original selected 2B overrides missing')
    backend = result['original_backend_policy']
    require(backend['original_loader_assignment_verified']
            and backend['flags']['matmul_allow_tf32'] and backend['flags']['cudnn_allow_tf32']
            and backend['flags']['cudnn_benchmark'] and not backend['flags']['cudnn_deterministic'],
            'Original loader backend binding missing')
    for name,digest in {**selected['source_sha256'],**backend['source_sha256']}.items():
        require(hashlib.sha256((ROOT/'cache/runtime'/name).read_bytes()).hexdigest()==digest,
                'Accepted configuration source differs: '+name)
    for key in ('CUDA_initialized','GPU_ready','actual_B1_replay','original_C_CUDA_parity_accepted',
                'GPU_runner_entry_accepted','financial_lifecycle_accepted','GPU_held_collection_selects_directions'):
        require(result[key] is False,'CPU evidence overstated: '+key)
    for key in ('new_GPU_submissions','new_GPUh','ledger_writes'):
        require(result[key]==0 and capture.get(key,0)==0,'CPU evidence carries GPU/budget changes')
    require(result['health_has_no_scores'],'Partial scientific scores leaked into operational health')
    require(result['actual_platform']['system']=='Linux' and result['actual_platform']['machine']=='x86_64'
            and result['torch_version']=='2.7.1+cu128','Registered CPU runtime/platform differs')
    require(result['raw_ru_maxrss_unit']=='KiB' and result['raw_ru_maxrss']==result['peak_RSS_KiB'],
            'Linux resource units differ')
    require(0<result['wall_seconds']<1800 and 0<result['CPU_seconds']<3600
            and 0<result['peak_RSS_KiB']<8*2**20,'CPU resource bounds exceeded')
    return dict(profile=profile,container=capture['launch']['container'],
        source_revision=capture['launch']['source_revision'],result_sha256=capture['result_sha256'],
        fixture_states=12,fixture_head_calls=222,tests=20,CPU_seconds=result['CPU_seconds'],
        worker_wall_seconds=result['wall_seconds'],peak_RSS_GiB=result['peak_RSS_KiB']/2**20,
        orchestration_and_backend_binding_CPU_accepted=True,GPU_ready=False,
        original_C_CUDA_parity_accepted=False,new_GPUh=0)
