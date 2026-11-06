"""Technical decoder-policy acceptance, with an unchanged denoiser reference."""
from .stage_witness import compare_stages
from .decoder_policy import compare_decoder_identity


def summarize_policy(left,right,reference):
    for receipt in [left,right]:
        assert receipt['status']=='STAGE_WITNESS_ACCEPTED_SINGLE_FRESH_PROCESS'
        assert receipt['decoder_policy']['enabled'] is True
        calls=receipt['decoder_calls']
        assert calls and len(calls)==sum(e['stage']=='decode_input' for e in receipt['events'])
        for call in calls:
            assert all(compare_decoder_identity(call['before'],call['after']).values())
            assert call['flags_before']==call['flags_after']
            active=dict(call['flags_before'],cudnn_benchmark=False,cudnn_deterministic=True)
            assert call['flags_inside']==active,'Unexpected backend policy change'
        assert len(receipt['forward_output_sha256'])==72 and len(receipt['decoded_rgb'])==93
    assert left['pid']!=right['pid']
    assert left['source_sha256']==right['source_sha256']
    assert left['decoder_checkpoint']==right['decoder_checkpoint']
    assert left['decoder_calls']==right['decoder_calls'],'Decoder state differs across fresh processes'
    for key in ['forward_output_sha256','block_counts','trace','cache_end_sha256','sampling','sample']:
        assert left[key]==right[key]==reference[key],'Changed official reference '+key
    for receipt in [left,right]:
        assert [e for e in receipt['events'] if e['stage'] in ['sample_return','decode_input']]==[
            e for e in reference['events'] if e['stage'] in ['sample_return','decode_input']],'Changed final latent'
    comparison=compare_stages(left,right)
    result={'status':'LOCAL_DECODE_POLICY_REPRODUCTION_PASS' if comparison['status']=='EXACT_PIPELINE_REPRODUCTION_TWO_FRESH_PROCESSES' else 'LOCAL_DECODE_POLICY_REPRODUCTION_NOT_ESTABLISHED',
            'comparison':comparison,'decoder_identity_identical':True,'flags_restored':True,
            'official_denoiser_and_latent_reference_identical':True,
            'scope':'Two fresh engineering processes only; state hashing and scoped cuDNN policy jointly differ from previous witness protocol. Not isolated causal proof, global determinism, quality, method gain or clean latency.'}
    return result
