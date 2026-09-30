"""Paired complete-frame MUSIQ descriptors; no overall/physical quality gate."""
import math
import numpy as np
import torch
import torch.nn.functional as F


def prepare_frame(rgb):
    if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[-1] != 3:
        raise ValueError('Expected uint8 HWC RGB')
    h, w, _ = rgb.shape
    image = torch.from_numpy(np.ascontiguousarray(rgb)).permute(2, 0, 1).unsqueeze(0).float()
    if max(h, w) > 512:
        scale = 512.0 / max(h, w)
        image = F.interpolate(image, size=(int(scale*h), int(scale*w)), mode='bilinear', align_corners=False, antialias=False)
    return image / 255.0


def score_complete_frames(frames, model, device, expected_frames=93, expected_shape=(432, 768, 3)):
    scores = []
    pts = []
    for rgb, timestamp, time_base in frames:
        if tuple(rgb.shape) != tuple(expected_shape):
            raise ValueError('Video RGB geometry differs')
        with torch.inference_mode():
            output = model(prepare_frame(rgb).to(device))
        if output.numel() != 1 or not torch.isfinite(output).all():
            raise ValueError('Nonfinite or non-scalar MUSIQ output')
        scores.append(float(output.item()))
        pts.append([timestamp, str(time_base)])
    if len(scores) != expected_frames:
        raise ValueError('Incomplete video frames')
    return {'frames': len(scores), 'pts': pts, 'frame_scores': scores,
            'mean_raw_score': sum(scores)/len(scores), 'normalized_score': sum(scores)/len(scores)/100.0}


def paired_summary(rows, planned_names):
    if [row['name'] for row in rows] != list(planned_names):
        raise ValueError('Incomplete or reordered paired evaluation')
    differences = []
    for row in rows:
        if row['status'] == 'SCORED':
            reference, candidate = row['reference'], row['candidate']
            if reference['frames'] != candidate['frames'] or reference['pts'] != candidate['pts']:
                raise ValueError('Paired frame count/PTS differs')
            values = [reference['normalized_score'], candidate['normalized_score']]
            if not all(math.isfinite(x) for x in values):
                raise ValueError('Nonfinite paired score')
            differences.append(values[1]-values[0])
        elif row['status'] not in ['TEXT_REJECTED', 'VIDEO_REJECTED']:
            raise ValueError('Unverified evaluation row')
    return {'planned': len(rows), 'scored_pairs': len(differences), 'rejected_candidates': len(rows)-len(differences),
            'candidate_higher': sum(x > 0 for x in differences), 'candidate_lower': sum(x < 0 for x in differences),
            'equal_sample_mean_delta': sum(differences)/len(differences) if differences else None,
            'status': 'IMAGING_DIMENSION_COMPLETE_OVERALL_QUALITY_UNASSESSED',
            'scope': 'One MUSIQ imaging dimension on reusable CAL, equal scene weighting. Frames are dependent; no semantic/physical score, significance, noninferiority or clean speed conclusion.'}
