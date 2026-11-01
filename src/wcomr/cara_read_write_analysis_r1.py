"""Complete M1 read/write contrasts under the preregistered loss convention."""
import math

from .cara_fast_spec_r1 import digest
from .cara_read_write_artifacts_r1 import READ_ROLES
from .cara_read_write_plan_r1 import validate
from .policy_price_terminal_r1 import require


def analyze(card, accepted, *, cpu_validation=False):
    validate(card)
    rows = accepted['rows']
    require(accepted['status'] == 'ACCEPTED_COMPLETE8_READ_WRITE_SCORES'
        and accepted['CPU_fixture_only'] is cpu_validation
        and accepted['scope_sha256'] == card['scope_sha256']
        and accepted['new_scored_pairs'] == 8 and accepted['reused_original_rows'] == 0
        and len(rows) == 8 and {(r['member'], r['role']) for r in rows}
            == {(m, role) for m in card['FIT'] for role in READ_ROLES},
        'Complete accepted original eight-pair M1 result required')

    def contrasts(losses):
        l00, l10, l01, l11 = (losses[role] for role in READ_ROLES)
        return dict(read=l10-l00, write=l01-l00, interaction=l11-l10-l01+l00, joint=l11-l00)

    members = []
    for member in card['FIT']:
        chosen = {r['role']:r for r in rows if r['member'] == member}
        for role, row in chosen.items():
            require(row['status'] == 'COMPLETE' and row['frames'] == 93 and row['temporal_frame_pairs'] == 92
                and row['PTS_equal'] is True
                and row['candidate']['member'] == row['reference']['member'] == member
                and row['candidate']['role'] == role and row['reference']['role'] == 'NATIVE35'
                and row['candidate']['scope_sha256'] == row['reference']['scope_sha256'] == card['scope_sha256']
                and len(row['Alex_frames']) == 93 and all(math.isfinite(x) for x in row['Alex_frames'])
                and row['Alex'] == sum(row['Alex_frames'])/93,
                'Original complete per-input reference/curve identity differs')
        references = [row['reference'] for row in chosen.values()]
        require(all(r == references[0] for r in references), 'Four corners must share the same fresh Native reference')
        effects = contrasts({r:chosen[r]['Alex'] for r in READ_ROLES})
        curves = [contrasts({r:chosen[r]['Alex_frames'][i] for r in READ_ROLES}) for i in range(93)]
        secondary = {name:contrasts({r:(1-chosen[r]['SSIM'] if name == 'one_minus_SSIM' else chosen[r][name])
            for r in READ_ROLES}) for name in ('MSE_video', 'one_minus_SSIM', 'reference_temporal_L1', 'reference_gradient_L1')}
        members.append(dict(member=member, losses_Alex={r:chosen[r]['Alex'] for r in READ_ROLES},
            Alex_effects=effects, Alex_frame_effects=curves, secondary_error_effects=secondary))
    means = {name:sum(m['Alex_effects'][name] for m in members)/2 for name in members[0]['Alex_effects']}
    mean_curves = [{name:sum(m['Alex_frame_effects'][i][name] for m in members)/2 for name in means} for i in range(93)]
    return dict(schema='CARA_M1_COMPLETE_READ_WRITE_ANALYSIS_R1', status='COMPLETE_TWO_OLD_FIT_M1_CONTRASTS',
        scope_sha256=card['scope_sha256'], accepted_scores_sha256=digest(accepted), CPU_fixture_only=cpu_validation,
        old_FIT_members=card['FIT'], seed=0, target_update=8, scientific_pairs=8, physical_paths=14,
        physical_model_pairs=512, members=members, equal_input_mean_Alex_effects=means,
        equal_input_mean_Alex_frame_effects=mean_curves, negative_effect_means_lower_reference_error=True,
        interpretation='Paid same-parent intervention at one fixed update under the frozen future policy',
        independent_new_inputs=False, deployment_speed_claim=False, method_established=False,
        automatic_next_GPU_authorized=False, GPU_submissions=0, ledger_written=False)
