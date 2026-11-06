"""The final input adapter preserves source conditioning and every request slot."""
import copy
import json
import unittest

from wcomr.frozen_shared_inputs_r1 import bind_selected, inspect_source, sha_bytes


def fixture():
    sources, raw = [], {}
    methods = ['NATIVE35', 'NATIVE26', 'NATIVE18', 'WC_DEFAULT', 'RA_DEFAULT',
               'A_NO_P', 'TABLE_PHASE_H1', 'FRONT_DENSE_C', 'FRONT_DENSE_A', 'FIXED_PLAIN']
    for category in ('av', 'human', 'misc', 'robot'):
        for index in range(2):
            name = f'SYNTHETIC_{category}_{index}'
            prompt = 'Synthetic exact source text ' + name + '\n'
            original = dict(name=name, prompt=prompt, negative_prompt='Synthetic unchanged negative\n',
                            inference_type='text2world', seed=0, guidance=7,
                            num_output_frames=93, resolution='432,768')
            sources.append(dict(name=name, category=category, prompt_sha256=sha_bytes(prompt.encode()),
                                group_members=[name]))
            raw[name] = (json.dumps(original, ensure_ascii=False) + '\n').encode()
    cases = [dict(id=s['name'] + '_PAPER_COMMON_seed' + str(seed), prompt_id=s['name'],
                  seed=seed, category=s['category']) for s in sources for seed in (17, 43)]
    selection = dict(status='FINAL_INPUT_SELECTION_KERNEL_RESULT_REQUIRES_PHYSICAL_INPUT_BINDING',
                     selected_sources=sources, cases=cases, method_ids=methods)
    return selection, raw


class InputBindingControls(unittest.TestCase):
    def test_all_arguments_and_source_bytes_unchanged(self):
        selected, raw = fixture()
        original = copy.deepcopy(raw)
        result = bind_selected(selected, raw)
        self.assertEqual(raw, original)
        self.assertEqual(len(result['argument_variants']), 160)
        self.assertEqual(len(result['execution_plan']), 180)
        self.assertEqual(result['planned_scope_counts']['ordinary_pairs'], 6012)
        for row in result['argument_variants']:
            self.assertEqual(row['changed_original_fields'], ['name', 'num_steps', 'seed'])
            args = row['arguments']
            self.assertTrue(args['prompt'].endswith('\n'))
            self.assertEqual(args['negative_prompt'], 'Synthetic unchanged negative\n')
            self.assertIn(args['seed'], (17, 43))
        self.assertEqual({r['arguments']['num_steps'] for r in result['argument_variants']}, {18, 26, 35})
        self.assertFalse(result['actual_InferenceArguments_CPU_accepted'])
        self.assertFalse(result['physical_input_manifest_written'])

    def test_source_identity_prompt_and_header_mismatch(self):
        selected, raw = fixture()
        source = selected['selected_sources'][0]
        for field, bad in [('name', 'other'), ('prompt', 'changed'), ('guidance', 8),
                           ('resolution', '768,432'), ('num_output_frames', 92), ('seed', 17)]:
            value = json.loads(raw[source['name']]);value[field] = bad
            with self.assertRaises(ValueError): inspect_source(source, json.dumps(value).encode())

    def test_missing_bytes_changed_seed_or_shrunk_scope_rejected(self):
        selected, raw = fixture()
        short = dict(raw);short.pop(next(iter(short)))
        with self.assertRaises(ValueError): bind_selected(selected, short)
        bad = copy.deepcopy(selected);bad['cases'][0]['seed'] = 0
        with self.assertRaises(ValueError): bind_selected(bad, raw)
        bad = copy.deepcopy(selected);bad['method_ids'].remove('FRONT_DENSE_C')
        with self.assertRaises(ValueError): bind_selected(bad, raw)

    def test_no_image_switch_extra_fields_or_path_traversal(self):
        selected, raw = fixture();source = selected['selected_sources'][0]
        value = json.loads(raw[source['name']]);value['image_path'] = '/SYNTHETIC/image.jpg'
        with self.assertRaises(ValueError): inspect_source(source, json.dumps(value).encode())
        bad = {**source, 'name': '../not-a-source'}
        with self.assertRaises(ValueError): inspect_source(bad, raw[source['name']])


if __name__ == '__main__':
    unittest.main()
