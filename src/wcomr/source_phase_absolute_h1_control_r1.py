"""Teacher-free four-action H1 with calibrated absolute same-state errors.

This is a local objective, not learned terminal action value or a covariance
bound. The old positive root birth proxy is retained as an empirical feature.
"""
import copy,hashlib,json,math
from dataclasses import replace

from .source_aware_current_birth_control_r1 import CurrentBirthCPDController
from .source_aware_cpd_control import Choice,SourceAwareCPDController
from .source_phase_table_fit_r1 import cell,feature

VERSION='SOURCE_PHASE_ABSOLUTE_GUIDED_MSE_FOUR_ACTION_H1_R1'


def fingerprint(parameters):
    p={k:v for k,v in parameters.items() if k!='fingerprint'}
    return hashlib.sha256(json.dumps(p,sort_keys=True,allow_nan=False).encode()).hexdigest()


def validate_parameters(p):
    if p.get('version')!=VERSION or p.get('fingerprint')!=fingerprint(p):raise ValueError('Frozen full table fingerprint required')
    model=p['table_model'];costs=p['cost_seconds']
    expected={'D_EARLY','D_LATE','P_EARLY','P_LATE'} if model['grouping']=='SOURCE_PHASE' else {'D','P'}
    if (model['grouping'] not in ('SOURCE_PHASE','SOURCE') or model['target']!='absolute_guided_MSE'
            or model['current_teacher_energy_is_online_feature'] or set(model['cells'])!=expected
            or p['lambda_seconds_per_weighted_absolute_MSE']<=0
            or not math.isfinite(p['lambda_seconds_per_weighted_absolute_MSE'])
            or set(costs)!={'C','A','P','D'} or any(not math.isfinite(v) or v<=0 for v in costs.values())
            or set(p['source_A_cost_seconds'])!={'D','P'}
            or any(not math.isfinite(v) or v<=0 for v in p['source_A_cost_seconds'].values())
            or not 0<=p['gamma']<=1):raise ValueError('Absolute complete cells/positive costs/lambda and frozen gamma required')
    for cell in model['cells'].values():
        if cell['status']=='FIT':
            values=[cell['C_scale'],cell['A_ratios']['FUSION_A'],cell['actual_NEW_P_birth_mean']]
            if any(not math.isfinite(v) or v<0 for v in values) or cell['C_scale']==0 or cell['actual_NEW_P_birth_mean']==0:
                raise ValueError('Current calibrated finite scale, harmful A and positive P birth required')
        elif cell['status']!='UNKNOWN_ZERO_FEATURE_OR_C_TARGET':raise ValueError('Explicit UNKNOWN cell required')


class SourcePhaseH1Controller(CurrentBirthCPDController):
    def __init__(self,*args,table_parameters,math_parameters,horizon,sigma_at,fixed_control_plan=None,**kw):
        super().__init__(*args,**kw);p=copy.deepcopy(table_parameters);validate_parameters(p)
        if horizon!=1 or not callable(sigma_at) or fixed_control_plan is not None:
            raise ValueError('One-step free actual action choice required; no future forecast')
        # Original pi0 C includes stage A; new H1 quotes plain C and A apart.
        if (self.costs.C not in (p['cost_seconds']['C'],p['source_A_cost_seconds']['D']) or self.costs.D!=p['cost_seconds']['D']
                or self.costs.P!=p['cost_seconds']['P'] or math_parameters['gamma']!=p['gamma']):
            raise ValueError('Bound pi0 stage-A ordering versus H1 semantic quotes/gamma differ')
        self.table_parameters,self.math_parameters,self.horizon,self.sigma_at=p,copy.deepcopy(math_parameters),horizon,sigma_at

    def predicted_actions(self,choice):
        source=choice.state_before[1];phase='EARLY' if choice.step<25 else 'LATE'
        point={'selection':{'source':source,'phase':phase},'parent_pre_action':choice.state_before,
            'actual_C_paid_proxy':{'local_proxy':choice.local_proxy}}
        model=self.table_parameters['table_model'];fitted=model['cells'].get(cell(point,model['grouping']))
        if fitted is None or fitted['status']!='FIT':return None
        qc=fitted['C_scale']*feature(point)
        costs=self.table_parameters['cost_seconds'];gain=choice.gain
        prices={'C':costs['C'],'A':self.table_parameters['source_A_cost_seconds'][source],'D':costs['D']}
        losses={'C':qc,'A':qc*fitted['A_ratios']['FUSION_A'],'D':0.}
        if (choice.partial_ready and self.partial_prior is not None and self.costs.P is not None
                and choice.state_before[5]<self.partial_prior.maximum_consecutive_P):
            prices['P']=costs['P'];losses['P']=fitted['actual_NEW_P_birth_mean']
        if any(not math.isfinite(v) or v<0 for v in list(losses.values())+[gain]):return None
        lam=self.table_parameters['lambda_seconds_per_weighted_absolute_MSE']
        result={a:{'price':prices[a],'absolute_current_MSE':losses[a],'gain_squared_risk':gain*gain*losses[a],
            'score':prices[a]+lam*gain*gain*losses[a]} for a in prices}
        if any(not math.isfinite(v['gain_squared_risk']) or not math.isfinite(v['score']) for v in result.values()):return None
        return result

    def _choice(self,step,packet_values,ready,partial_ready,protected=False):
        origin=CurrentBirthCPDController._choice(self,step,packet_values,ready,partial_ready,protected)
        if protected:return origin
        if origin.local_proxy is None:return origin
        table=self.predicted_actions(origin)
        if table is None:
            name='A' if origin.action=='C' and self.working_kind=='D' else origin.action
            return replace(origin,reason='MATH_EVENT_TABLE_PI0_UNKNOWN_FALLBACK:'+name)
        # Do not filter by the old root-risk threshold: new calibrated MSE
        # and lambda form a distinct objective with the same structural domain.
        name=min(table,key=lambda a:(table[a]['score'],{'C':0,'A':1,'P':2,'D':3}[a]))
        floor=0. if name=='D' else self.partial_prior.creation_floor_at(step) if name=='P' else self.creation_floor
        if name=='P' and floor<=0:raise ValueError('Real P root source floor remains positive')
        # Keep the original root bookkeeping for a real pi0 fallback at the
        # state reached by this policy. Absolute squared errors are NOT added
        # into this root accumulator or compared with its threshold.
        root_added=0. if name=='D' else origin.gain*floor if name=='P' else origin.gain*(self.creation_floor+origin.local_proxy)
        return replace(origin,action='C' if name=='A' else name,added_risk=root_added,
            predicted_creation_floor=floor,candidates=tuple((a,v['price'],v['gain_squared_risk'],
                0. if a=='D' else self.partial_prior.creation_floor_at(step) if a=='P' else self.creation_floor) for a,v in table.items()),
            reason='MATH_EVENT_TABLE_ABSOLUTE_H1:'+name)

    def commit(self,choice,*,actual_action,pair_completed):
        return SourceAwareCPDController.commit(self,choice,actual_action=actual_action,pair_completed=pair_completed)

    def state_dict(self):
        value=super().state_dict();value['binding']+=(VERSION,self.table_parameters['fingerprint'],self.math_parameters['fingerprint'])
        return value

    def restore(self,snapshot):
        if set(snapshot)!={'binding','state','history'} or snapshot['binding']!=self.state_dict()['binding']:
            raise ValueError('Exact new table/lambda/cost/source/gamma snapshot required')
        replay=SourcePhaseH1Controller(self.calibration,self.threshold,self.costs,self.partial_prior,strategy=self.strategy,
            table_parameters=self.table_parameters,math_parameters=self.math_parameters,horizon=1,sigma_at=self.sigma_at)
        for original in snapshot['history']:
            if not isinstance(original,Choice) or original.owner!=id(self):raise ValueError('Foreign absolute-table history')
            d=replay._choice(original.step,original.packets,original.both_sources_ready,original.partial_ready,protected=original.reason=='actual_protected_dense')
            if replace(d,owner=id(self))!=original:raise ValueError('Changed table choice/history')
            replay.commit(d,actual_action=d.action,pair_completed=True)
        if replay._state()!=snapshot['state'] or snapshot['state'][-1]:raise ValueError('Incomplete/poisoned table restore')
        old=self.state_dict()
        (self.anchor,self.working_kind,self.working_step,self.creation_floor,self.accumulated,
            self.consecutive_P,self.last_completed_step,self.generation,self.poisoned)=snapshot['state']
        self.history=copy.deepcopy(snapshot['history']);return old

    def query_basis(self,choice):
        value=super().query_basis(choice);table=self.predicted_actions(choice) if choice.local_proxy is not None else None
        return {**value,'math_version':VERSION,'risk_unit':'AMPLITUDE_GAIN_SQUARED_ABSOLUTE_GUIDED_MSE_PROXY',
            'source_before':choice.state_before[1],'phase':'EARLY' if choice.step<25 else 'LATE',
            'source_age_and_root_floor_outside_cal16_are_TRANSFER':True,'physical_P_keeps_original_positive_root_floor':True,
            'absolute_new_P_error_not_written_to_root_floor':True,'candidate_risk_and_price':table,
            'choice_added_risk_and_accumulator_unit':'ORIGINAL_GAIN_TIMES_ROOT_PROXY_FOR_PI0_FALLBACK',
            'candidate_score_risk_unit':'AMPLITUDE_GAIN_SQUARED_ABSOLUTE_GUIDED_MSE',
            'pi0_action_order_prices':{'legacy_C_including_stage_A':self.costs.C,'P':self.costs.P,'D':self.costs.D},
            'H1_semantic_plain_C_price':self.table_parameters['cost_seconds']['C'],
            'H1_source_A_price':self.table_parameters['source_A_cost_seconds'][choice.state_before[1]] if choice.state_before[1] in ('D','P') else None,
            'old_root_threshold_used_for_new_objective':False,'absolute_error_written_into_root_accumulator':False,
            'actual_online_candidate_evaluations':0,
            'actual_online_teacher_calls':0,'future_drift_forecast_used':False,'terminal_pi0_value_fitted':False,
            'optimizer_selected_D':choice.reason=='MATH_EVENT_TABLE_ABSOLUTE_H1:D'}
