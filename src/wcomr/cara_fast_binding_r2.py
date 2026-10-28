"""Resolve the Fast science source and its prospective production slot binding."""
import copy
import hashlib
import json
from pathlib import Path

from .cara_fast_spec_r1 import digest


def execution_view(science, specification):
    card = copy.deepcopy(science)
    parent_scope = card.pop('scope_sha256')
    card.update(copy.deepcopy(specification['overrides']))
    card.update(binding_version='CARA_FAST_PRODUCTION_BINDING_R2',
                scientific_parent_scope_sha256=parent_scope,
                base_manifest_file_sha256=specification['base_manifest']['sha256'])
    slots = card['physical_matrix']
    if len({slot['id'] for slot in slots}) != len(slots):
        raise ValueError('Distinct physical slot identities required')
    for slot in slots:
        if slot['eligible_clean_time'] and slot['audit_enabled']:
            raise ValueError('Clean timing cannot include guided tensor audit copies')
        if slot['section'] == 'A_DIAGNOSTIC' and (
                not slot['audit_enabled'] or slot['eligible_clean_time']):
            raise ValueError('Diagnostic paths must retain audit and remain outside clean means')
    card['scope_sha256'] = digest(card)
    return card


def load_card(root, specification_path):
    root = Path(root)
    spec = json.loads((root / specification_path).read_text())
    source = root / spec['base_manifest']['path']
    if hashlib.sha256(source.read_bytes()).hexdigest() != spec['base_manifest']['sha256']:
        raise ValueError('Frozen science source differs')
    science = json.loads(source.read_text())
    card = execution_view(science, spec)
    if card['scope_sha256'] != spec['resolved_scope_sha256']:
        raise ValueError('Resolved physical scope differs')
    return card
