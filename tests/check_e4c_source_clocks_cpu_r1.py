"""Distinguish source age before an action from refresh after-age zero."""
import copy


def run(clocks):
    actions=['DD','DD','CC','PP','CC','CC','CC','CC','PP','CC','DD']+['DD']*25
    dense=[[],[]];working=[None,None];history=[]
    for step,action in enumerate(actions,1):
        before=copy.deepcopy(dense)
        if action=='DD':dense=[(x+[step])[-2:] for x in dense]
        if action!='CC':working=[{'slot':b,'kind':action[0],'created_step':step} for b in (0,1)]
        a={'step':step,'action':action,'shared_alpha':1 if action=='CC' else 0,
            'branch_status':['scalar']*2 if action=='CC' else ['ACTUAL_REFRESH']*2,
            'working_source_kind':[v['kind'] for v in working],
            'past_D_steps':copy.deepcopy(dense),'extra_heads':2 if action=='CC' else 0}
        history.append({'step':step,'action':action,'working_sources':copy.deepcopy(working),
            'working_source_ages':[step-v['created_step'] for v in working],
            'true_D_before':before,'true_D_after':copy.deepcopy(dense),'A_readout':a,
            'source_policy':{'creation_floor_proxy_after':.02 if working[0]['kind']=='P' else 0,
                'accumulated_interval_proxy_after':.03},'native_cycle_reset':step==35})
        if step==35:dense=[[],[]];working=[None,None]
    row={'collect':'CPD','actions':actions,'collection_complete':{'deployment':{'history':history}},
        'instrumented_parent_pipeline_wall_seconds':123.}
    out=clocks(row)
    assert out['C_reads_P_source']==5 and out['P_to_P_transitions']==1 and out['P_to_D_transitions']==1
    p=out['P_events'][0]
    assert p['created_step']==4 and p['C_read_steps']==[5,6,7,8] and p['C_read_ages']==[1,2,3,4]
    assert p['next_refresh_step']==9 and p['next_refresh_action']=='PP'
    assert p['same_P_source_still_present_at_age']=={'1':True,'2':True,'4':True}
    assert out['steps'][3]['source_age_before']==[2,2] and out['steps'][3]['source_age_after']==[0,0]
    assert out['steps'][4]['source_age_before']==[1,1] and out['steps'][4]['true_D_last_age_before']==[3,3]
    assert out['steps'][4]['true_D_interval_steps_before']==[1,1]
    assert out['steps'][35]['source_kind_before']==[None,None] and out['steps'][35]['true_D_steps_before']==[[],[]]
    controls=[]
    for name,change in [
        ('lost_step',lambda h:h.pop()),
        ('wrong_step',lambda h:h[4].update(step=8)),
        ('after_age_used_as_before',lambda h:h[4].update(working_source_ages=[0,0])),
        ('discontinuous_D',lambda h:h[4].update(true_D_before=[[1,3],[1,3]])),
        ('P_promotes_D',lambda h:h[3].update(true_D_after=[[2,4],[2,4]])),
        ('C_rebirth',lambda h:h[4]['working_sources'][0].update(created_step=5)),
        ('future_source',lambda h:h[3]['working_sources'][0].update(created_step=6)),
        ('readout_other_source',lambda h:h[4]['A_readout'].update(working_source_kind=['D','D'])),
        ('missing_cycle_reset',lambda h:h[34].update(native_cycle_reset=False))]:
        bad=copy.deepcopy(row);change(bad['collection_complete']['deployment']['history'])
        try:clocks(bad)
        except ValueError:controls.append(name)
        else:raise AssertionError('Invalid causal clock admitted: '+name)
    ra=clocks({'collect':'SOURCE_RA','collection_complete':{'deployment':None}})
    assert not ra['applicable'] and ra['steps']==[]
    return {'status':'E4C_CAUSAL_BEFORE_AFTER_CLOCK_CPU_CONTROLS_PASS_NOT_REAL_TRACE_RESULT',
        'synthetic36_steps':36,'synthetic_P_events':2,'synthetic_C_reads_P':5,'refusals':controls,
        'native_cycle_reset_preserved':True,'RA_not_zero_filled_as_P_trace':True}
