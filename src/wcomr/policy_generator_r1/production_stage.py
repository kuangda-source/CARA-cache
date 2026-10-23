"""Separate PG stage: accepted clean prices are a pre-load requirement."""
import json
from pathlib import Path
from .production_contract import COUNTS,VERSION,matrix
from .production_evidence import sha
from .continuation_preparation import require
RUN='cara-pg-p1-cal-fit4-select2-full64-ada-r1'
CONFIG='pg-config.json'
CPU_PROOF='PG-combination-CPU.json'
CPU_BUNDLE=CPU_PROOF
read=lambda p:json.loads(Path(p).read_text())


def accepted_assets(stage):
    stage=Path(stage)
    old_raw=(stage/'pg-old-labels.json').read_bytes();new_raw=(stage/'pg-clean-prices.json').read_bytes()
    old=read(stage/'pg-old-acceptance.json');accepted=read(stage/'pg-price-acceptance.json');new=json.loads(new_raw)
    import hashlib
    digest=lambda b:hashlib.sha256(b).hexdigest()
    require(accepted.get('status')=='FULL_PRICE_ORIGINALS_EXCLUSIVITY_AND_FINANCE_ACCEPTED'
        and accepted.get('full_protocol_accepted') is True and accepted.get('clean_action_prices_accepted') is True
        and accepted.get('exclusive_monitoring',{}).get('accepted') is True,'Complete exclusive price acceptance before model load required')
    require(old.get('full_protocol_accepted') is True and old.get('formal_source_time_cells')==1624,'Original complete labels required')
    require(accepted['replacement_bundle_sha256']==digest(new_raw) and accepted['original_label_bundle_sha256']==digest(old_raw),'Asset bytes differ from accepted originals')
    original=json.loads(old_raw)
    require(new['statistics']==original['statistics'] and new['profile']==original['profile'] and new['fit_members']==original['fit_members'],'Repricing changed labels or split')
    require(new['status']=='COMPLETE_OLD_LABELS_WITH_NEW_EXCLUSIVE_PRICES' and new['clean_action_prices_accepted'] and new['exclusive_monitoring_accepted'],'Old prices cannot pass through')
    require(len(new['statistics'])==1624,'Whole price/label denominator required')
    return old_raw,new_raw,old,accepted


def validate(project,stage):
    stage=Path(stage);project=Path(project);reg=read(stage/'registration.json')
    require(reg['namespace']==VERSION and reg['stage']==str(stage),'Wrong complete PG stage')
    for name,h in reg['payload_sha256'].items():
        p=stage/name
        require(not p.is_symlink() and p.resolve().is_relative_to(stage.resolve()) and sha(p)==h,'Frozen PG source/input changed: '+name)
    for name,h in reg['runtime_source_sha256'].items():require(sha(project/'runtime'/name)==h,'Runtime changed')
    c=read(stage/CONFIG);q=read(stage/'pg-whole-quote.json')
    require(c['scope_counts']==q['scope_counts']==COUNTS and c['matrix']==q['matrix']==matrix() and c['run_id']==RUN,'Whole64 scope differs')
    require(0<q['forecast_complete_GPUh']<=q['billed_limit_GPUh']<12,'Whole autonomous quote required')
    require(all(c[k]==q[k] for k in ('forecast_complete_GPUh','billed_limit_GPUh')),'Quote/config mismatch')
    assets=accepted_assets(stage)
    required=['pg-config.json','pg-whole-quote.json','pg-old-labels.json','pg-clean-prices.json','pg-old-acceptance.json','pg-price-acceptance.json','pg-exposure-baseline.json']
    require(all(n in reg['payload_sha256'] for n in required),'Stage omitted immutable scientific prerequisites')
    return c,reg,assets
