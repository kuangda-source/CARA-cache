"""Identity-only project output inventory; no outcome or timing export."""
import hashlib
import json
import os
from pathlib import Path
import time

CATALOG_KEYS = {'dataset_catalog', 'benchmark_catalog', 'source_catalog', 'candidate_catalog',
    'eligible_pools', 'identity_hits', 'local_identity_hits', 'remote_identity_hits',
    'excluded_group_members', 'engineering_excluded_groups', 'protected_groups',
    'group_members', 'matching_output_paths', 'source_sha256', 'runtime_source_sha256', 'payload_sha256'}
JSON_NAMES = {'receipt.json', 'runner.json', 'CPU-final-results.json', 'results.json',
              'summary.json', 'generation.json', 'input.json', 'request.json', 'metrics.json', 'scores.json'}


class Identities:
    def __init__(self, records):
        self.records = {r['name']: r for r in records}
        self.by_hash = {r['prompt_sha256']: r['name'] for r in records}
        if len(self.records) != len(records) or len(self.by_hash) != len(records):
            raise ValueError('Unique original benchmark names and prompt hashes required')
        self.prefixes = {}
        for name in sorted(self.records, key=lambda n: (-len(n), n)):
            self.prefixes.setdefault(name.split('_')[0], []).append(name)

    def match(self, value):
        if not isinstance(value, str): return None
        if value in self.by_hash: return self.by_hash[value]
        hashed = hashlib.sha256(value.encode()).hexdigest()
        if hashed in self.by_hash: return self.by_hash[hashed]
        for name in self.prefixes.get(value.split('_')[0], []):
            if value == name or value.startswith(name + '_') or value == name + '.json' or value == name + '.mp4':
                return name
        return None

    def whole_catalog(self, value):
        return (isinstance(value, list) and len(value) == len(self.records)
                and all(isinstance(r, dict) and self.records.get(r.get('name')) == r for r in value)
                and len({r['name'] for r in value}) == len(self.records))

    def document(self, data):
        hits, skipped = [], []
        def walk(value, at='$'):
            if self.whole_catalog(value):
                skipped.append(dict(location=at, reason='UNEXECUTED_WHOLE_SOURCE_CATALOG')); return
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in CATALOG_KEYS:
                        skipped.append(dict(location=at + '.' + key, reason='DECLARED_CATALOG_OR_IDENTITY_METADATA'))
                        continue
                    name = self.match(key)
                    if name: hits.append(dict(name=name, location=at + '.' + key, kind='IDENTITY_KEY'))
                    walk(item, at + '.' + key)
            elif isinstance(value, list):
                for index, item in enumerate(value): walk(item, at + '[' + str(index) + ']')
            elif isinstance(value, str):
                name = self.match(value)
                if name: hits.append(dict(name=name, location=at, kind='NAME_OR_PROMPT_IDENTITY'))
                else:
                    for part in Path(value).parts:
                        name = self.match(part)
                        if name: hits.append(dict(name=name, location=at, kind='PATH_COMPONENT_IDENTITY'))
        walk(data)
        return hits, skipped


def collect_outputs(project, records):
    """Only outputs: do not scan a vendor/input catalog or every old config."""
    project = Path(project).resolve(); output = (project / 'outputs').resolve()
    if not output.is_dir(): raise ValueError('Original project output tree missing')
    index = Identities(records)
    result = dict(identity_hits={}, documents=[], skipped_identity_metadata=[], read_errors=[],
        matching_output_paths=[], scope='PROJECT_OUTPUTS_NAMES_AND_DECLARED_RESULT_JSON_NOT_EXTERNAL_OR_UNRECORDED_RUNS',
        no_endpoint_or_timing_values_extracted=True, videos_or_tensors_decoded=False,
        GPU_submissions=0, ledger_written=False)
    paths = []
    def walk_error(error):
        result['read_errors'].append(dict(path=str(error.filename), kind='OUTPUT_WALK_ERROR', error=str(error)))
    for directory, names, files in os.walk(output, followlinks=False, onerror=walk_error):
        paths.extend(Path(directory) / name for name in sorted(names + files))
    for path in sorted(paths):
        name = index.match(path.name)
        if name:
            result['matching_output_paths'].append(str(path))
            result['identity_hits'].setdefault(name, []).append(dict(path=str(path), location='OUTPUT_PATH_NAME'))
        if path.is_symlink():
            try:
                target = path.resolve()
                if not target.exists():
                    result['read_errors'].append(dict(path=str(path), kind='MISSING_OUTPUT_LINK_TARGET',
                        target=str(target)))
                elif not target.is_relative_to(output):
                    result['read_errors'].append(dict(path=str(path), kind='EXTERNAL_OUTPUT_LINK_REQUIRES_EXPLICIT_SCOPE',
                        target=str(target)))
                else:
                    result['skipped_identity_metadata'].append(dict(path=str(path), location='OUTPUT_LINK',
                        reason='IN_SCOPE_ALIAS_TARGET_ALREADY_WALKED'))
            except Exception as error:
                result['read_errors'].append(dict(path=str(path), kind='OUTPUT_LINK_ERROR', error=str(error)))
            continue
        if not path.is_file() or path.suffix != '.json' or (path.name not in JSON_NAMES and not name): continue
        try:
            raw = path.read_bytes(); data = json.loads(raw)
            hits, skipped = index.document(data)
            result['documents'].append(dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
            for hit in hits:
                result['identity_hits'].setdefault(hit['name'], []).append(
                    dict(path=str(path), location=hit['location'], kind=hit['kind']))
            result['skipped_identity_metadata'].extend(dict(path=str(path), **row) for row in skipped)
        except Exception as error:
            result['read_errors'].append(dict(path=str(path), error_type=type(error).__name__, error=str(error)))
    result['observed_unix'] = time.time()
    return result


def registered_jobs(pool, process_reader):
    """Report only original job identity/terminal state, never its cost fields."""
    jobs = []; complete = True
    for name, job in pool['jobs'].items():
        original = dict(pid=job['supervisor_pid'], start_ticks=job['supervisor_start_ticks'])
        actual = process_reader(original['pid'])
        alive = actual['state'] not in (None, 'Z', 'X') and actual['start_ticks'] == original['start_ticks']
        terminal = job['status'] == 'SETTLED' and not alive
        jobs.append(dict(job_id=name, original_supervisor=original,
            observed=dict(pid=actual['pid'], state=actual['state'], start_ticks=actual['start_ticks']),
            registered_status=job['status'], original_supervisor_alive=alive, terminal=terminal))
        complete = complete and terminal
    return dict(all_registered_GPU_jobs_terminal=complete, original_jobs=jobs)
