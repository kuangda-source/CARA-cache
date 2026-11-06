"""Read original accepted point8 scores and complete accepted point20 only."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def main():
    p=argparse.ArgumentParser()
    for name in ('point20-accepted','point20-packet','output'):
        p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args()
    assert not args.output.exists()
    from wcomr.cara_read_write_identity_r1 import P0
    from wcomr.cara_source_lifecycle_native_bridge_r1 import ACCEPTED_SHA256,PACKET_SHA256
    from wcomr.cara_source_lifecycle_p0_analysis_r1 import combine
    accepted_file=ROOT/'reports/cara_read_write_complete_acceptance_r1_20261101.json'
    assert hashlib.sha256(accepted_file.read_bytes()).hexdigest()==ACCEPTED_SHA256
    original=json.loads(accepted_file.read_text())
    def saved(key):
        file=ROOT/original['evidence_refs'][key]
        raw=file.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==original['evidence_sha256'][key]
        return json.loads(raw)
    assert original['evidence_sha256']['packet']==PACKET_SHA256
    point8_packet=saved('packet')
    point8_card=json.loads((ROOT/'reports/cara_read_write_final_card_original_r1_20261101.json').read_text())
    assert point8_card['scope_sha256']==original['scope_sha256']==point8_packet['manifest']['scope_sha256']
    result=combine(point8_card,saved('accepted_scores'),json.loads((ROOT/P0.manifest).read_text()),
        json.loads(args.point20_accepted.read_text()),json.loads(args.point20_packet.read_text()))
    result.update(original_point8_acceptance_sha256=ACCEPTED_SHA256,
                  original_point8_actual_GPUh=original['actual_GPUh'])
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=result['status'],output=str(args.output))))


if __name__=='__main__':
    main()
