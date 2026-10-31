"""Cross-allocation identities preserve both original descriptor scopes."""
from .cara_s_uniform_endpoint_plan_r1 import BUDGET_ROLE,NEW_ROLES,REUSED_ROLES
from .policy_price_terminal_r1 import require

SOURCE='src/wcomr/cara_s_endpoint_scoring_manifest_r1.py'


def validate_pair_identities(manifest):
    seven=manifest.get('endpoint7',False)
    new_roles=NEW_ROLES+(BUDGET_ROLE,)+(('F19_RISKSWAP_C',) if seven else ())
    positions_required=28 if seven else 24
    require(manifest['schema']=='CARA_ENDPOINT_CROSS_ALLOCATION_SCORING_R1'
            and manifest['GPU_released'] is True and manifest['identity_controls_passed']==(13 if seven else 9)
            and manifest['analysis_scope_sha256']!=manifest['original_B36_scope_sha256'],
            'Released cross-allocation identity controls required')
    pairs=manifest['pairs'];ids=[p['id'] for p in pairs]
    representative=manifest['budget_role_representative']
    require((representative==BUDGET_ROLE if seven else representative in new_roles)
            and manifest['physical_paths']==(46 if seven else 32 if representative==BUDGET_ROLE else 25)
            and len(pairs)==(16 if seven else 12 if representative==BUDGET_ROLE else 8),
            'Frozen physical equivalence denominator differs')
    require(len(ids)==len(set(ids))==manifest['unique_new_scoring_pairs']
            and len(ids) in ((16,) if seven else (8,12)),'Complete unique new scoring denominator required')
    members=manifest['members'];references=manifest['original_references']
    require(len(members)==len(set(members))==4 and set(references)==set(members),
            'Four original Native references required')
    for pair in pairs:
        candidate,reference=pair['candidate'],pair['reference']
        require(reference==references[candidate['member']] and reference['role']=='NATIVE35'
                and reference['scope_sha256']==manifest['original_B36_scope_sha256']
                and candidate['scope_sha256']==manifest['analysis_scope_sha256']
                and candidate['role']==candidate['concrete_role'] in new_roles,
                'Preserve original reference scope and new candidate identity')
        for field in ('member','seed','host','gpu_uuid','model_sha256','comparison_input_sha256','precision'):
            require(candidate[field]==reference[field],'Mismatched cross-allocation reference: '+field)
        for side in (candidate,reference):
            for field in ('sha256','execution_request_sha256','argument_file_sha256'):
                value=side[field]
                require(isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value),
                        'Original descriptor SHA required: '+field)
    reused=manifest['reused_rows'];positions=manifest['formal_positions']
    require(len(reused)==len({r['id'] for r in reused})==12 and len(positions)==positions_required
            and {(r['member'],r['role']) for r in positions}==
                {(m,r) for m in members for r in REUSED_ROLES+new_roles},
            f'Complete{positions_required} logical positions and12 unchanged original rows required')
    old={r['id']:r for r in reused};fresh={p['id']:p for p in pairs}
    require(len({r['id'] for r in positions})==positions_required,'Unique logical position identities required')
    for position in positions:
        if position['mode']=='REUSE_COMPLETE_SCORE':
            row=old[position['score_id']]
            require(position['role'] in REUSED_ROLES and row['role']==position['role']
                    and row['member']==position['member'] and row['reference']==references[position['member']]
                    and row['candidate']['scope_sha256']==manifest['original_B36_scope_sha256'],
                    'Original metric identity cannot be projected into the new scope')
        else:
            require(position['mode']=='GENERATE_AND_SCORE' and position['role'] in new_roles,
                    'Unknown logical score mode')
            pair=fresh[position['score_id']]
            expected=manifest['budget_role_representative'] if position['role']==BUDGET_ROLE else position['role']
            require(pair['candidate']['member']==position['member'] and pair['candidate']['role']==expected
                    and position['counts_as_independent_sample_from_alias'] is False,
                    'Frozen physical metric alias differs')
    require({r['score_id'] for r in positions if r['mode']=='GENERATE_AND_SCORE'}==set(ids)
            and {r['score_id'] for r in positions if r['mode']=='REUSE_COMPLETE_SCORE'}==set(old),
            'No unused or missing scoring pairs allowed')
    return ids
