"""Fetch the four fixed native runtime wheels; never install/import them."""
import argparse
import json
import os
from pathlib import Path
import shutil
import time
from urllib.parse import urlsplit
from wcomr.ranged_download import transfer
from wcomr.wheel_assets import inspect_wheel, acquire_release_asset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.manifest.read_text())
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or protocol['cpu_download_seconds_cap'] != 3600:
        raise ValueError('Wrong CPU-only wheel protocol')
    if {x['package'] for x in protocol['files']} != {'torch', 'torchvision', 'torchaudio', 'flash-attn'} or len(protocol['files']) != 4:
        raise ValueError('Full four-wheel scope required')
    args.cache.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(args.cache).free < 4 << 30 or args.receipt.exists():
        raise ValueError('Insufficient disk or existing job identity')
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    state = {'pid': os.getpid(), 'started_unix': time.time(), 'status': 'RUNNING',
             'gpu_workload_started': False, 'completed': []}

    def save():
        temp = args.receipt.with_suffix('.tmp')
        temp.write_text(json.dumps(state, indent=2) + '\n')
        temp.replace(args.receipt)

    def progress(stats):
        state['current_transfer'] = stats
        save()

    save()
    try:
        for row in protocol['files']:
            name = row['filename']
            if Path(name).name != name or not name.endswith('.whl') or row['size'] <= 0:
                raise ValueError('Invalid wheel filename/size')
            url = row.get('download_url', row['url'])
            if urlsplit(url).scheme != 'https' or urlsplit(url).hostname not in ('download.pytorch.org', 'github.com'):
                raise ValueError('Unexpected wheel source endpoint')
            state.update(current=name, current_transfer=None)
            save()
            blob = args.cache / name
            if row['official_sha256'] is not None:
                result = transfer(url, blob.with_name(name + '.incomplete'), blob, row['size'], row['official_sha256'], progress=progress)
                result['metadata'] = inspect_wheel(blob, row)
                result['official_sha256'] = row['official_sha256']
            else:
                result = acquire_release_asset(row, args.cache, progress=progress)
            state['completed'].append({'filename': name, 'path': str(blob), 'integrity': result})
            save()
        state['status'] = 'ALL4_WHEEL_PAYLOADS_VERIFIED_FLASH_LOCAL_SHA_ONLY_NOT_INSTALLED'
    except Exception as error:
        state.update(status='WHEEL_ACQUISITION_FAILED_PARTIAL_RETAINED', error_type=type(error).__name__)
        raise RuntimeError('CPU wheel acquisition failed; inspect sanitized durable receipt') from None
    finally:
        state['ended_unix'] = time.time()
        save()


if __name__ == '__main__':
    main()
