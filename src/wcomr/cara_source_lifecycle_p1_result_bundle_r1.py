"""Portable original-complete P1 reporting, without model/metric dependencies."""
import base64
from pathlib import Path

from . import cara_source_lifecycle_p1_report_r1 as report
from . import cara_source_lifecycle_p1_figures_r1 as figures
from .cara_budget_search_journal_r1 import create_record, read_record
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest
from .cara_source_lifecycle_p1_identity_r1 import RUN_ID, SCOPE_SHA256
from .policy_price_terminal_r1 import require

SOURCE='src/wcomr/cara_source_lifecycle_p1_result_bundle_r1.py'
CLI='scripts/cara_source_lifecycle_p1_result_bundle_r1.py'
SOURCES=tuple(dict.fromkeys((*report.SOURCES,figures.SOURCE,figures.CLI,SOURCE,CLI)))
SCHEMA='CARA_V1_P1_ORIGINAL_COMPLETE_RESULT_BUNDLE_R1'


def export(stage,*,cpu_validation=False,fixture_summary=None):
    """The original complete-score gate runs before opening scientific output."""
    stage=Path(stage);registration=read_record(stage/'registration.json')
    source={n:file_sha(report.ROOT/n) for n in SOURCES}
    require(all(registration['payload_sha256'].get(n)==h==file_sha(stage/n) for n,h in source.items()),
            'Original registered P1 result-export and figure sources required')
    accepted=report.complete(stage,cpu_validation=cpu_validation,fixture_summary=fixture_summary)
    directory=Path(accepted['analysis_path']).parent
    paths=dict(report=directory/'report.json',analysis=Path(accepted['analysis_path']),freeze=Path(accepted['freeze_path']))
    files={name:dict(original_path=str(path),raw_base64=base64.b64encode(path.read_bytes()).decode(),
                    sha256=file_sha(path)) for name,path in paths.items()}
    value=dict(schema=SCHEMA,CPU_fixture_only=cpu_validation,run_id=accepted['binding']['run_id'],
        launch_id=accepted['binding']['launch_id'],scope_sha256=accepted['binding']['scope_sha256'],
        source_sha256=source,files=files,logical_quality_positions=52,semantic_denominator=146,
        original_metric_pairs_recomputed=0,original_FIT_plans_reselected=False,
        original_GPU_stage_changed=False,GPU_submissions=0,ledger_written=False)
    output=directory/'original-complete-result-bundle.json'
    report.write_original(output,value)
    return dict(status='P1_ORIGINAL_COMPLETE_RESULT_BUNDLE_EXPORTED',CPU_fixture_only=cpu_validation,
        run_id=value['run_id'],launch_id=value['launch_id'],scope_sha256=value['scope_sha256'],
        bundle_path=str(output),bundle_sha256=file_sha(output),bytes=output.stat().st_size,
        original_metric_pairs_recomputed=0,GPU_submissions=0,ledger_written=False)


def load(path,expected_sha256,*,cpu_validation=False):
    """The expected hash comes from the original export receipt, not this file."""
    import hashlib
    import json
    path=Path(path)
    require(file_sha(path)==expected_sha256,'Original export-receipt bundle SHA required')
    value=read_record(path)
    source={n:file_sha(report.ROOT/n) for n in SOURCES}
    require(value['schema']==SCHEMA and value['CPU_fixture_only'] is cpu_validation
        and value['run_id']==RUN_ID and value['scope_sha256']==SCOPE_SHA256
        and value['logical_quality_positions']==52 and value['semantic_denominator']==146
        and value['source_sha256']==source and set(value['files'])=={'report','analysis','freeze'}
        and value['original_metric_pairs_recomputed']==0 and value['original_FIT_plans_reselected'] is False,
        'Original complete P1 source/scope required; CPU evidence cannot form production figures')
    objects={}
    for name,row in value['files'].items():
        raw=base64.b64decode(row['raw_base64'],validate=True)
        require(hashlib.sha256(raw).hexdigest()==row['sha256'],'Original complete result file SHA differs')
        objects[name]=json.loads(raw)
    accepted,analysis,freeze=(objects[n] for n in ('report','analysis','freeze'))
    binding=accepted['binding']
    require(accepted['status']=='P1_COMPLETE52_ANALYSIS_AND_ORIGINAL_FIT_FREEZE_ACCEPTED'
        and accepted['CPU_fixture_only'] is cpu_validation
        and accepted['logical_quality_positions']==52
        and accepted['analysis_sha256']==value['files']['analysis']['sha256']
        and accepted['freeze_sha256']==value['files']['freeze']['sha256']
        and accepted['original_metric_pairs_recomputed']==0 and accepted['original_FIT_plans_reselected'] is False
        and binding['source_sha256']=={n:source[n] for n in report.SOURCES}
        and all(binding[k]==value[k]==analysis[k]==freeze[k] for k in ('run_id','launch_id','scope_sha256')),
        'Original complete host report, analysis and FIT-freeze identities differ')
    require(analysis['status']=='P1_COMPLETE_INPUT_EQUAL_ANALYSIS_PENDING_ONCE_FREEZE'
        and analysis['CPU_fixture_only'] is freeze['CPU_fixture_only'] is cpu_validation
        and analysis['logical_quality_positions']==52 and len(analysis['rows'])==52
        and analysis['semantic_denominator']==146
        and analysis['analysis_source_sha256']==source['src/wcomr/cara_source_lifecycle_p1_analysis_r1.py']
        and freeze['schema']=='CARA_V1_P1_ORIGINAL_FIT_PLANS_ONCE_FREEZE_R1'
        and freeze['analysis_sha256']==digest(analysis)
        and freeze['analysis_source_sha256']==analysis['analysis_source_sha256']
        and freeze['original_FIT_plans_and_costs']==analysis['calibration_costs_and_original_plans']
        and freeze['selection_was_complete_FIT_before_CHECK'] is True and freeze['CHECK_used_to_reselect'] is False,
        'Original complete analysis or once-selected FIT plans differ')
    return value,analysis


def render(path,expected_sha256,directory,*,cpu_validation=False):
    value,analysis=load(path,expected_sha256,cpu_validation=cpu_validation)
    directory=Path(directory);receipt=directory/'figure-report.json'
    binding=dict(bundle_sha256=expected_sha256,source_sha256=value['source_sha256'],CPU_fixture_only=cpu_validation)
    if receipt.exists():
        original=read_record(receipt)
        require(original['binding']==binding and all(file_sha(directory/n)==h for n,h in original['files_sha256'].items()),
                'Original portable figures differ; preserve the original export')
        return original
    directory.mkdir(parents=True,exist_ok=True)
    require(not any(directory.iterdir()),'Partial original portable figure directory requires inspection')
    figures.export_tables(analysis,directory);figures.plots(analysis,directory)
    result=dict(status='P1_COMPLETE_ORIGINAL_BUNDLE_FIGURES_EXPORTED',binding=binding,directory=str(directory),
        files_sha256={p.name:file_sha(p) for p in sorted(directory.iterdir())},logical_quality_positions=52,
        input_equal_mean_rows=39,frame_curve_rows=3627,all93_frames=True,both_original_clocks=True,
        original_metric_pairs_recomputed=0,original_FIT_plans_reselected=False,remote_handle_recovered=False,
        CHECK_is_exposed_development=True,GPU_submissions=0,ledger_written=False)
    create_record(receipt,result)
    return result
