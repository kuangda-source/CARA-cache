"""Predeclared four-cell fixed-reference contrasts; no model or training."""
import math
from fractions import Fraction

CELLS = ('BASE', 'CFG0', 'CFG1', 'PAIRED')
PAIRS = (('BASE', 'CFG0'), ('BASE', 'CFG1'), ('CFG0', 'PAIRED'), ('BASE', 'PAIRED'))


def factorial_summary(losses, counts, costs):
    if set(losses) != set(CELLS) or set(counts) != set(CELLS) or set(costs) != set(CELLS):
        raise ValueError('All four current-card cells and costs required')
    common = None
    for name in CELLS:
        loss = losses[name]
        distances = loss['frame_distances']
        pts = loss['pts']
        digest = loss['reference_sha256']
        if (type(digest) is not str or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest)
                or len(pts) != 93 or any(type(p) is not list or len(p) != 2 or type(p[0]) is not int
                    or p[0] < 0 or type(p[1]) is not str for p in pts)):
            raise ValueError('Actual full93 reference identity/PTS pairs required')
        identity = (digest, tuple(tuple(p) for p in pts))
        if (loss['frames'] != 93 or len(distances) != 93 or len(set(identity[1])) != 93
                or any(p[1] != pts[0][1] for p in pts) or Fraction(pts[0][1]) <= 0
                or any((b[0] - a[0]) * Fraction(a[1]) != Fraction(1, 16) for a, b in zip(pts, pts[1:]))
                or any(type(x) not in (float, int) or not math.isfinite(x) or x < 0 for x in distances)
                or not math.isclose(loss['mean_LPIPS'], math.fsum(distances) / 93, abs_tol=1e-12, rel_tol=0)
                or (common is not None and common != identity)):
            raise ValueError('Same fixed reference/PTS and full93 arithmetic required')
        common = identity
        if len(costs[name]) != 2 or any(not math.isfinite(x) or x <= 0 for x in costs[name]):
            raise ValueError('Both complete control costs required')
        if set(counts[name]) != {'prefix_CFG', 'current_CFG', 'future_CFG', 'whole_CFG'}:
            raise ValueError('Current, strict future and whole per-CFG accounting required')
        for key, values in counts[name].items():
            if len(values) != 2 or any(type(x) is not int or x < 0 for x in values):
                raise ValueError('Finite nonnegative integer per-CFG work required')
        if any(counts[name]['prefix_CFG'][i] + counts[name]['current_CFG'][i]
               + counts[name]['future_CFG'][i] != counts[name]['whole_CFG'][i] for i in (0, 1)):
            raise ValueError('Work accounting does not add up')
        if any(x > 1 for x in counts[name]['current_CFG']):
            raise ValueError('Current step has only one call per CFG slot')
    if any(counts[name]['prefix_CFG'] != counts['BASE']['prefix_CFG'] for name in CELLS):
        raise ValueError('Shared parent prefix accounting differs')
    contrasts = []
    for reference, candidate in PAIRS:
        frame = [a - b for a, b in zip(losses[reference]['frame_distances'], losses[candidate]['frame_distances'])]
        signed = math.fsum(frame) / 93
        denominator = losses[reference]['mean_LPIPS']
        contrasts.append({
            'comparison': candidate + '_vs_' + reference,
            'signed_quality': signed,
            'relative_fidelity_improvement_percent': 100 * signed / denominator if denominator else None,
            'frame_signed_changes': frame,
            'improved_frames': sum(x > 0 for x in frame),
            'worse_frames': sum(x < 0 for x in frame),
            'tied_frames': sum(x == 0 for x in frame),
            'three_equal31_frame_mean_changes': [math.fsum(frame[i:i+31]) / 31 for i in (0, 31, 62)],
            'current_full_added': sum(counts[candidate]['current_CFG']) - sum(counts[reference]['current_CFG']),
            'strict_future_full_saved': sum(counts[reference]['future_CFG']) - sum(counts[candidate]['future_CFG']),
            'whole_full_saved': sum(counts[reference]['whole_CFG']) - sum(counts[candidate]['whole_CFG']),
            'signed_diagnostic_seconds': math.fsum(costs[reference]) / 2 - math.fsum(costs[candidate]) / 2,
        })
    frames = [a + b - c - d for a, b, c, d in zip(
        losses['CFG0']['frame_distances'], losses['CFG1']['frame_distances'],
        losses['BASE']['frame_distances'], losses['PAIRED']['frame_distances'])]
    return {'status': 'FULL93_FOUR_CELL_TOTAL_ADAPTIVE_EFFECTS_NOT_CONF_NOT_RV_LABEL',
            'contrasts': contrasts,
            'interaction': {'signed_quality': math.fsum(frames) / 93,
                'frame_signed_interactions': frames,
                'definition': 'L_CFG0+L_CFG1-L_BASE-L_PAIRED',
                'interpretation': 'Total current-request interaction through native adaptive continuation; no unique mechanism attribution'},
            'actual_counts': counts, 'control_costs': costs,
            'independent_CONF': False, 'clean_speed_measurement': False, 'formal_single_action_RV_labels': False}
