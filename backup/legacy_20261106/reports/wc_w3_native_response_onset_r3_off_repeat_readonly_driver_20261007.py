
import base64,gzip,hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');out=root/'outputs'/M['run_id'];stage=root/M['stage']
s=json.loads((out/'supervisor.json').read_text());raw=(out/'diagnostic/receipt.json').read_bytes();r=json.loads(raw)
assert s['status']=='GPU_W3_NATIVE_RESPONSE_ONSET_RUNNING' and s['pid']==3115400 and s['child_pid']==3115418
assert s['source_revision']==r['source_revision']==M['source_revision']
processes={}
for pid,entry in [(3115400,'supervise_wc_w3_native_response_onset.py'),(3115418,'run_wc_w3_native_response_onset.py')]:
 p=pathlib.Path('/proc/'+str(pid));assert p.exists();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode();assert str(stage) in cmd and entry in cmd and M['source_revision'] in cmd
 processes[str(pid)]=cmd
row=r['requests'][0];by={c['label']:c for c in row['children']};a=by['OFF1'];b=by['OFF2'];trace=['inputs','outputs','deep','banks','solver_outputs']
assert a['status']==b['status']=='COMPLETE_NATIVE_RESPONSE_SUFFIX_NOT_RV_LABEL'
assert all(len(a[k])==len(b[k])==(14 if k=='solver_outputs' else 28) for k in trace)
checks={k:a[k]==b[k] for k in trace+['final_latent_sha256','response_boundaries']}
checks.update(final_state_components=a['record']['final_state_components']==b['record']['final_state_components'],action_report=a['record']['action_report']==b['record']['action_report'])
assert all(checks.values()) and a['record']['final_state_components'] and set(a['response_boundaries'])=={'65','67','69'}
assert a['record']['parent_restored'] is True and b['record']['parent_restored'] is True
encoded=next(c for c in row['decoded_children'] if c['label']=='OFF1');assert encoded['status']=='ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE'
artifact=encoded['artifact'];ref=r['scope']['references']['human_199']['official_WC'];video=pathlib.Path(artifact['path'])
actual_sha=hashlib.sha256(video.read_bytes()).hexdigest();assert video.stat().st_size==artifact['bytes']==ref['bytes'] and actual_sha==artifact['sha256']==ref['sha256']
post=root/'.sync/wc-w3-native-response-onset-postrun-cpu-r3-20261007';c=json.loads((post/'continuation.json').read_text());p=pathlib.Path('/proc/3115990');assert c['pid']==3115990 and p.exists() and str(post/'continue.py') in (p/'cmdline').read_bytes().replace(b'\0',b' ').decode()
assert c['status']=='WAITING_ORIGINAL_GPU_TERMINAL_NOT_CPU_AUDIT_OR_SCORE' and c['steps']==[]
archive=gzip.compress(raw,mtime=0)
result={'status':'TWO_COMPLETE_OFF_SUFFIXES_NINE_RAW_REPEAT_COMPARISONS_AND_OFF1_HISTORY_BYTE_BRIDGE_PASS_WHOLE_BATCH_PENDING','observed_unix':time.time(),'run_id':M['run_id'],'source_revision':M['source_revision'],'scope_counts':[1,10,6,2],'actual_original_process_cmdlines':processes,'postCPU_pid_confirmed_live':3115990,'postCPU_steps':0,'trace_lengths':{k:len(a[k]) for k in trace},'nine_repeat_checks':checks,'complete_suffixes_at_snapshot':sum(x['status']=='COMPLETE_NATIVE_RESPONSE_SUFFIX_NOT_RV_LABEL' for x in row['children']),'started_labels_at_snapshot':[x['label'] for x in row['children']],'OFF1_actual_encoded_sha256':actual_sha,'OFF1_historical_official_WC_byte_bridge':True,'parent_bridge_pending':True,'original_receipt_sha256':hashlib.sha256(raw).hexdigest(),'original_receipt_bytes':len(raw),'archive_sha256':hashlib.sha256(archive).hexdigest(),'GPU_submissions':0,'score_runs':0,'full_trajectory_acceptance':False,'new_quality_or_speed_result':False}
print(json.dumps({'result':result,'native_receipt_gzip':base64.b64encode(archive).decode()}))
