"""Identity-only checks for the unchanged final and reserve source groups."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import time

MAX_JSON_BYTES = 256*2**20


def unpack(value):
    if isinstance(value, dict):
        return {k: unpack(v) for k, v in value.items()}
    if isinstance(value, list):
        return [unpack(v) for v in value]
    if isinstance(value, str) and value.lstrip().startswith(('{', '[')):
        try:
            return unpack(json.loads(value))
        except (ValueError, RecursionError):
            return value
    return value


def identity_locations(data, index, protected):
    hits, _ = index.document(unpack(data))
    return [row for row in hits if row['name'] in protected]


def collect_protected_outputs(project, index, protected, known_clear_documents=None):
    """Read all output JSON, including custom collection names; never decode media."""
    project = Path(project).resolve()
    output = (project/'outputs').resolve()
    if not output.is_dir():
        raise ValueError('Registered project output tree missing')
    result = dict(resolved_project=str(project), output_root=str(output), documents=[],
        identity_hits={}, read_errors=[], in_scope_aliases=[], files_observed=0,
        JSON_bytes_inventoried=0, prior_clear_documents_reused=0,
        videos_or_tensors_decoded=False, endpoint_values_exported=False)
    known = known_clear_documents or {}
    paths = []
    def walk_error(error):
        result['read_errors'].append(dict(path=str(error.filename), kind='OUTPUT_WALK_ERROR'))
    for directory, folders, files in os.walk(output, followlinks=False, onerror=walk_error):
        paths.extend(Path(directory)/name for name in sorted(folders+files))
    for path in sorted(paths):
        # Native input names can occur in a tensor filename as well as an MP4.
        name = index.match(path.name) or index.match(path.stem)
        if name in protected:
            result['identity_hits'].setdefault(name, []).append(dict(path=str(path), location='OUTPUT_PATH_NAME'))
        if path.is_symlink():
            try:
                target = path.resolve()
                if not target.exists() or not target.is_relative_to(output):
                    result['read_errors'].append(dict(path=str(path), kind='UNRESOLVED_OR_EXTERNAL_OUTPUT_LINK', target=str(target)))
                else:
                    result['in_scope_aliases'].append(dict(path=str(path), target=str(target)))
            except (OSError, RuntimeError):
                result['read_errors'].append(dict(path=str(path), kind='OUTPUT_LINK_ERROR'))
            continue
        if not path.is_file():
            continue
        result['files_observed'] += 1
        if not str(path).endswith(('.json', '.json.gz')):
            continue
        try:
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(2**20), b''):
                    digest.update(chunk)
            fingerprint = digest.hexdigest()
            if known.get(str(path)) == fingerprint:
                size = path.stat().st_size
                result['documents'].append(dict(path=str(path), sha256=fingerprint, bytes=size))
                result['JSON_bytes_inventoried'] += size
                result['prior_clear_documents_reused'] += 1
                continue
            if path.stat().st_size > MAX_JSON_BYTES:
                raise ValueError('JSON_SIZE_LIMIT')
            raw = path.read_bytes()
            # A size-limited decompression also bounds malformed compressed metadata.
            if path.suffix == '.gz':
                with gzip.open(path, 'rb') as stream:
                    payload = stream.read(MAX_JSON_BYTES+1)
            else:
                payload = raw
            if len(payload) > MAX_JSON_BYTES:
                raise ValueError('JSON_SIZE_LIMIT')
            hits = identity_locations(json.loads(payload), index, protected)
            if hashlib.sha256(raw).hexdigest() != fingerprint:
                raise ValueError('JSON_CHANGED_DURING_READ')
            result['documents'].append(dict(path=str(path), sha256=fingerprint, bytes=len(raw)))
            result['JSON_bytes_inventoried'] += len(raw)
            for hit in hits:
                result['identity_hits'].setdefault(hit['name'], []).append(
                    dict(path=str(path), location=hit['location'], kind=hit['kind']))
        except (OSError, ValueError, RecursionError, MemoryError) as error:
            result['read_errors'].append(dict(path=str(path), kind=type(error).__name__,
                size_limit=str(error)=='JSON_SIZE_LIMIT'))
    result['observed_unix'] = time.time()
    return result
