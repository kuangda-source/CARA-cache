"""The two registered read/write mechanism cards; no execution authority."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class CardIdentity:
    run_id: str
    stage_name: str
    card_kind: str
    target_update: int
    manifest: str
    profile: str
    phase: str

    @property
    def dense_control(self):
        return f'D{self.target_update}_CONTROL'

    def check_stage(self, name, *, cpu_validation=False):
        if self.target_update == 8:
            prefix = 'cara-read-write-M1-CPU-fixture-' if cpu_validation else 'cara-read-write-M1-GPU-'
            valid = name.startswith(prefix)
        else:
            valid = (name.startswith('cara-source-lifecycle-P0-point20-CPU-fixture-')
                     if cpu_validation else name == self.stage_name)
        if not valid:
            raise ValueError('Original registered read/write stage differs from its card')


M1 = CardIdentity('cara-read-write-M1-full14-r1-20261101',
    'cara-read-write-M1-GPU-a6000-full14-r1-20261101', 'CARA_READ_WRITE_M1_FULL14', 8,
    'plans/cara_next_stage_20261101/read_write/M1_FULL14_MANIFEST_R2.json',
    'plans/cara_next_stage_20261101/read_write/M1_FULL14_CONTAINER_PROFILE_R1.json', 'READ_WRITE_M1')
P0 = CardIdentity('cara-source-lifecycle-P0-point20-full14-r1-20261101',
    'cara-source-lifecycle-P0-point20-GPU-a6000-full14-r1-20261101',
    'CARA_SOURCE_LIFECYCLE_P0_POINT20_FULL14', 20,
    'plans/cara_next_stage_20261101/source_lifecycle/P0_POINT20_FULL14_MANIFEST_R1.json',
    'plans/cara_next_stage_20261101/source_lifecycle/P0_POINT20_CONTAINER_PROFILE_R1.json',
    'SOURCE_LIFECYCLE_P0_POINT20')


def for_run(run_id):
    if run_id == P0.run_id:
        return P0
    # Preserve original M1 CPU metadata fixtures and production naming.
    if re.fullmatch('cara-read-write-M1-[a-z0-9-]+', run_id):
        return M1
    raise ValueError('Only the original M1 or distinct registered P0 point20 identity is supported')


def for_card(card):
    if card['schema'] == 'CARA_READ_WRITE_M1_FULL14_PROSPECTIVE_CARD_R2' and card['target_update'] == 8:
        return M1
    if (card['schema'] == 'CARA_SOURCE_LIFECYCLE_P0_POINT20_FULL14_EXECUTION_SCOPE_R1'
            and card['target_update'] == 20 and card['run_id'] == P0.run_id):
        return P0
    raise ValueError('Read/write scope and registered intervention point differ')
