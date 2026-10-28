"""The matched-reference boundary distinguishes content from solver budget."""
from .cara_fast_spec_r1 import digest


def comparison_input_digest(request):
    # Native-k deliberately changes num_steps. Dataset partition is bookkeeping;
    # all conditioning, seed, geometry and prompt fields remain in the identity.
    return digest({k:v for k,v in request.items() if k not in ('num_steps','partition')})


def validate_pair_identities(config):
    ids = [row['id'] for row in config['pairs']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate physical scoring pair')
    for row in config['pairs']:
        reference, candidate = row['reference'], row['candidate']
        if reference['role'] != 'NATIVE35':
            raise ValueError('Matched full Native35 reference required')
        for key in ('member','seed','host','gpu_uuid','model_sha256',
                    'comparison_input_sha256','precision','scope_sha256'):
            if candidate[key] != reference[key]:
                raise ValueError('Mismatched reference identity: '+key)
        if candidate['scope_sha256'] != config['scope_sha256']:
            raise ValueError('Mixed card scopes')
        for descriptor in (candidate, reference):
            value = descriptor['execution_request_sha256']
            if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
                raise ValueError('Separate complete execution-request SHA required')
    return ids
