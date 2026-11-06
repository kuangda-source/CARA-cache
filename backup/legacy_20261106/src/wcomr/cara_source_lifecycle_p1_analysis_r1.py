"""Complete P1 input-equal analysis; preserve original FIT choices and costs."""
import copy
import math
from pathlib import Path

from .cara_budget_search_journal_r1 import create_record,read_record
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest
from .cara_source_lifecycle_estimation_r1 import FAMILIES
from .cara_source_lifecycle_p1_artifacts_r1 import validate_manifest

SOURCE='src/wcomr/cara_source_lifecycle_p1_analysis_r1.py'


def complete_analysis(packet,accepted,summary_path,*,cpu_validation=False):
    manifest=packet['manifest'];validate_manifest(manifest,cpu_validation=cpu_validation)
    summary_path=Path(summary_path)
    if (accepted['status']!='P1_COMPLETE52_QUALITY_POSITIONS_ACCEPTED_PENDING_ANALYSIS_FREEZE'
            or accepted['CPU_fixture_only'] is not cpu_validation or accepted['logical_quality_positions']!=52
            or len(accepted['rows'])!=52 or accepted['original_artifact_packet_sha256']!=digest(packet)
            or accepted['internal_scores_recomputed']!=0 or accepted['scope_sha256']!=manifest['scope_sha256']
            or accepted['launch_id']!=manifest['launch_id']
            or file_sha(summary_path)!=manifest['algorithm_summary_sha256']):
        raise ValueError('Complete original52 accepted scores and immutable algorithm summary required')
    summary=read_record(summary_path)
    if (summary.get('failure') is not None or summary['scope_sha256']!=manifest['scope_sha256']
            or summary['status']!='P1_ALGORITHM_COMPLETE_PENDING_ORIGINAL_RELEASE_SETTLEMENT_AND_SCIENCE'
            or summary['CPU_fixture_only'] is not cpu_validation or len(summary['semantic_positions'])!=146
            or summary['original_RGB_MSE_search_reselected'] is not False):
        raise ValueError('Original complete146 algorithm and original RGB-MSE freeze required')
    positions={p['id']:p for p in manifest['quality_positions']}
    if {r['id'] for r in accepted['rows']}!=set(positions):
        raise ValueError('Every original role/input position is required exactly once')
    rows=[]
    for row in accepted['rows']:
        position=positions[row['id']]
        if any(row[k]!=v for k,v in position.items()):
            raise ValueError('Accepted quality role, original artifact or clean clocks changed')
        metric=row['metrics']
        if (len(metric['Alex_frames'])!=93 or len(metric['SSIM_frames'])!=93
                or metric['Alex']!=sum(metric['Alex_frames'])/93
                or metric['SSIM']!=sum(metric['SSIM_frames'])/93):
            raise ValueError('Original complete93-frame metric reductions required')
        role=position['role']
        if role.startswith('V1-'):
            key=role.removeprefix('V1-')
            if position['candidate']['candidate_id']!=summary['FIT_selected'][key]['policy']['fingerprint']:
                raise ValueError('Once-selected complete FIT plan cannot be reselected from CHECK')
        if role.startswith('LPIPS_SEARCH-'):
            budget=role.removeprefix('LPIPS_SEARCH-K')
            if position['candidate']['candidate_id']!=summary['fair_searches'][budget]['best_complete_candidate']['policy_fingerprint']:
                raise ValueError('Original complete LPIPS-search winner changed')
        rows.append(copy.deepcopy(row))
    roles=list(dict.fromkeys(p['role'] for p in manifest['quality_positions']))
    groups={name:members for name,members in (('FIT',manifest['FIT']),('EXPOSED_CHECK',manifest['CHECK']),
                                             ('FOUR_OLD_CAL',manifest['FIT']+manifest['CHECK']))}
    tables={}
    for group,members in groups.items():
        table={}
        for role in roles:
            selected=[r for r in rows if r['role']==role and r['member'] in members]
            if len(selected)!=len(members) or {r['member'] for r in selected}!=set(members):
                raise ValueError('Complete input-equal group denominator required')
            mean=lambda key:math.fsum(r['metrics'][key] for r in selected)/len(selected)
            table[role]=dict(inputs=len(selected),members=members,LPIPS=mean('Alex'),SSIM=mean('SSIM'),
                MSE_video=mean('MSE_video'),T_DD=math.fsum(r['T_DD'] for r in selected)/len(selected),
                T_request=math.fsum(r['T_request'] for r in selected)/len(selected),
                LPIPS_curve=[math.fsum(r['metrics']['Alex_frames'][i] for r in selected)/len(selected) for i in range(93)],
                SSIM_curve=[math.fsum(r['metrics']['SSIM_frames'][i] for r in selected)/len(selected) for i in range(93)],
                infinite_PSNR_inputs=[r['member'] for r in selected if r['metrics']['PSNR_is_infinite']],
                undefined_gradient_inputs=[r['member'] for r in selected if r['metrics']['gradient_energy_ratio'] is None],
                independent_clean_samples=sum(r['independent_clean_sample'] for r in selected),
                quality_aliases=sum(not r['independent_clean_sample'] for r in selected))
        tables[group]=table
    budgets={}
    for k in (19,22):
        search=summary['fair_searches'][str(k)]
        parts=search['cap_components_seconds']
        expected=math.fsum(parts[n] for n in ('half_shared_calibration','half_main_estimation','main_complete_FIT_selection'))
        if (not math.isclose(expected,search['measured_cost_cap_seconds'],rel_tol=0,abs_tol=1e-8)
                or not 0<=search['measured_charged_seconds']<=search['measured_cost_cap_seconds']
                or (not search['configured_search_finished'] and search['HC_iterations_completed']>=1)):
            raise ValueError('Original equal actual-calibration cost cap or unfinished search denominator changed')
        budgets[str(k)]=dict(cap_components_seconds=copy.deepcopy(parts),
            main_V1_shared_calibration_and_complete_FIT_cap_seconds=expected,
            search_measured_charged_seconds=search['measured_charged_seconds'],
            search_termination=search['termination'],configured_search_finished=search['configured_search_finished'],
            requested_queries=search['requested_queries'],completed_queries=search['completed_queries'],
            HC_iterations_completed=search['HC_iterations_completed'],
            original_once_selected_V1={f:copy.deepcopy(summary['FIT_selected'][f+'-K'+str(k)]) for f in FAMILIES},
            original_once_selected_search=copy.deepcopy(search['best_complete_candidate']))
    comparisons={}
    for group,table in tables.items():
        comparisons[group]={}
        for k in (19,22):
            main=table[f'V1-{FAMILIES[-1]}-K{k}'];uniform=table[f'UNIFORM{k}_C'];single=table[f'V1-{FAMILIES[1]}-K{k}']
            comparisons[group][str(k)]=dict(
                main_LPIPS_reduction_vs_Uniform=1-main['LPIPS']/uniform['LPIPS'] if uniform['LPIPS'] else None,
                previous_gap_LPIPS_reduction_vs_stage_age=1-main['LPIPS']/single['LPIPS'] if single['LPIPS'] else None,
                Uniform_mean_LPIPS_zero=uniform['LPIPS']==0,stage_age_mean_LPIPS_zero=single['LPIPS']==0,
                main_T_DD_ratio_vs_Uniform=main['T_DD']/uniform['T_DD'])
    table=tables['FOUR_OLD_CAL'];main=table[f'V1-{FAMILIES[-1]}-K19'];f19=table['F19_A1']
    screen=dict(scope='FOUR_OLD_CAL_ENGINEERING_CONTINUATION_ONLY',LPIPS_ratio_vs_F19_A1=(main['LPIPS']/f19['LPIPS'] if f19['LPIPS'] else None),
        T_DD_ratio_vs_F19_A1=main['T_DD']/f19['T_DD'],max_LPIPS_ratio=1.10,max_T_DD_ratio=1.05,
        passes=(main['LPIPS']<=1.10*f19['LPIPS'] and main['T_DD']<=1.05*f19['T_DD']),
        selects_a_different_plan=False,paper_validity_threshold=False)
    return dict(status='P1_COMPLETE_INPUT_EQUAL_ANALYSIS_PENDING_ONCE_FREEZE',CPU_fixture_only=cpu_validation,
        run_id=manifest['run_id'],launch_id=manifest['launch_id'],scope_sha256=manifest['scope_sha256'],
        artifact_packet_sha256=digest(packet),accepted_scores_sha256=digest(accepted),
        algorithm_summary_sha256=manifest['algorithm_summary_sha256'],analysis_source_sha256=file_sha(__file__),
        logical_quality_positions=52,semantic_denominator=146,input_count=4,rows=rows,tables=tables,
        comparisons=comparisons,calibration_costs_and_original_plans=budgets,engineering_screen=screen,
        original_guardian_GPUh=packet['release']['actual_GPUh'],
        original_internal_metric_pairs_recomputed=0,old_RGB_MSE_winner_reselected=False,
        CHECK_is_exposed_development=True,independent_new_inputs=False,scientific_method_established=False,
        GPU_submissions=0,ledger_written=False)


def freeze_original_plans(analysis,path,*,cpu_validation=False):
    """Publish original FIT choices once; never choose a winner using CHECK."""
    if (analysis['status']!='P1_COMPLETE_INPUT_EQUAL_ANALYSIS_PENDING_ONCE_FREEZE'
            or analysis['CPU_fixture_only'] is not cpu_validation or analysis['logical_quality_positions']!=52
            or analysis['semantic_denominator']!=146 or analysis['analysis_source_sha256']!=file_sha(__file__)):
        raise ValueError('Complete original P1 analysis required before once freeze')
    if not cpu_validation and not str(Path(path).name).startswith('V1_P1_FROZEN_ORIGINAL_FIT_PLANS_'):
        raise ValueError('A new P1-specific freeze is required; old freezes cannot be overwritten')
    value=dict(schema='CARA_V1_P1_ORIGINAL_FIT_PLANS_ONCE_FREEZE_R1',CPU_fixture_only=cpu_validation,
        run_id=analysis['run_id'],launch_id=analysis['launch_id'],scope_sha256=analysis['scope_sha256'],
        analysis_sha256=digest(analysis),analysis_source_sha256=analysis['analysis_source_sha256'],
        original_FIT_plans_and_costs=copy.deepcopy(analysis['calibration_costs_and_original_plans']),
        selection_was_complete_FIT_before_CHECK=True,CHECK_used_to_reselect=False,
        old_freezes_overwritten=False,GPU_submissions=0,ledger_written=False)
    path=Path(path)
    if path.exists():
        if read_record(path)!=value:raise ValueError('Existing P1 freeze differs; preserve the original bytes')
    else:create_record(path,value)
    return value
