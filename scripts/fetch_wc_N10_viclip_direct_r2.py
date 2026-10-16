#!/usr/bin/env python3
"""Same pinned full checkpoint and range verifier, with explicit direct HTTPS."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from types import ModuleType

ORIGINAL='fetch_wc_N10_viclip_ranges_r1.py'
ORIGINAL_SHA='abed3996e5552680aefb1c63f179c3c394ea4b2abb4fb0e0a1812c3be611dee4'
POLICY='DIRECT_HTTPS_NO_ENV_PROXY'


def derive(stage):
    path=Path(stage)/ORIGINAL;raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA:
        raise ValueError('Keep the original full-range source and whole-object verifier')
    source=raw.decode();changed=source
    edits=(("[registration['curl_executable'], '--location'",
            "[registration['curl_executable'], '--disable', '--location'"),
        ("'--proxy', 'http://127.0.0.1:7897', '--connect-timeout', '15'",
            "'--proxy', '', '--noproxy', '*', '--connect-timeout', '15', '--max-time', '90'"))
    for before,after in edits:
        if changed.count(before)!=1:raise ValueError('Exact declared curl transport changes required')
        changed=changed.replace(before,after)
    restored=changed
    for before,after in reversed(edits):restored=restored.replace(after,before)
    if restored!=source or ast.dump(ast.parse(restored))!=ast.dump(ast.parse(source)):
        raise ValueError('The original full scope, retry, range or digest logic cannot change')
    module=ModuleType('pinned_direct_range_resource_r2');module.__file__=str(Path(__file__).resolve())
    exec(compile(changed,str(path)+'#direct-HTTPS-only', 'exec'),vars(module))
    return module,dict(original_range_source_sha256=ORIGINAL_SHA,
        inverse_bytes_and_AST_equal=True,declared_transport_replacements=2,
        full_scope_and_range_ETag_and_whole_SHA_unchanged=True,TLS_verification_disabled=False)


def download(stage):
    stage=Path(stage).resolve();reg=json.loads((stage/'registration.json').read_text())
    if reg.get('transport_policy')!=POLICY or reg.get('original_range_worker_sha256')!=ORIGINAL_SHA:
        raise ValueError('Use the explicitly registered direct route and original range source')
    module,_=derive(stage)
    return module.download(stage)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',type=Path,required=True)
    raise SystemExit(download(parser.parse_args().stage))
