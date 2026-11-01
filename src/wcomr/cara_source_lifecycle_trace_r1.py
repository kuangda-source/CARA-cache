"""Direct two-source cache consumers from a complete accepted owner history."""


def consumers(history, source_step):
    if ([r['step'] for r in history] != list(range(1,37))
            or type(source_step) is not int or not 1 <= source_step <= 36):
        raise ValueError('Complete original36 history and one source step required')
    reads = [[],[]];replaced = [None,None];minted = [False,False]
    for row in history:
        t = row['step'];source = row['source_history']
        if (row['actual'] not in ('C','D') or row['fallback_reason'] is not None
                or source['extra_heads'] != 0 or source['teacher_calls'] != 0):
            raise ValueError('Actual pure C/D history without hidden extra compute required')
        anchors = source['past_D_steps']
        if len(anchors) != 2:
            raise ValueError('Both CFG source records required')
        for branch in (0,1):
            if t == source_step:
                minted[branch] = source_step in anchors[branch]
            if t <= source_step or not minted[branch]:
                continue
            if row['actual'] == 'C' and source_step in anchors[branch]:
                reads[branch].append(t)
            if replaced[branch] is None and source_step not in anchors[branch]:
                replaced[branch] = t
    return dict(source_step=source_step, minted= minted, C_consumers=reads,
        replaced_after_update=replaced, direct_residual_source_trace=True,
        full_working_state_influence_measured=False)
