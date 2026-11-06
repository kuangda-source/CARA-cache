"""Production complete52 analysis and one immutable original-FIT freeze."""
import copy
import fcntl
from pathlib import Path

from . import cara_source_lifecycle_p1_score_dispatch_r1 as scores
from .cara_budget_search_journal_r1 import create_record, read_record
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest
from .cara_source_lifecycle_p1_analysis_r1 import complete_analysis, freeze_original_plans
from .cara_source_lifecycle_p1_identity_r1 import RUN_ID
from .policy_price_terminal_r1 import require

ROOT = Path(__file__).resolve().parents[2]
SOURCE = 'src/wcomr/cara_source_lifecycle_p1_report_r1.py'
CLI = 'scripts/analyze_cara_source_lifecycle_p1_complete_r1.py'
SOURCES = (SOURCE, CLI, 'src/wcomr/cara_source_lifecycle_p1_analysis_r1.py')


def write_original(path, value):
    if path.exists():
        require(read_record(path) == value, 'Existing original P1 report differs; preserve its bytes')
    else:
        create_record(path, value)


def stable_scores(accepted):
    value = copy.deepcopy(accepted)
    value.pop('execution_sha256')
    return value


def stable_execution(execution):
    value = copy.deepcopy(execution)
    # Fresh original-process observations have a new observation time (and may
    # later record PID reuse). recover() still verifies exit against the same
    # original PID/start ticks. All identity, result, source and container fields
    # below stay exact; only these two freshly validated observations vary.
    value.pop('original_observation')
    value.pop('cli_observation')
    return value


def complete(stage, *, cpu_validation=False, fixture_summary=None):
    stage = Path(stage)
    require(cpu_validation or fixture_summary is None, 'Only explicit CPU fixtures may select a fixture summary')
    intent, packet, config = scores.read_intent(stage)
    require(intent['CPU_fixture_only'] is cpu_validation and config['CPU_fixture_only'] is cpu_validation,
            'CPU fixture evidence cannot form a production P1 report')
    reg = read_record(stage/'registration.json')
    source = {n:file_sha(ROOT/n) for n in SOURCES}
    require(all(reg['payload_sha256'].get(n) == h == file_sha(stage/n) for n,h in source.items()),
            'Original registered production analysis source differs')
    recovered = scores.recover(stage)
    require(recovered['status'] == 'ORIGINAL_COMPLETE52_P1_SCORE_ACCEPTED',
            'Complete original post-score supervisor, CLI, container and worker must have ended')
    capture = recovered['score_capture']
    accepted, execution = capture['accepted'], capture['execution']
    require(accepted['execution_sha256'] == digest(execution), 'Original complete score execution binding differs')
    _, out = scores.paths(stage, config)
    summary = (Path(fixture_summary) if cpu_validation and fixture_summary is not None
               else stage.parents[1]/'outputs'/RUN_ID/'algorithm/algorithm-summary.json')
    require(summary.is_absolute() and file_sha(summary) == packet['manifest']['algorithm_summary_sha256'],
            'Original immutable complete algorithm summary required')
    binding = dict(CPU_fixture_only=cpu_validation, stage=str(stage), run_id=intent['run_id'],
        launch_id=intent['launch_id'], scope_sha256=intent['scope_sha256'],
        score_intent_sha256=file_sha(stage/'post-score-control/intent.json'),
        config_sha256=digest(config), packet_sha256=digest(packet),
        algorithm_summary_path=str(summary), algorithm_summary_sha256=file_sha(summary), source_sha256=source)
    directory = out/'complete-analysis'
    directory.mkdir(exist_ok=True)
    with (directory/'analysis.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        seal_path = directory/'original-analysis-input.json'
        if seal_path.exists():
            seal = read_record(seal_path)
            require(seal['binding'] == binding
                and seal['accepted']['execution_sha256'] == digest(seal['execution'])
                and stable_scores(seal['accepted']) == stable_scores(accepted)
                and stable_execution(seal['execution']) == stable_execution(execution),
                'Original sealed complete P1 scores or source differ; no reselection or overwrite')
        else:
            seal = dict(schema='CARA_V1_P1_ORIGINAL_ANALYSIS_INPUT_R1', binding=binding,
                        accepted=accepted, execution=execution)
            create_record(seal_path, seal)
        analysis = complete_analysis(packet, seal['accepted'], summary, cpu_validation=cpu_validation)
        analysis_path = directory/'complete-analysis.json'
        write_original(analysis_path, analysis)
        freeze_path = directory/('V1_P1_FROZEN_ORIGINAL_FIT_PLANS_'+intent['launch_id']+'.json')
        freeze_original_plans(analysis, freeze_path, cpu_validation=cpu_validation)
        result = dict(status='P1_COMPLETE52_ANALYSIS_AND_ORIGINAL_FIT_FREEZE_ACCEPTED',
            CPU_fixture_only=cpu_validation, binding=binding, logical_quality_positions=52,
            input_seal_path=str(seal_path), input_seal_sha256=file_sha(seal_path),
            analysis_path=str(analysis_path), analysis_sha256=file_sha(analysis_path),
            freeze_path=str(freeze_path), freeze_sha256=file_sha(freeze_path),
            original_metric_pairs_recomputed=0, original_FIT_plans_reselected=False,
            CHECK_is_exposed_development=True, independent_new_inputs=False,
            scientific_method_established=False, GPU_submissions=0, ledger_written=False)
        write_original(directory/'report.json', result)
        return result
