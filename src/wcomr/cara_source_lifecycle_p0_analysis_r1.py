"""Complete two-position P0 mechanism reduction; no metric or GPU execution."""
from .cara_fast_spec_r1 import digest
from .cara_read_write_analysis_r1 import analyze
from .cara_read_write_artifacts_r1 import validate_manifest
from .cara_read_write_identity_r1 import for_card, M1, P0
from .policy_price_terminal_r1 import require


def combine(point8_card, point8_scores, point20_card, point20_scores, point20_packet, *, cpu_validation=False):
    require(for_card(point8_card)==M1 and for_card(point20_card)==P0,
            'Both preregistered original point8 and distinct point20 scopes required')
    require(all(point8_card[k]==point20_card[k] for k in
        ('profile','schedule','FIT','CHECK','inputs','settings'))
        and point8_card['roles']['UNIFORM19_C']==point20_card['roles']['UNIFORM19_C'],
        'Same original two-FIT parent, sampler, grid and inputs required across points')
    manifest = point20_packet['manifest']
    validate_manifest(manifest)
    require(point20_packet['CPU_fixture_only'] is cpu_validation
        and manifest['scope_sha256']==point20_card['scope_sha256']
        and point20_scores['artifact_packet_sha256']==digest(point20_packet)
        and point20_packet['release']['GPU_released'] and point20_packet['release']['cost_settled'],
        'Complete released point20 packet, bridges and accepted scores required')
    summaries = [analyze(c,s,cpu_validation=cpu_validation)
                 for c,s in ((point8_card,point8_scores),(point20_card,point20_scores))]
    rows = [dict(target_update=p['target_update'], **m,
        direct_source_consumption=(manifest['source_consumption'][m['member']]
                                   if p['target_update']==20 else None))
        for p in summaries for m in p['members']]
    return dict(schema='CARA_P0_TWO_POSITION_COMPLETE_MECHANISM_R1',
        status='COMPLETE16_SCIENTIFIC_POSITIONS_WITH_ORIGINAL_POINT8_REUSED',
        CPU_fixture_only=cpu_validation, old_FIT_members=point20_card['FIT'],
        target_updates=[8,20], complete_scientific_positions=16,
        new_scoring_pairs=8, reused_original_scoring_rows=8, original_point8_new_scoring=0,
        original_point8_GPU_replayed=False, point_summaries=summaries, four_input_states=rows,
        write_value_sign_counts={k:dict(positive=sum(m['Alex_write_values'][k]>0 for m in rows),
            zero=sum(m['Alex_write_values'][k]==0 for m in rows),
            negative=sum(m['Alex_write_values'][k]<0 for m in rows),denominator=4) for k in ('W_C','W_D')},
        point8_scores_sha256=digest(point8_scores), point20_scores_sha256=digest(point20_scores),
        point20_packet_sha256=digest(point20_packet),
        source_consumption_scope='direct residual sources; full working-state causal influence is not identified by metadata',
        scientific_scope='Two old FIT, seed0, same Uniform19 parent, two action-structure-selected intervention positions',
        mechanical_quality_threshold=None, automatic_P1_launch_authorized=False,
        source_lifecycle_planner_established=False, independent_generalization=False,
        equal_latency_deployment_claim=False, GPU_submissions=0, ledger_written=False)
