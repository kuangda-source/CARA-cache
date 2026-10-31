"""Child-only CPU injection for the unchanged production guardian entry.

Loaded through a temporary sitecustomize in this test's PYTHONPATH. All GPU,
Docker and further process creation boundaries fail closed. No real credential
or production stage is supplied.
"""
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace


def install():
    stage = Path(os.environ['CARA_DISPATCH_CPU_STAGE'])
    assert (stage/'CPU-dispatch-fixture').read_text() == 'TEMPORARY_CPU_ONLY\n'
    assert Path('/proc/self').exists()
    assert os.environ['CUDA_VISIBLE_DEVICES'] == ''
    assert os.environ['NVIDIA_VISIBLE_DEVICES'] == 'void'
    from wcomr import cara_s_endpoint_gpu_dispatch_r1 as dispatch
    from wcomr import cara_s_endpoint_host_guardian_r1 as guardian
    from wcomr.cara_budget_search_journal_r1 import read_record, create_record
    from wcomr.history104_storage_r2 import FixedJournal

    config = read_record(stage/'CPU-storage.json')
    journal = FixedJournal(Path(config['journal_path']))

    def persist(key, path, value, writer):
        journal.write(key, value)
        writer(path, value)

    storage = SimpleNamespace(config=config, output=Path(config['output_mount']),
                              journal=journal, check=lambda: {}, persist=persist)
    dispatch.storage_for = lambda selected: storage if selected == stage else None

    def forbidden(*args, **kwargs):
        raise AssertionError('CPU child must not access GPU, Docker or spawn another process')

    original_allocate = guardian.allocate

    def failed_allocation(project, selected, bound_storage, password):
        assert selected == stage and bound_storage is storage
        assert password == 'CPU-ONLY-NO-CREDENTIAL'
        create_record(stage/'CPU-credential-received.json', dict(
            synthetic_credential_received=True, real_credential_used=False))
        # Exercise original journal/terminal code with a missing credential,
        # before any lock, device or container allocation is attempted.
        return original_allocate(project, selected, storage, None,
            observe_gpu=forbidden, change_mode=forbidden, inspect=forbidden, stop=forbidden)

    guardian.allocate = failed_allocation
    subprocess.Popen = forbidden
    subprocess.run = forbidden
    subprocess.check_output = forbidden

