"""Read-only decomposition of existing F16 predictions; no new fit or tuning."""
import hashlib
import json
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
SOURCE='reports/wc_fb_probe_scheduled_collection_20261013.json'
PREVIOUS='reports/wc_fb_probe_F16_independent_decision_analysis_20261013.json'


def main():
    source=ROOT/SOURCE;previous=ROOT/PREVIOUS
    capture=json.loads(source.read_text());old=json.loads(previous.read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest()==old['source_capture_sha256']
    assert capture['source_revision']=='a95b8166efd0371363bd28a1852bbddb448ec935'
    f=capture['F_analysis'];rows=[r for fold in f['folds'] for r in fold['held_rows']]
    assert len(rows)==16 and len({(r['scene'],r['step']) for r in rows})==16
    assert len({r['scene'] for r in rows})==4
    methods=['SOURCE_PHASE_LOPO','RAW_CLOCK','RAW_SUB','HAAR','FFT'];values={m:[] for m in methods}
    full=[]
    for r in rows:
        truth=r['actual_absolute_guided_MSE'];cost=r['source_prices'];g2=r['gain_squared']
        dq=truth['C']-truth['A'];dc=cost['A']-cost['C']
        assert dq>0 and dc>0 and g2>0
        state=dict(scene=r['scene'],step=r['step'],source=r['source'],parent_action=r['parent_continues'],
                   actual_CA_q_improvement=dq,actual_CA_lambda_breakpoint=dc/(g2*dq),methods=[])
        assert {s['method'] for s in r['scores']}==set(methods)
        for score in r['scores']:
            name=score['method'];p=score['prediction'];ec=p['C']-truth['C'];ea=p['A']-truth['A']
            common=(ec+ea)/2;difference=ec-ea
            assert abs((ec*ec+ea*ea)-(2*common*common+.5*difference*difference))<1e-10
            values[name].append(dict(common_squared=common*common,difference_squared=difference*difference,
                                      gain_squared_difference_squared=g2*g2*difference*difference,
                                      total_two_target_squared=ec*ec+ea*ea))
            predicted_dq=p['C']-p['A'];decisions=[]
            for d in score['decisions']:
                lam=d['lambda'];margin=lam*g2*predicted_dq-dc;true_margin=lam*g2*dq-dc
                chosen='A' if margin>0 else 'C';oracle='A' if true_margin>0 else 'C'
                assert chosen==d['chosen'] and oracle==d['local_CA_oracle']
                regret=abs(true_margin) if chosen!=oracle else 0.
                assert abs(regret-d['regret_seconds_plus_weighted_MSE'])<1e-10
                decisions.append(dict(lambda_value=lam,primary=d['primary_lambda'],predicted_margin=margin,
                                      true_margin=true_margin,chosen=chosen,local_CA_oracle=oracle,regret=regret))
            state['methods'].append(dict(method=name,predicted_CA_q_improvement=predicted_dq,
                predicted_lambda_breakpoint=dc/(g2*predicted_dq) if predicted_dq>0 else None,decisions=decisions))
        full.append(state)
    aggregates={name:{key:mean(v[key] for v in data) for key in data[0]} for name,data in values.items()}
    base,raw=aggregates['SOURCE_PHASE_LOPO'],aggregates['RAW_SUB']
    reduction=base['total_two_target_squared']-raw['total_two_target_squared']
    contribution=2*(base['common_squared']-raw['common_squared'])/reduction
    harmful=[r for r in full if any(d['primary'] and d['chosen']!=d['local_CA_oracle']
                                   for d in r['methods'][0]['decisions'])]
    assert len(harmful)==3
    result=dict(status='EXISTING_F16_COMMON_ERROR_AND_CA_MARGIN_DECOMPOSITION_NOT_NEW_METHOD',
        inputs={SOURCE:hashlib.sha256(source.read_bytes()).hexdigest(),PREVIOUS:hashlib.sha256(previous.read_bytes()).hexdigest()},
        states=16,prompt_groups=4,primary_lambda=f['primary_lambda'],aggregates=aggregates,
        RAW_SUB_fraction_of_two_target_squared_error_reduction_from_common_component=contribution,
        RAW_SUB_relative_difference_squared_error_reduction=1-raw['difference_squared']/base['difference_squared'],
        RAW_SUB_relative_gain_squared_difference_squared_error_reduction=1-raw['gain_squared_difference_squared']/base['gain_squared_difference_squared'],
        primary_locally_harmful_states=harmful,all_state_margins=full,
        GPU_submissions=0,server_contacts=0,ledger_written=False,new_regression_fitted=False,
        not_endpoint_quality_or_full_policy_generalization=True)
    out=ROOT/'reports/wc_F16_decision_margin_error_decomposition_20261013.json'
    assert not out.exists(),'Preserve prior result; do not replace it'
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','states','RAW_SUB_fraction_of_two_target_squared_error_reduction_from_common_component',
        'RAW_SUB_relative_difference_squared_error_reduction','RAW_SUB_relative_gain_squared_difference_squared_error_reduction','GPU_submissions')}))


if __name__=='__main__':main()
