"""Anonymous full-video packets from already accepted evidence; no new metrics."""
import hashlib
import hmac
import json
from pathlib import Path
import shutil


AXES = ('content', 'motion', 'detail')
CHOICES = ('worse', 'no_obvious_difference', 'better', 'uncertain')


def plan_review(analysis, manifest, nonce):
    """The CLI owns complete-evidence validation; this boundary owns the packet."""
    if analysis['status'] != 'COMPLETE_ACCEPTED_B36_ANALYSIS' or analysis['CPU_fixture_only']:
        raise ValueError('Complete accepted production B36 analysis required')
    if len(nonce) != 32 or analysis['launch_id'] != manifest['launch_id']:
        raise ValueError('Original identity and a private32-byte packet nonce required')
    pairs = manifest['pairs']
    identities = {(r['score_id'], r['member'], r['role']) for r in analysis['per_member']}
    if len(pairs) != 32 or identities != {(p['id'], p['candidate']['member'], p['candidate']['role']) for p in pairs}:
        raise ValueError('Complete32 accepted positions required; no favorable subset')

    def opaque(value):
        return hmac.new(nonce, value.encode(), hashlib.sha256).hexdigest()

    members = sorted({p['candidate']['member'] for p in pairs}, key=lambda m: opaque('scene:'+m))
    if len(members) != 4:
        raise ValueError('Original four-CAL scope required')
    scenes = {member: 'S'+str(i+1).zfill(2) for i, member in enumerate(members)}
    cases = []
    for p in sorted(pairs, key=lambda p: opaque('order:'+p['id'])):
        candidate, reference = p['candidate'], p['reference']
        if reference['role'] != 'NATIVE35' or reference['member'] != candidate['member']:
            raise ValueError('Same-input Native reference required')
        case_id = 'C'+opaque('case:'+p['id'])[:16]
        cases.append(dict(case_id=case_id, scene=scenes[candidate['member']],
                          score_id=p['id'], member=candidate['member'], role=candidate['role'],
                          candidate=candidate, reference=reference))
    if len({c['case_id'] for c in cases}) != 32:
        raise ValueError('Packet case identity collision')
    public = dict(schema='CARA_ANONYMOUS_FULL_VIDEO_REVIEW_R1',
        package_id='R'+opaque('package')[:20], scene_count=4, case_count=32, frames=93, fps=16,
        axes=list(AXES), choices=list(CHOICES),
        cases=[dict(case_id=c['case_id'], scene=c['scene'],
                    reference='media/'+c['scene']+'-reference.mp4',
                    candidate='media/'+c['case_id']+'-candidate.mp4') for c in cases])
    return dict(public=public, cases=cases)


def asset_catalog(plan):
    """Keep original paths and hashes on the coordinator side only."""
    unique = {}
    for case in plan['cases']:
        for descriptor in (case['candidate'], case['reference']):
            old = unique.setdefault(descriptor['sha256'], descriptor)
            if old['bytes'] != descriptor['bytes']:
                raise ValueError('Conflicting accepted video byte identity')
    return [dict(path=d['path'], sha256=sha, bytes=d['bytes']) for sha, d in sorted(unique.items())]


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for body in iter(lambda: handle.read(1024*1024), b''):
            digest.update(body)
    return digest.hexdigest()


def materialize(plan, videos, output, template):
    """Copy hash-addressed originals without decoding, trimming or recompression."""
    videos, output = Path(videos), Path(output)
    if output.exists():
        raise ValueError('Fresh review directory required; preserve previous packets')
    catalog = asset_catalog(plan)
    for d in catalog:
        path = videos/(d['sha256']+'.mp4')
        if not path.is_file() or path.stat().st_size != d['bytes'] or file_sha(path) != d['sha256']:
            raise ValueError('Missing or changed original video: '+d['sha256'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    (output/'media').mkdir()
    copied = set()
    for private, public in zip(plan['cases'], plan['public']['cases']):
        for side in ('candidate', 'reference'):
            relative = public[side]
            if relative in copied:
                continue
            source = private[side]
            target = output/relative
            shutil.copyfile(videos/(source['sha256']+'.mp4'), target)
            if file_sha(target) != source['sha256']:
                raise ValueError('Copied original changed; preserve incomplete packet')
            copied.add(relative)
    packet = json.dumps(plan['public'], ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    (output/'review.html').write_text(Path(template).read_text().replace('__PACKET__', packet))
    (output/'packet.json').write_text(json.dumps(plan['public'], ensure_ascii=False, indent=2)+'\n')
    return dict(status='B36_ANONYMOUS_VIDEO_PACKET_MATERIALIZED_NOT_REVIEWED',
        package_id=plan['public']['package_id'], scenes=4, cases=32, copied_media=len(copied),
        original_unique_videos=len(catalog), files={str(p.relative_to(output)): file_sha(p)
        for p in sorted(output.rglob('*')) if p.is_file()}, human_reviews=0,
        independent_human_evidence=False, metrics_computed=False, GPU_submissions=0)


def validate_response(packet, response):
    """Validate completeness, never infer reviewer independence or method success."""
    if response.get('package_id') != packet['package_id'] or not response.get('reviewer', '').strip():
        raise ValueError('Packet identity and reviewer alias required')
    rows = response.get('responses', [])
    ids = [r['case_id'] for r in rows]
    if len(ids) != 32 or len(set(ids)) != 32 or set(ids) != {c['case_id'] for c in packet['cases']}:
        raise ValueError('All32 cases exactly once required')
    for row in rows:
        if row.get('full_watch_attested') is not True or any(row.get(axis) not in CHOICES for axis in AXES):
            raise ValueError('Complete-watch attestation and all three observations required')
    return dict(status='COMPLETE_RESPONSE_STRUCTURE_ONLY', cases=32,
                independent_human_evidence=False, scientific_result_accepted=False)
