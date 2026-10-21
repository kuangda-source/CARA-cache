#!/usr/bin/env python3
"""Bind omitted historical metadata to the SAME scientific Git revision.

The original1789 denominator and captured registration are never extended or
edited. New, separately registered metadata are inputs to an explicit host port.
"""
import gzip
import io
import json
from pathlib import Path
import subprocess
import tarfile

from four_card_bank24_execution_adapter_r1 import LIFECYCLE_SOURCE, digest, read, require
from four_card_bank24_host_contract_r1 import archive_members

BASE = Path('.sync/four-card-bank24-host-cpu-r1-20261022/frozen-closure.tgz')
DIRECTORY = Path('.sync/four-card-bank24-execution-adapter-r1-20261022')
MANIFEST = Path('manifests/wc_four_card_bank24_execution_metadata_r1_20261022.json')


def freeze():
    require(not MANIFEST.exists(), 'Never change an existing metadata registration')
    original = read('reports/wc_scout_BANK24_GPU_lifecycle_CPU_R2_collection_20261019.json.gz')['registration']['payload_sha256']
    files = archive_members(BASE.read_bytes(), original)
    additions = {}
    def fetch(name):
        rel=Path(name)
        require(not rel.is_absolute() and '..' not in rel.parts, 'Invalid historical metadata path')
        if name not in files:
            body=subprocess.check_output(['git','show',LIFECYCLE_SOURCE+':'+name])
            files[name]=body;additions[name]=body
        return files[name]
    def value(name):return json.loads(fetch(name))
    def native(proof, role):
        record=proof['files'][role];body=fetch(record['local_path']);raw=gzip.decompress(body)
        require(digest(body)==record['compressed_sha256'] and digest(raw)==record['sha256']
                and len(raw)==record['bytes'], 'Captured native metadata bytes differ')
        return json.loads(raw)
    cost=value('reports/wc_action_cost_real_r1_terminal_20261010_capture_and_independent_audit.json')
    parent=value('reports/wc_ra_plus_a_r1_terminal_20261010_capture_and_independent_audit.json')
    script=value('reports/wc_current_birth_real_parameters_cpu_r1_results_20261010.json')
    for name,expected in script['source_sha256'].items():
        require(digest(fetch(name))==expected, 'Historical source byte mismatch')
    for name in ['reports/wc_action_cost_real_r1_bound_ranking_inputs_20261010.json',
                 'reports/wc_real_cost_creation_phase_prior_r1_bound_20261010.json']:
        fetch(name)
    native(cost,'calibration_table');config=native(parent,'config');native(parent,'runner')
    for key in ['calibration_table_ref','calibration_runner_ref','independent_threshold_ref']:
        fetch(config[key])
    design=value('manifests/wc_ra_conservative_half_threshold_r2_design_preregistration_20261010.json')
    require(digest(fetch(design['basis_ref']))==design['basis_sha256'], 'Frozen prior basis changed')
    profile=value('configs/wc_p_acr_local12_profile528_production_r1_20261015.json')
    for binding in profile['references'].values():
        require(digest(fetch(binding['ref']))==binding['sha256'], 'Frozen H1 input changed')
    # BANK24 dependencies remain byte-exact even if a stale graph omitted a ref.
    bank=value('configs/wc_scout_bank24_production_entry_r1_20261018.json')
    for binding in bank['references'].values():
        require(digest(fetch(binding['ref']))==binding['sha256'], 'Frozen BANK24 input changed')
    require(not set(original).intersection(additions), 'Cannot override original closure')
    raw=io.BytesIO()
    with tarfile.open(fileobj=raw,mode='w') as archive:
        for name,body in sorted(additions.items()):
            info=tarfile.TarInfo(name);info.size=len(body);info.mode=0o600;info.mtime=0
            archive.addfile(info,io.BytesIO(body))
    packed=gzip.compress(raw.getvalue(),mtime=0)
    DIRECTORY.mkdir(parents=True,exist_ok=True)
    target=DIRECTORY/'execution-metadata.tgz'
    with target.open('xb') as out:out.write(packed)
    # A local code-only input copy permits exact reconstruction without SSH.
    root=DIRECTORY/'inputs'
    for name,body in files.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as out:out.write(body)
    result=dict(status='BANK24_SAME_SOURCE_ADDITIONAL_METADATA_FROZEN_NOT_PRODUCTION_CPU',
        source_revision=LIFECYCLE_SOURCE,original_denominator=1789,
        original_payload_sha256=original,additional_metadata_sha256={n:digest(b) for n,b in additions.items()},
        additional_metadata_files=len(additions),additional_metadata_bytes=sum(map(len,additions.values())),
        metadata_archive_ref=str(target),metadata_archive_sha256=digest(packed),metadata_archive_bytes=len(packed),
        provenance='EXACT_GIT_BLOB_BYTES_FROM_ORIGINAL_2bd41dc8_NO_NEW_FIT',
        old_physical_Native_artifacts_required=False,new_Native_paths_required=6,
        captured_registration_modified=False,GPU_submissions=0,ledger_written=False)
    with MANIFEST.open('x') as out:out.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['original_payload_sha256','additional_metadata_sha256']}))


if __name__=='__main__':freeze()
