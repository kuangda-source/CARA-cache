"""Pinned L0-only CPU asset acquisition via small anonymous HTTP ranges."""
import argparse
import json
import os
from pathlib import Path
import time
from urllib.parse import quote
from wcomr.ranged_download import transfer
from verify_public_assets import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.manifest.read_text())
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or protocol['endpoint'] != 'https://huggingface.co':
        raise ValueError('Only anonymous official CPU acquisition is supported')
    if protocol.get('download_strategy') != 'bounded_http_ranges' or protocol['cpu_download_seconds_cap'] != 3600:
        raise ValueError('Wrong frozen range acquisition protocol')
    project = args.manifest.resolve().parent.parent
    integrity = json.loads((project / protocol['integrity_manifest']).read_text())
    state = {'stage': 'L0_ADAPTER_RANGE_CPU_ACQUISITION', 'pid': os.getpid(),
             'status': 'RUNNING', 'started_unix': time.time(), 'completed': [],
             'gpu_workload_started': False, 'chunk_bytes': protocol['range_chunk_bytes']}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)

    def save():
        tmp = args.receipt.with_suffix('.tmp')
        tmp.write_text(json.dumps(state, indent=2) + '\n')
        tmp.replace(args.receipt)

    def progress(stats):
        state['current_transfer'] = stats
        save()

    save()
    try:
        for source in protocol['sources']:
            repo, revision = source['repo_id'], source['revision']
            if not repo.startswith('Efficient-Large-Model/LongLive-Plug-Wan2.2-TI2V-5B-') or integrity[repo]['revision'] != revision:
                raise ValueError('L0 source family or revision differs')
            cache = args.cache / ('models--' + repo.replace('/', '--'))
            snapshot = cache / 'snapshots' / revision
            snapshot.mkdir(parents=True, exist_ok=True)
            checks = []
            for row in integrity[repo]['files']:
                relative = Path(row['path'])
                if relative.is_absolute() or '..' in relative.parts:
                    raise ValueError('Unsafe asset path')
                state.update(current=repo, current_file=row['path'])
                save()
                result = verify(snapshot, row)
                if result['status'] != 'PASS':
                    if result['status'] != 'MISSING':
                        raise ValueError('Existing snapshot corrupt; preserve for inspection')
                    oid = row['lfs']['oid'] if 'lfs' in row else row['git_blob_oid']
                    blob = cache / 'blobs' / oid
                    url = protocol['endpoint'] + '/' + repo + '/resolve/' + revision + '/' + quote(row['path'])
                    transfer(url, blob.with_name(blob.name + '.incomplete'), blob, row['size'], oid,
                             chunk_bytes=protocol['range_chunk_bytes'], attempts=protocol['range_attempts_per_chunk'],
                             socket_timeout=protocol['socket_timeout_seconds'], git_blob='lfs' not in row, progress=progress)
                    target = snapshot / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.exists() or target.is_symlink():
                        raise ValueError('Snapshot file appeared concurrently; preserve')
                    target.symlink_to(blob.resolve())
                    result = verify(snapshot, row)
                    if result['status'] != 'PASS':
                        raise ValueError('Final snapshot digest differs')
                checks.append(result)
            (cache / 'refs').mkdir(exist_ok=True)
            (cache / 'refs/main').write_text(revision)
            state['completed'].append({'repo_id': repo, 'revision': revision, 'snapshot': str(snapshot), 'integrity': checks})
            save()
        state['status'] = 'ALL_SELECTED_FILES_OFFICIAL_HASH_PASS_NOT_LOAD_TESTED'
    except Exception as error:
        state.update(status='RESOURCE_BLOCKED_PARTIAL_RETAINED', error_type=type(error).__name__)
        raise RuntimeError('L0 bounded range acquisition failed; inspect durable receipt') from None
    finally:
        state['ended_unix'] = time.time()
        save()


if __name__ == '__main__':
    main()
