#!/usr/bin/env python3
"""Freeze one complete engineering-budgeted N10 config, no CPU/GPU launch."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
CONFIG_REF='configs/wc_paper_N10_full960_production_r1_20261018.json'
SCOPE_REF='manifests/wc_paper_N10_unpriced_full960_production_scope_20261018.json'
COST_REF='reports/wc_paper_N10_full960_engineering_cost_R1_20261018.json'


def read(ref):
    path=ROOT/ref;raw=path.read_bytes();return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def binding(ref):return dict(ref=ref,sha256=hashlib.sha256((ROOT/ref).read_bytes()).hexdigest())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not any((ROOT/r).exists() for r in (CONFIG_REF,COST_REF)) and not a.output.exists()
    sys.path.insert(0,str(ROOT/'src'))
    from wcomr.automatic_quality_production_r1 import validate
    from wcomr.automatic_quality_quote_r1 import quote,validate_selected,VERSION
    scope=read(SCOPE_REF)
    for evidence in scope['source_evidence'].values():
        assert binding(evidence['ref'])['sha256']==evidence['sha256']
    template=scope['unpriced_config_template'];values=[read(template['references'][k]['ref'])
        for k in ('accepted_inputs','model_CPU_acceptance','model_CPU_registration','model_resources')]
    for info in template['references'].values():assert binding(info['ref'])['sha256']==info['sha256']
    cost=quote(scope);rawcost=(json.dumps(cost,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    c=copy.deepcopy(template);c.update(engineering_cost_policy=VERSION,
        forecast_GPUh=cost['forecast_GPUh'],billed_limit_GPUh=cost['billed_limit_GPUh'])
    c['references'].update(unpriced_scope=binding(SCOPE_REF),
        whole_card_cost=dict(ref=COST_REF,sha256=hashlib.sha256(rawcost).hexdigest()))
    validate(c,scope['validation_registration_preview'],*values);validate_selected(c,scope,cost)
    assert cost['forecast_GPUh']==4.915 and cost['billed_limit_GPUh']==6.25
    config=(json.dumps(c,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    with (ROOT/COST_REF).open('xb') as h:h.write(rawcost)
    with (ROOT/CONFIG_REF).open('xb') as h:h.write(config)
    result=dict(status='N10_COMPLETE960_ENGINEERING_QUOTE_CONFIG_SELECTED_NOT_PRODUCTION_CPU_OR_GPU',
        config_ref=CONFIG_REF,config_sha256=hashlib.sha256(config).hexdigest(),cost_ref=COST_REF,
        cost_sha256=hashlib.sha256(rawcost).hexdigest(),scope_ref=SCOPE_REF,
        input_bundle_fingerprint=c['input_bundle_fingerprint'],scope_counts=c['scope_counts'],
        comparisons=len(c['comparisons']),forecast_GPUh=4.915,billed_limit_GPUh=6.25,
        cost_inputs_are_engineering_allowances_not_measured_GPU_rates=True,
        actual_production_CPU_accepted=False,new_quality_scores=0,GPU_submissions=0,ledger_written=False)
    with a.output.open('x') as h:json.dump(result,h,ensure_ascii=False,indent=2,allow_nan=False);h.write('\n')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
