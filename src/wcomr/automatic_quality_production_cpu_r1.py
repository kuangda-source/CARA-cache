"""Complete quoted full960 production CPU acceptance, no scoring or GPU IO."""
from .automatic_quality_production_r1 import CPU_STATUS
from .automatic_quality_quote_r1 import validate_selected

PATTERNS=('test_N10_production_entry_r1.py','test_N10_supervisor_r1.py',
          'test_N10_complete_batch_r1.py','test_N10_whole_quote_r1.py')
BUNDLE='N10-production-CPU-bundle-result.json'
PROOF='CPU-scoring-entry-result.json'
STATUS='N10_FULL960_QUOTED_PRODUCTION_CPU_BUNDLE_PASS_NOT_GPU'
ACCEPTED='N10_FULL960_ACTUAL_PRODUCTION_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU'


def original_alive(expected, observed):
    return bool(expected and observed and expected['pid']==observed['pid']
                and expected['start_ticks']==observed['start_ticks']
                and observed['state'] not in (None,'Z','X'))


def accept(value):
    launch=value['launch'];reg=value['registration']
    if (value['status']!='N10_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE'
            or value['observed_unix']<launch['final_not_before_unix']
            or value['registration_sha256']!=launch['registration_sha256']
            or reg['source_revision']!=launch['source_revision']
            or value['payload_actual_sha256']!=reg['payload_sha256']
            or value['GPU_submissions'] or value['ledger_written']):
        raise ValueError('Exact full quoted source and original post-ETA CPU capture required')
    if original_alive(launch['identity'],value['process']):
        return dict(status='N10_PRODUCTION_CPU_STILL_RUNNING_REESTIMATE_ONCE',CPU_accepted=False)
    b,p,e,c=(value['files'][k].get('data') for k in ('bundle','proof','exit','config'))
    if not all((b,p,e,c)) or b.get('exit_code')!=0 or e.get('exit_code')!=0:
        return dict(status='N10_PRODUCTION_CPU_FAILURE_OR_MISSING_RETAINED',CPU_accepted=False)
    for name in ('unpriced_scope','whole_card_cost'):
        actual=value['files'][name];ref=c['references'][name]
        if actual['sha256']!=ref['sha256'] or reg['payload_sha256'].get(ref['ref'])!=ref['sha256']:
            raise ValueError('Exact original whole960 cost and source bytes required')
    validate_selected(c,value['files']['unpriced_scope']['data'],value['files']['whole_card_cost']['data'])
    expected=[[b['python_executable'],'-m','unittest','discover','-s',b['stage']+'/tests','-p',n,'-v'] for n in PATTERNS]
    expected.append([b['python_executable'],b['stage']+'/scripts/score_wc_paper_N10_full960_r1.py',
        '--project',b['project'],'--stage',b['stage'],'--cpu-check'])
    if (b['status']!=STATUS or b['source_revision']!=launch['source_revision']
            or b['registration_sha256']!=launch['registration_sha256'] or b['stage']!=launch['stage']
            or b['project']!=launch['project']
            or [r['command'] for r in b['commands']]!=expected
            or any(r['exit_code']!=0 for r in b['commands'])
            or b['actual_original_five_model_proof_reaccepted'] is not True
            or b['control_source_sha256']!={'tests/'+n:reg['payload_sha256']['tests/'+n] for n in PATTERNS}
            or b['proof_sha256']!=value['files']['proof']['sha256']
            or p['status']!=CPU_STATUS or p['exit_code']!=0
            or p['source_revision']!=launch['source_revision']
            or p['registration_sha256']!=launch['registration_sha256']
            or p['config_sha256']!=value['files']['config']['sha256']
            or b['config_sha256']!=p['config_sha256']
            or p['scope_counts']!=c['scope_counts'] or p['metric_positions']!=960
            or p['input_bundle_fingerprint']!=c['input_bundle_fingerprint']
            or p['runner_source_sha256']!=reg['payload_sha256']['scripts/score_wc_paper_N10_full960_r1.py']
            or value['files']['config']['sha256']!=reg['payload_sha256']['N10-production-config.json']
            or e['bundle_sha256']!=value['files']['bundle']['sha256']
            or e['source_revision']!=launch['source_revision']
            or any(e['original_CPU_identity'].get(k)!=launch['identity'].get(k) for k in ('pid','start_ticks'))
            or any(b[k] for k in ('GPU_submissions','ledger_written','model_weights_loaded'))
            or p['neural_framework_imported'] or p['GPU_submissions'] or p['ledger_written']):
        raise ValueError('Every original five-command CPU identity, real input/price and no-model boundary must agree')
    return dict(status=ACCEPTED,CPU_accepted=True,source_revision=launch['source_revision'],
        registration_sha256=launch['registration_sha256'],config_sha256=p['config_sha256'],
        production_CPU_sha256=value['files']['proof']['sha256'],bundle_sha256=value['files']['bundle']['sha256'],
        original_CPU_identity=launch['identity'],scope_counts=c['scope_counts'],CPU_commands=5,
        forecast_GPUh=c['forecast_GPUh'],billed_limit_GPUh=c['billed_limit_GPUh'],
        CPU_wall_seconds=b['wall_seconds'],new_quality_scores=0,GPU_submissions=0,ledger_written=False)
