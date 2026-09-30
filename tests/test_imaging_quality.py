import copy
import numpy as np
import pytest
import torch
from wcomr.imaging_quality import prepare_frame,score_complete_frames,paired_summary


def test_complete_frame_average_scale_and_invalid_frame_gate():
    frames=[(np.full((2,3,3),v,dtype=np.uint8),i,'1/16') for i,v in enumerate([0,255])]
    model=lambda image:image.mean().reshape(1,1)*100
    scored=score_complete_frames(frames,model,'cpu',expected_frames=2,expected_shape=(2,3,3))
    assert scored['frame_scores']==[0,100] and scored['normalized_score']==.5
    with pytest.raises(ValueError,match='Incomplete'):score_complete_frames(frames[:1],model,'cpu',2,(2,3,3))
    with pytest.raises(ValueError,match='Nonfinite'):score_complete_frames(frames,lambda x:torch.tensor(float('nan')),'cpu',2,(2,3,3))
    with pytest.raises(ValueError,match='geometry'):score_complete_frames(frames,model,'cpu',2,(3,2,3))
    image=prepare_frame(np.full((432,768,3),255,dtype=np.uint8));assert image.shape==(1,3,288,512) and torch.all(image==1)


def test_paired_denominator_preserves_rejects_and_time_alignment():
    a={'frames':2,'pts':[[0,'1/16'],[1,'1/16']],'normalized_score':.4}
    rows=[{'name':'a','status':'SCORED','reference':a,'candidate':dict(copy.deepcopy(a),normalized_score=.3)},
          {'name':'b','status':'VIDEO_REJECTED'}]
    s=paired_summary(rows,['a','b']);assert s['planned']==2 and s['scored_pairs']==1 and s['candidate_lower']==1 and s['rejected_candidates']==1
    assert s['equal_sample_mean_delta']==pytest.approx(-.1)
    with pytest.raises(ValueError,match='Incomplete'):paired_summary(rows[:1],['a','b'])
    bad=copy.deepcopy(rows);bad[0]['candidate']['pts'][1][0]=3
    with pytest.raises(ValueError,match='PTS'):paired_summary(bad,['a','b'])
