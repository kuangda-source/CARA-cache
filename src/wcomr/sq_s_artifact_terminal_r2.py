"""Independent complete S artifact byte/cohort checks; no tensor deserialization."""
import hashlib
import json
from pathlib import Path

from .gpu_budget_pool_v2 import sha,finite
from .sq_s_data_terminal_r2 import require,signature


def check_file(path,reference,maximum_bytes):
    path=Path(path);before=path.stat()
    require(path.is_file() and not path.is_symlink() and type(reference['bytes']) is int
        and 0<before.st_size==reference['bytes']<=maximum_bytes and signature(reference['sha256']),
        'Original bounded S artifact size/path differs')
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8*2**20),b''):value.update(block)
    after=path.stat();stamp=lambda stat:(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns)
    require(value.hexdigest()==reference['sha256'] and stamp(before)==stamp(after),
        'Original S artifact bytes or identity changed')
    return dict(path=str(path),bytes=after.st_size,sha256=value.hexdigest())


def check_artifacts(collection,output,*,collection_sha256,CPU_fixture=False):
    """Check every registered byte; this does not certify raw-tensor replay."""
    output=Path(output)
    require(type(CPU_fixture) is bool and collection['CPU_fixture']==CPU_fixture
        and collection['actual_CUDA'] is (not CPU_fixture) and output.is_absolute() and not output.is_symlink(),
        'Original S real/CPU artifact boundary differs')
    collection_path=output/'S-collection.json'
    require(not collection_path.is_symlink() and collection_path.stat().st_size<=16*2**20
        and sha(collection_path)==collection_sha256 and json.loads(collection_path.read_text())==collection,
        'Original complete S collection bytes differ')
    root=output/'streaming'
    require(root.is_dir() and not root.is_symlink() and root.resolve().parent==output.resolve(),
        'Original private S streaming directory required')
    storage=collection['matrix']['storage'];reference=storage['manifest']
    checked=[];names=set()
    def artifact(ref):
        name=ref['name']
        require(Path(name).name==name and name not in names and not name.startswith('.'),
            'Duplicate or foreign S artifact basename')
        names.add(name);value=check_file(root/name,ref,2*2**30);checked.append(value);return value
    require(reference['name']=='manifest.json','Original S streaming manifest required')
    artifact(reference);manifest=json.loads((root/'manifest.json').read_text())
    require(manifest['schema']=='SQ_S_STREAMING_STORAGE_DATA_ONLY_R1'
        and manifest['status']=='COMPLETE_CPU_DATA_ARTIFACTS_NOT_SCIENTIFIC_ACCEPTANCE'
        and manifest['maximum_total_bytes']==28*2**30 and manifest['maximum_file_bytes']==2*2**30
        and manifest['minimum_free_bytes']>=512*2**20
        and manifest['actual_Cosmos_weights_accepted'] is False and manifest['scientific_S_labels_accepted'] is False,
        'Original bounded S streaming contract differs')
    moments=[row for item in collection['matrix']['rows'] for row in item['result']['S_rows']]
    expected={(row['prompt'],row['parent'],row['step']):row for row in moments}
    key=lambda row:(row['prompt'],row['parent'],row['step'])
    require(len(moments)==len(expected)==len(manifest['rows'])==108
        and manifest['prompts']==list(dict.fromkeys(row['prompt'] for row in moments))
        and len(manifest['raw_states'])==8 and len(manifest['anchors'])==24,
        'Original complete S streaming row/raw/anchor cohort differs')
    raw={key(row):row['artifact'] for row in manifest['raw_states']}
    selected={key(row) for row in moments if row['raw_state_selected']}
    require(set(raw)==selected and len(raw)==8,'Original eight F19 raw artifact identities differ')
    seen=set()
    for row in manifest['rows']:
        identity=key(row)
        require(identity in expected and identity not in seen,'Duplicate or foreign S row artifact')
        seen.add(identity);artifact(row['artifact'])
        saved=json.loads((root/row['artifact']['name']).read_text())
        original=dict(expected[identity])
        # The original collector adds this duration after the durable sink
        # returns. It is intentionally absent from the saved scalar row.
        timing=original.pop('diagnostic_seconds_including_shadow_copy_hash_sink',None)
        require((CPU_fixture or (finite(timing) and timing>=0))
            and saved==dict(original,raw_artifact=raw.get(identity)),
            'S saved scalar row differs from original complete collection')
    for ref in raw.values():artifact(ref)
    expected_anchors=set()
    for row in moments:
        if row['raw_state_selected']:
            for branch in (0,1):
                for step in row['source']['source_anchor_steps']:
                    expected_anchors.add((row['prompt'],row['parent'],branch,step))
    observed_anchors=[(row['prompt'],row['parent'],row['branch'],row['step']) for row in manifest['anchors']]
    require(len(expected_anchors)==24 and set(observed_anchors)==expected_anchors
        and len(set(observed_anchors))==24,'Original complete S anchor identities differ')
    for row in manifest['anchors']:
        require(signature(row['content_sha256']),'Original S anchor content identity missing')
        artifact(row['artifact'])
    require({path.name for path in root.iterdir()}==names
        and sum(row['bytes'] for row in checked)-reference['bytes']==manifest['payload_bytes_before_manifest']
        and sum(row['bytes'] for row in checked)==storage['actual_stored_bytes']<=28*2**30,
        'S streaming payload denominator/total bytes changed or extra partial files remain')
    paths_root=output/'paths'
    require(paths_root.is_dir() and not paths_root.is_symlink() and paths_root.resolve().parent==output.resolve(),
        'Original private S role directory required')
    videos=[]
    for row in collection['matrix']['rows']:
        slot=row['slot'];ref=row['result']['encoded_video'];path=Path(ref['path'])
        parent=output/'paths'/slot['id']
        require(path.is_absolute() and not parent.is_symlink() and parent.resolve().parent==paths_root.resolve()
            and path.resolve().parent==parent.resolve(),
            'S encoded artifact escaped its original role')
        videos.append(check_file(path,ref,2*2**30))
    require(len(videos)==len({row['path'] for row in videos})==10,
        'Original ten saved S videos required')
    return dict(status='S_COMPLETE_ARTIFACT_BYTES_PASS',CPU_fixture=CPU_fixture,
        collection_sha256=collection_sha256,manifest_sha256=reference['sha256'],
        row_files=108,raw_files=8,anchor_files=24,video_files=10,
        streaming_bytes=sum(row['bytes'] for row in checked),video_bytes=sum(row['bytes'] for row in videos),
        original_file_bytes_accepted=True,raw_tensors_deserialized=False,raw_tensor_replay_accepted=False,
        scientific_S_effect_established=False,complete_video_deployment_or_speed_established=False,
        validator_sha256=sha(__file__),files=checked+videos)
