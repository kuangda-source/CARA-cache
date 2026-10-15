"""Contain video subprocess failures; never promote a failed parent to success."""
import ast
import hashlib
import inspect
import subprocess
from textwrap import dedent

class VideoFailureGuard:
    def __init__(self):self.failures=[]
    def wrap(self,read):
        def guarded(row):
            try:return read(row)
            except subprocess.SubprocessError as error:
                self.failures.append(dict(parent_id=row['id'],scene=row['scene'],
                    error_type=type(error).__name__,error=str(error),
                    video_artifact=row.get('video_artifact'),original_video_unchanged=True))
                raise ValueError('ORIGINAL_VIDEO_CONTAINER_OR_DECODE_FAILURE: '+str(error)) from error
        return guarded
    def annotate(self,report):
        parents={p['id']:p for p in report['parents']}
        eligible=[];model_only=[];warm=[];sensitivity=[]
        for label in report['labels']:
            parent=parents[label['parent_id']]
            full=(parent['audit_status']=='AUDITED' and parent.get('all36_guided_actions_Ahistory_final_equal') is True
                  and parent.get('all93_RGB_equal_to_resident_baseline') is True)
            usable=bool(label['labels_available'] and full and label['section']=='FORMAL')
            raw_model=bool(label['labels_available'] and label['section']=='FORMAL'
                and parent.get('all36_guided_actions_Ahistory_final_equal') is True)
            label['sensitivity_raw_model_fit_admitted']=raw_model
            if raw_model:sensitivity.append(label)
            label['primary_grouped_fit_admitted']=usable
            label['primary_fit_policy']='REQUIRE_ORIGINAL_FULL_PARENT_RAW_AND_RGB_AUDIT_FORMAL_ONLY'
            if usable:eligible.append(label)
            elif label['labels_available'] and label['section']=='WARMUP':warm.append(label)
            elif label['labels_available']:model_only.append(label)
        return dict(video_subprocess_failures_retained=self.failures,
            sensitivity_raw_model_fit_label_count=len(sensitivity),
            sensitivity_raw_model_fit_prompt_groups=sorted({r['scene'] for r in sensitivity}),
            primary_grouped_fit_label_count=len(eligible),
            primary_grouped_fit_prompt_groups=sorted({r['scene'] for r in eligible}),
            model_only_formal_labels_not_in_primary_fit=len(model_only),
            warmup_labels_excluded_from_fit=len(warm),
            original_full_scope_acceptance_relaxed=False,
            original_source_GPU_or_files_written=False,
            repaired_video_or_new_GPU_submission=False)

def derive_reader(main):
    source=dedent(inspect.getsource(main))
    changes=[('        report=audit_all(', '        guard=_VideoFailureGuard()\n        report=audit_all('),
      ("read_video=video,provenance='REAL_SAME_STATE_POST_RF')", "read_video=guard.wrap(video),provenance='REAL_SAME_STATE_POST_RF')"),
      ('        result.update(report)', '        result.update(report)\n        result.update(guard.annotate(report))\n        result[\'reader_repair\']=_reader_repair_identity')]
    changed=source
    for old,new in changes:
        if changed.count(old)!=1:raise ValueError('Exactly one explicit reader repair site required: '+old)
        changed=changed.replace(old,new,1)
    inverse=changed
    for old,new in reversed(changes):
        if inverse.count(new)!=1:raise ValueError('Reader repair inverse is ambiguous')
        inverse=inverse.replace(new,old,1)
    if inverse!=source or ast.dump(ast.parse(inverse))!=ast.dump(ast.parse(source)):
        raise ValueError('Read-only post changed outside video exception/annotation sites')
    proof=dict(explicit_sites=3,inverse_AST_equal=True,original_main_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
               original_CAD_raw_auditor_changed=False,original_artifact_hash_checks_changed=False,
               original_parent_failure_and_full_denominators_preserved=True)
    ns={**main.__globals__,'_VideoFailureGuard':VideoFailureGuard,'_reader_repair_identity':proof}
    exec(compile(changed,__file__+'#read-only-post-repair','exec'),ns)
    return ns['main'],proof
