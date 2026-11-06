"""Sparse CAL point selection and explicit-layout, read-only group scoring."""
import torch
from .shadow_metrics import tensor_error

LAYOUTS={'residual':{'name':'B,T,H,W,D','time':1,'height':2,'width':3,'channel':4,'channel_name':'hidden_features'},
         'velocity':{'name':'B,C,T,H,W','time':2,'height':3,'width':4,'channel':1,'channel_name':'latent_channels'}}


def select_pairs(trace,max_pairs=4):
    """Select from the OFF deployment trace alone, before any shadow truth."""
    if type(max_pairs) is not int or max_pairs<1:raise ValueError('Positive max_pairs required')
    if len(trace)%2:raise ValueError('Incomplete CFG pairs')
    eligible=[];history=[[],[]];cycle=0;previous=None
    for offset in range(0,len(trace),2):
        rows=trace[offset:offset+2]
        for j,row in enumerate(rows):
            counter=row['cache_counter_before']
            if row['call']!=offset+j+1 or type(counter) is not int or counter<0 or type(row['deep_executed']) is not bool:
                raise ValueError('Malformed deployment trace')
            if counter==0:
                history=[[],[]];cycle+=1
            elif previous is None or counter!=previous+1:raise ValueError('Unexplained cache-counter transition')
            previous=counter
            if counter%2!=j:raise ValueError('CFG pair branch layout changed')
        # A horizon reset can only occur at the first member of this pair.
        counters=[r['cache_counter_before'] for r in rows]
        if counters[1]!=counters[0]+1:raise ValueError('CFG pair reset mid-pair')
        if all(not r['deep_executed'] for r in rows) and all(len(h)>=2 for h in history):
            eligible.append({'calls':[r['call'] for r in rows],'cache_counters':counters,
                             'cycle':cycle,'anchor_steps':[list(h) for h in history]})
        for branch,row in enumerate(rows):
            if row['deep_executed']:history[branch]=(history[branch]+[row['cache_counter_before']])[-2:]
    n=len(eligible);take=min(max_pairs,n)
    indices=list(range(n)) if take==n else [round(i*(n-1)/(take-1)) for i in range(take)] if take>1 else [0]
    chosen=[eligible[i] for i in indices]
    return {'rule':'OFF trace only; both CFG skip and at least two strictly past full anchors each; evenly spaced eligible-pair ranks',
            'eligible_pairs':n,'selected_pairs':chosen,'calls':[c for pair in chosen for c in pair['calls']],
            'coverage':'FULL_FOUR_PAIR_SCREEN' if len(chosen)==4 else 'INSUFFICIENT_SKIP_COVERAGE'}


def _ranges(size,bins):
    count=min(size,bins)
    return [(i*size//count,(i+1)*size//count) for i in range(count)]


@torch.no_grad()
def grouped_error(prediction,truth,kind):
    layout=LAYOUTS[kind]
    if truth.ndim!=5:raise ValueError('Pinned group scoring requires five-dimensional tensors')
    out=tensor_error(prediction,truth)
    out['layout']={'axes':layout['name'],'shape':list(truth.shape),'channel_semantics':layout['channel_name']}
    if out['status']!='OK':return out
    partitions={}
    for name in ['time','channel']:
        axis=layout[name];groups=[]
        for start,end in _ranges(truth.shape[axis],4):
            sl=[slice(None)]*5;sl[axis]=slice(start,end)
            score=tensor_error(prediction[tuple(sl)],truth[tuple(sl)])
            groups.append({'bounds':{str(axis):[start,end]},'elements':truth[tuple(sl)].numel(),'metrics':score})
        partitions[name]=groups
    groups=[];h,w=layout['height'],layout['width']
    for hs,he in _ranges(truth.shape[h],2):
        for ws,we in _ranges(truth.shape[w],2):
            sl=[slice(None)]*5;sl[h]=slice(hs,he);sl[w]=slice(ws,we)
            groups.append({'bounds':{str(h):[hs,he],str(w):[ws,we]},'elements':truth[tuple(sl)].numel(),
                           'metrics':tensor_error(prediction[tuple(sl)],truth[tuple(sl)])})
    partitions['spatial']=groups;out['partitions']=partitions
    return out


def validate_geometry(net,residual,velocity):
    if residual.ndim!=5 or velocity.ndim!=5:raise ValueError('Unsupported pinned tensor rank')
    expected=(residual.shape[1]*net.patch_temporal,residual.shape[2]*net.patch_spatial,residual.shape[3]*net.patch_spatial)
    if residual.shape[0]!=velocity.shape[0] or tuple(velocity.shape[2:])!=expected:
        raise ValueError('Unpatchify geometry differs from pinned BTHWD -> BCTHW mapping')


def validate_pair(off,on,selection):
    keys=['outcome','guardrail_events','forward_output_sha256','block_counts','trace','cache_end_sha256',
          'sampling','pipeline_events','decoder_calls','video_sha256','decoded_rgb','flags_before','flags_after']
    checks={key:off[key]==on[key] for key in keys}
    records=on['shadow_records']
    checks['selected_calls_observed']=[r['call'] for r in records]==selection['calls']
    checks['finite_metrics']=all(r['candidates'][m][k]['status']=='OK' and all(g['metrics']['status']=='OK'
        for groups in r['candidates'][m][k]['partitions'].values() for g in groups)
        for r in records for m in ['official','scalar','shrink'] for k in ['prewarp_residual','postwarp_residual','velocity'])
    checks['past_anchors_only']=all(len(r['candidates'][m]['history']['anchor_steps'])>=2 and
        all(step<r['cache_counter'] for step in r['candidates'][m]['history']['anchor_steps'])
        for r in records for m in ['scalar','shrink'])
    checks['flags_restored']=off['flags_before']==off['flags_after']==on['flags_before']==on['flags_after']
    if not all(checks.values()):raise ValueError('W1-D off/on parity or truth isolation check failed: '+str(checks))
    return checks
