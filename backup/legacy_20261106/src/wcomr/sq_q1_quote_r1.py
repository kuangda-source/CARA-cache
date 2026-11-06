"""Whole Q1 planning allowance, including CPU work while the GPU is held.

Historical CPU costs anchor I/O/packing terms. GPU head time and the Ada
packing multiplier are explicit unmeasured allowances, not measured prices.
This file cannot reserve budget, admit hardware or authorize execution.
"""
import hashlib
import json
import math

from .sq_q1_spec_r1 import COUNTS

SCOPE = 'plans/cara_next_stage_20261028/sq/Q1_WHOLE_SCOPE_R1.json'
Q0 = 'reports/cara_sq_cpu_accepted_20261028.json'
HEAD = 'reports/cara_sq_q1_dual_cpu_accepted_r2_20261028.json'


def whole_quote(root, host):
    if host not in ('two_card','four_card'):
        raise ValueError('Registered host required for a whole Q1 quote')
    paths = (SCOPE,Q0,HEAD)
    raw = {name:(root/name).read_bytes() for name in paths}
    scope, q0, heads = (json.loads(raw[name]) for name in paths)
    if scope['scope_counts'] != COUNTS or scope['GPU_authorization']:
        raise ValueError('The unapproved Q1 scope or full denominator changed')
    resources = q0['resources']
    # Q0 encoded/decoded all six variants on ten unique anchor pairs. Q1's
    # inline two-anchor windows require 12*6*2=144 pair encodes/decodes.
    packet_work = (resources['worker_wall_seconds']-resources['hash_wall_seconds'])*144/60
    original_load = heads['hosts']['two_card']['head_metadata']['read_and_hash_wall_seconds']
    host_load = heads['hosts'][host]['head_metadata']['read_and_hash_wall_seconds']
    IO_factor = max(1.,host_load/original_load)
    CPU_factor = 1. if host=='two_card' else 2.
    terms = dict(context_import_startup_allowance=180., checkpoint_SHA_and_head_load=host_load,
        original_32_file_SHA_and_read_allowance=resources['hash_wall_seconds']*IO_factor*1.25,
        inline_144_pair_CPU_codec_work=packet_work*CPU_factor,
        FP32_M_roundtrip_24_pairs_allowance=120.*CPU_factor,
        CPU_GPU_transfer_allowance=180., original_C_or_dense_head_pairs_allowance=111*4.,
        input_state_rng_buffer_audit_allowance=12*30., output_and_GPU_release_allowance=120.)
    subtotal = math.fsum(terms.values())
    forecast = math.ceil(subtotal*1.25)/3600
    hard_limit = 1.25 if host=='two_card' else 2.
    if not 0<forecast<hard_limit:
        raise ValueError('Whole quote does not fit its proposed hard limit')
    return dict(schema='SQ_Q1_WHOLE_QUOTE_R1',host=host,
        status='PROPOSED_WHOLE_PLANNING_ALLOWANCE_NOT_GPU_PRICE_ACCEPTANCE',scope_counts=COUNTS,
        model_loads=1,loaded_model_scope='READOUT_ONLY_THREE_ORIGINAL_HEAD_TENSORS',
        terms_GPU_held_wall_seconds=terms,subtotal_seconds=subtotal,failure_allowance_fraction=.25,
        forecast_complete_GPUh=forecast,proposed_hard_limit_GPUh=hard_limit,timing_repeats=0,
        additional_C_or_D_hidden_head_pairs=15,formal_C_pairs=96,
        CPU_post_release=dict(wall_seconds_max=300,CPUs_max=2,allocated_vCPUh_max=1/6),
        Ada_B1_port_before_GPU=dict(required=host=='four_card',started=False,original_bytes=20_795_567_276,
            file_count=32,wall_seconds_max=7200,CPUs_max=2,allocated_vCPUh_max=4.,new_GPUh=0,
            destination_reserve_bytes_min=32*2**30,source_and_destination_SHA_required=True),
        resource_proposal=dict(GPU_devices=1,host_CPUs=2,host_RAM_GiB=16,
            private_input_logical_cap_GiB=8,CUDA_allocator_fraction_max=.5,
            output_reserved_GiB=1,independent_control_journal_MiB=48,output_file_MiB_max=64),
        basis=dict(Q0_unique_pairs=10,Q0_packet_variants=60,whole_inline_pair_variants=144,
            measured_Q0_non_hash_wall_seconds=resources['worker_wall_seconds']-resources['hash_wall_seconds'],
            host_checkpoint_IO_factor=IO_factor,host_CPU_codec_allowance_factor=CPU_factor,
            per_readout_pair_seconds_allowance=4.,measured_GPU_readout_unit_price=False,
            Ada_codec_work_measured=False,whole_card_native_quote_accepted=False),
        input_source_sha256={name:hashlib.sha256(value).hexdigest() for name,value in raw.items()},
        policy='Recover both-host intents; prefer admissible Ada, otherwise admissible A6000. Existing B1 raw is present only on A6000; Ada needs a separately verified immutable port before admission.',
        first_original_control_failure='Stop subsequent codecs and all selection; settle the original bill. No tolerance fitting, replays or automatic retries.',
        scheduling='After actual unique launch, schedule halfway at forecast/2 from actual start and terminal at forecast plus release/scoring allowance; update existing checks if ETA changes.',
        GPU_authorization=False,GPU_ready=False,new_GPU_submissions=0,budget_reserved_GPUh=0,
        ledger_writes=0,cumulative_cap_GPUh=226,unknown_liability_GPUh_preserved=16.5)
