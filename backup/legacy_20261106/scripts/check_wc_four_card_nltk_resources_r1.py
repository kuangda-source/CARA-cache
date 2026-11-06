#!/usr/bin/env python3
"""Run the real offline Cosmos Blocklist path with GPUs hidden; no neural inference."""
import argparse
import hashlib
import json
import os
from pathlib import Path

from four_card_bank24_execution_tools_r1 import verify_nltk_resources


def check(project, config_path):
    resource = verify_nltk_resources(project)
    assert os.environ.get('NLTK_DATA') == resource['root']
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    assert os.environ.get('NVIDIA_VISIBLE_DEVICES') == 'void'
    assert os.environ.get('HF_HUB_OFFLINE') == '1'
    assert not list(Path('/dev').glob('nvidia*'))
    import nltk
    import torch
    from cosmos_predict2._src.imaginaire.auxiliary.guardrail.blocklist.blocklist import Blocklist
    from cosmos_predict2._src.imaginaire.auxiliary.guardrail.common.core import GuardrailRunner
    assert not torch.cuda.is_initialized()
    assert Path(nltk.data.path[0]) == Path(resource['root'])
    token_path = Path(str(nltk.data.find('tokenizers/punkt_tab/english/')))
    assert token_path.resolve().is_relative_to(Path(resource['root']))
    assert nltk.word_tokenize('Children are playing in a park.')
    assert nltk.WordNetLemmatizer().lemmatize('children') == 'child'
    blocklist = Blocklist()
    runner = GuardrailRunner(safety_models=[blocklist])
    config = json.loads(config_path.read_text())
    assert len(config['requests']) == 6
    checks = []
    for request in config['requests']:
        safe, _ = runner.run_safety_check(request['prompt'])
        assert safe, 'Frozen BANK24 prompt rejected by the original Blocklist'
        checks.append({'request': request['name'], 'safe': safe,
                       'prompt_sha256': hashlib.sha256(request['prompt'].encode()).hexdigest()})
    # Exercise the installed policy's rejection branch, without changing its rules.
    candidates = [w for w in blocklist.blocklist_words if w.strip() and w not in blocklist.whitelist_words]
    rejected = any(not runner.run_safety_check(w)[0] for w in candidates[:8])
    assert rejected, 'Installed Blocklist negative control was not rejected'
    assert not torch.cuda.is_initialized()
    return {'status': 'REAL_COSMOS_BLOCKLIST_CPU_PASS', 'resources': resource,
            'nltk_version': nltk.__version__, 'tokenizer_root': str(token_path),
            'frozen_requests': checks, 'wordnet_pass': True, 'blocked_control_pass': True,
            'CUDA_initialized': False, 'neural_guardrail_tested': False,
            'video_generation_tested': False, 'guardrail_disabled': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--config', required=True, type=Path)
    args = parser.parse_args()
    print('WC_NLTK_CHECK_JSON=' + json.dumps(check(args.project, args.config)))
