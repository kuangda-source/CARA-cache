"""Read-only historical originals and explicit cross-batch compatibility.

A mismatch is an observed bridge result, never permission to rewrite old runs or
pool incompatible cohorts. Missing/corrupt originals are technical failures.
"""
import hashlib,json
from pathlib import Path
from .continuation_preparation import require
from .production_evidence import sha
from .shared66_card import digest
CAPTURE='reports/cara_history104_R2_terminal_20261024_2315.json'
NATIVE_SLOT='CALIBRATION_NATIVE_0_1'

def expected_origins(card, capture):
    rows={role:dict(slot_id=b['slot_id'],artifact_checks=b['artifact_checks'],policy_fingerprint=b['policy_fingerprint'],RGB93=b['RGB93']) for role,b in card['historical_bridges'].items()}
    rows['NATIVE35']=dict(slot_id=NATIVE_SLOT,artifact_checks=capture['artifact_checks'][NATIVE_SLOT],policy_fingerprint=None,RGB93=None)
    return rows

def load_origins(card, root):
    from .shared66_collection import tensor_digest
    from ..rv0_video_reader import decoded_video
    import torch
    path=Path(root)/CAPTURE
    require(sha(path)==next(iter(card['historical_bridges'].values()))['capture_sha256'],'Historical receipt SHA differs')
    capture=json.loads(path.read_text());rows=expected_origins(card,capture);result={}
    for role,b in rows.items():
        ck=b['artifact_checks']
        require(ck==capture['artifact_checks'][b['slot_id']], 'Historical checks not original')
        for key in ('video_artifact','final_latent_artifact','request_artifact'):
            a=ck[key];p=Path(a['path'])
            require(p.is_file() and p.stat().st_size==a['bytes'] and sha(p)==a['sha256'],'Historical artifact differs: '+role+'/'+key)
        request=json.loads(Path(ck['request_artifact']['path']).read_text())
        if b['policy_fingerprint'] is not None:
            require(request['policy']['fingerprint']==b['policy_fingerprint']==card['roles'][role]['policy']['fingerprint'],'Bridge policy differs')
        latent=tensor_digest(torch.load(ck['final_latent_artifact']['path'],map_location='cpu',weights_only=True)['final_latent'])
        require(latent==ck['latent_tensor'],'Historical tensor bytes differ')
        h=hashlib.sha256();frames=0
        with decoded_video(ck['video_artifact']['path']) as video:
            for frame,pts,base in video:h.update(frame.tobytes());frames+=1
        rgb=dict(frames=frames,sha256=h.hexdigest())
        require(frames==93 and (b['RGB93'] is None or rgb==b['RGB93']),'Historical RGB digest differs')
        result[role]=dict(slot_id=b['slot_id'],artifact_checks=ck,policy_fingerprint=b['policy_fingerprint'],RGB93=rgb)
    return dict(capture_sha256=sha(path),originals=result,read_only=True,CUDA_used=False)

def comparisons(card, checks, rgb, packet):
    require(packet['capture_sha256']==next(iter(card['historical_bridges'].values()))['capture_sha256'] and packet['read_only'] and not packet['CUDA_used'],'Historical original binding missing')
    require(set(packet['originals'])=={'S26_C','SHARED26_C','NATIVE35'},'Two bridges plus original Native required')
    capture_path=Path(__file__).resolve().parents[3]/CAPTURE
    require(sha(capture_path)==packet['capture_sha256'],'Bound original capture missing')
    original=json.loads(capture_path.read_text())
    result=[]
    for role,old in packet['originals'].items():
        require(old['artifact_checks']==original['artifact_checks'][old['slot_id']],'Historical native/source artifact mismatch')
        section='QUALITY' if role=='NATIVE35' else 'HISTORICAL_BRIDGE'
        slot=next(s for s in card['matrix'] if s['section']==section and s['role']==role and s['member']==card['CAL_FIT_members'][0])
        if role!='NATIVE35':
            bound=card['historical_bridges'][role]
            require(old['slot_id']==bound['slot_id'] and old['artifact_checks']==bound['artifact_checks'] and old['policy_fingerprint']==bound['policy_fingerprint'],'Historical role/source mismatch')
            require(bound['RGB93'] is None or old['RGB93']==bound['RGB93'],'Historical known RGB mismatch')
        require(old['RGB93']['frames']==rgb[slot['id']]['frames']==93,'Bridge frame denominator')
        result.append(dict(role=role,new_slot_id=slot['id'],old_slot_id=old['slot_id'],latent_equal=checks[slot['id']]['latent_tensor']==old['artifact_checks']['latent_tensor'],RGB93_equal=rgb[slot['id']]==old['RGB93']))
    return dict(comparisons=result,historical_pooling_compatible=all(r['latent_equal'] and r['RGB93_equal'] for r in result),independent_new_samples_added=0)
