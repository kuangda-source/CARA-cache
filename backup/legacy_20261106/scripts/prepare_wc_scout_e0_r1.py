#!/usr/bin/env python3
"""Freeze existing assets and a zero-GPU scout read; never submit GPU work."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'plans/scouts_20261018'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(ref):
    p = ROOT / ref
    return json.loads(gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_bytes())


def bind(ref):
    p = ROOT / ref
    return dict(path=ref, sha256=digest(p), bytes=p.stat().st_size)


def write(path, value):
    assert not path.exists(), str(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def main():
    originals = Path('/Users/kuangda_gao/Documents/worldcache_scouts_20261018')
    archives = []
    for name in ('01_Three_Independent_Exploratory_Experiments.md', '02_Codex_Handoff.md',
                 '03_Exploration_Registry_Template.yaml'):
        target = ROOT / 'plans/reviews/scouts_20261018' / name
        assert not target.exists()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((originals / name).read_bytes())
        archives.append(bind(str(target.relative_to(ROOT))))
    n12ref = 'reports/wc_drop1_full18_terminal_collection_20261018_0001.json.gz'
    n12acc = 'reports/wc_drop1_full18_independent_acceptance_20261018.json'
    n08ref = 'reports/wc_paper_N08_balanced_full40_terminal_collection_user_status_20261017.json.gz'
    n08acc = 'reports/wc_paper_N08_balanced_full40_terminal_independent_acceptance_roundoff_r1_20261017.json'
    warmref = 'reports/wc_drop1_saved_warm21_actual_CPU_independent_acceptance_20261018.json'
    endpointsref = 'reports/wc_drop1_complete_results_analysis_20261018.json'
    windowref = 'reports/wc_drop1_window24_real_N09_quote_and_config_preparation_20261018.json'
    gainref = 'reports/wc_ra_calibration_r1_terminal_20261010_calibration_table_native.gz'
    n12, n08, accepted = load(n12ref), load(n08ref), load(n12acc)
    assert accepted['accepted'] and accepted['capture_sha256'] == digest(ROOT / n12ref)
    assert load(n08acc)['full_raw_and_fidelity_scope_accepted']
    assert load(warmref)['accepted']
    cfg = load('configs/wc_drop1_cal4_three_arm_full18_r1_20261017.json')
    rows = n12['final']['rows']
    sources, masks, bank = {}, {}, []
    for scene in (r['name'] for r in cfg['requests']):
        sources[scene] = {}
        for method in ('S26-C', 'S25-C', 'S25-A'):
            row, = [r for r in rows if r['section'] == 'TIMED' and r['scene'] == scene and r['method'] == method]
            assert row['status'] == 'COMPLETE' and row['semantic_plan'] == cfg['plans'][method]
            plan = row['semantic_plan']
            actualD = [i for i, a in enumerate(row['actions'], 1) if a == 'DD']
            assert actualD == [i for i, a in enumerate(plan, 1) if a == 'D']
            masks[method] = dict(D_mask_36=''.join('1' if a == 'D' else '0' for a in plan),
                                 semantic_plan=plan, D_steps=actualD)
            last, state = 0, []
            for i, action in enumerate(plan, 1):
                if action == 'D': last = i
                history = row['A_history'][i-1]
                assert history['step'] == i and history['readout_action'] == action
                assert not history['C_or_P_observation_updates_D_anchor']
                state.append(dict(step=i, readout=action, actual_CFG_action=row['actions'][i-1],
                                  D_source_step=last, derived_source_age=i-last,
                                  working_source_kind=history['working_source_kind'],
                                  true_D_history=history['past_D_steps'],
                                  current_probe_tensors_saved=False))
            sources[scene][method] = dict(id=row['id'], states=state,
                same_state_teacher_at_all_formal_steps_saved=False)
    for row in load(endpointsref)['scene_rows']:
        d, a = (row['methods'][m] for m in ('S26-C', 'S25-A'))
        assert d['reference_sha256'] == a['reference_sha256'] and d['frames'] == a['frames'] == 93
        bank.append(dict(scene=row['scene'], seed=0, D21=d, A21=a,
                         delta_LPIPS_A_minus_D=a['LPIPS']-d['LPIPS'],
                         delta_core_seconds_A_minus_D=a['core_seconds']-d['core_seconds'],
                         local_probe_z=None, local_probe_z_gap='No step20/21 c/u probe tensors in saved warm format'))
    assets = []
    for r in rows:
        if r['section'] == 'WARMUP' and r['round'] == 1:
            assets.append(dict(role=r['method'], scene=r['scene'], seed=0,
                artifact=r['warm_guided_artifact'], original_id=r['id'],
                source_revision=n12['launch']['source_revision'],
                scheduler_timesteps=r['scheduler_timesteps'], actions=r['actions'],
                same_state_prior_basis='accepted original state restore, seeded request and all20 guided equal',
                direct_pre_action_latent_snapshot_saved=False,
                Phi_equals_saved_A_only_at_alpha1_step21=r['method'] == 'S25-A'))
    native = []
    for r in n08['final']['rows']:
        if r['section'] == 'WARMUP' and r['method'] == 'NATIVE35':
            assert r['status'] == 'COMPLETE' and r['solver_steps'] == 36
            assert r['seed'] == 0 and r['pre_request_state_identity']['original_state_sha256'] == r['pre_request_state_identity']['restored_state_sha256']
            native.append(dict(role='NATIVE35', scene=r['scene'], seed=0, original_id=r['id'],
                artifact=r['warm_guided_artifact'], scheduler_timesteps=r['scheduler_timesteps'],
                source_revision=n08['launch']['source_revision'],
                full_current_state_teacher_for_other_trajectories=False))
    assert len(assets) == 3 and len(native) == 2
    oldstate = {}
    for cap in (n12, n08):
        project = Path('/home/gaokuangda/data/gkd/worldcache_omr')
        stage = Path(cap['launch']['stage'])
        out = project / 'outputs' / cap['launch']['run_id']
        oldstate[str(stage / 'registration.json')] = cap['registration_sha256']
        oldstate[str(out / 'runner.json')] = cap['runner_sha256']
        oldstate[str(out / 'supervisor.json')] = cap['supervisor_sha256']
    gain = load(gainref)
    assert not gain['toy_only_not_Cosmos_calibration'] and gain['guided_weights'] == [8, -7]
    refs = [n12ref,n12acc,n08ref,n08acc,warmref,endpointsref,windowref,gainref,
            'configs/wc_drop1_correction_window_full24_production_r1_20261018.json',
            'reports/wc_w3_grouped_T0_T1_T2_primary_and_raw_sensitivity_accepted_r2_20261016.json']
    manifest = dict(status='EXISTING_CAPTURE_ASSET_INVENTORY_REMOTE_RAW_RELOAD_PENDING',
        input_documents=archives, source_bindings=[bind(p) for p in refs],
        N12_actual_masks=masks, N12_all12_formal_state_records=sources,
        continuation=dict(deleted_D=21,next_actual_D=24,legal_nonD_interval=[22,23],
                          A_does_not_reset_D_anchor=True, calibration_maximum_supported_age=6),
        same_state_assets=assets, native_trajectory_assets=native,
        same_state_independent_inputs=1, same_state_update=21,
        full_endpoint_bank_from_N12=bank,
        warmup_repeats_are_not_independent_inputs=True,
        W3_gaps=dict(label_steps=[10,16,23,25,29,30,32,35],contains_step21=False,
                     local_labels_are_not_complete_D21_A21_suffix_endpoints=True),
        window24=load(windowref),
        factorial_mapping=dict(G00='N12 S25-C / Window24 S25-C',G10='N12 S25-A / Window24 S25-A1',
            G01='MISSING: C21 A22 A23',G11='Window24 S25-A3, production CPU and GPU still pending'),
        new_GPU_submissions=0, new_GPUh=0, original_stages_written=False)
    write(DEST/'SCOUT_E0_ASSET_MANIFEST.json', manifest)
    plan = dict(status='READONLY_SAVED_TENSOR_CPU_DIAGNOSTICS_FROZEN_BEFORE_RAW_RESULTS',
        assets=assets, native_assets=native, original_metadata_sha256=oldstate,
        gains=[gain['gains'][str(i)] for i in range(1,37)], gain_source_binding=bind(gainref),
        gain_semantics='existing transferred coarse empirical latent-suffix amplification prior; not exact sensitivity of either Native trajectory',
        base_mask=cfg['plans']['S26-C'], all3_accepted_round2_repeats_reused_not_reloaded=True,
        alpha_grid=[0,.25,.5,.75,1], edge_gamma=.5, combo_parallel_weight=.25,
        schedule_aggregation='normalize each of two scene score vectors by its mean over steps2..36, then scene-equal mean',
        schedule_selection='one maximum positive legal exchange; tie by remove step then add step; protected1..7,36 age<=6',
        primary_schedule='gain_squared_weighted', secondary_schedule='unweighted_cpu_control_only',
        GPU_submissions=0, model_loads=0, mainline_change_allowed=False)
    write(DEST/'SCOUT_READONLY_CPU_PLAN.json',plan)
    print(json.dumps(dict(status=manifest['status'], files_written=5, N12_formal_paths=12,
        native_trajectories=2,same_state_inputs=1,exact_probe_z_unavailable=True, GPU_submissions=0)))


if __name__ == '__main__': main()
