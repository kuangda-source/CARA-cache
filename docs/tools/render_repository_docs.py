#!/usr/bin/env python3
"""Render repository navigation from saved evidence; never connect or dispatch.

Inputs: project_status.json, scientific registry, naming registry, templates,
and immutable local receipts. --check is read-only and detects output drift.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
STATUS = 'docs/project_status.json'
MASTER = 'paper/experiment_master_table.json'
MAPPING = 'paper/internal_to_paper_mapping.json'
ARCHIVE = 'docs/archive/20261022_before_navigation/manifest.json'


def load(path):
    return json.loads((ROOT / path).read_text())


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def digest(data):
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def link(path, title):
    return f'[{title}](repo:{path})'


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def local_time(unix):
    return datetime.fromtimestamp(unix, ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')


def resolve_ref(ref, master):
    return master['source_refs'].get(ref, ref)


def refs(items, master=None):
    return ' · '.join(link(resolve_ref(p, master) if master else p, f'证据{i + 1}')
                      for i, p in enumerate(items))


def localize(text, target):
    def replace(match):
        raw = match.group(1)
        path, sep, anchor = raw.partition('#')
        relative = os.path.relpath(ROOT / path, (ROOT / target).parent)
        return '](' + relative + (sep + anchor if sep else '') + ')'
    return re.sub(r'\]\(repo:([^\)]+)\)', replace, text)


def build():
    status, master, mapping = load(STATUS), load(MASTER), load(MAPPING)
    launch, observation = load(status['launch_ref']), load(status['observation_ref'])
    cpu = load(status['cpu_acceptance_ref'])
    # Refuse mixed-run snapshots instead of publishing a plausible but wrong status.
    for key in ('launch_id', 'run_id', 'source_revision', 'gpu_uuid', 'config_sha256', 'scope_counts'):
        if observation['launch'][key] != launch[key]:
            raise ValueError(f'observation/launch identity mismatch: {key}')
    if cpu['source_revision'] != launch['source_revision'] or not cpu['production_CPU_accepted']:
        raise ValueError('CPU acceptance does not bind the launched source')
    stamp = datetime.fromisoformat(status['evidence_observed_at']).timestamp()
    if abs(stamp - observation['observed_unix']) > 0.00001:
        raise ValueError('evidence timestamp does not match the saved observation')
    rows = master['rows']
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('duplicate scientific experiment IDs')
    by_id = {r['id']: r for r in rows}
    for row in rows:
        for ref in row['evidence_refs'] + row['reader']['evidence_refs']:
            path = resolve_ref(ref, master)
            if '://' not in path and not (ROOT / path).exists():
                raise ValueError(f'missing evidence: {row["id"]}: {path}')
    active = by_id[status['active_experiment_id']]
    active['state'] = status['active_state']
    running = 'RUNNING' in status['active_state']
    active['reader']['status'] = 'GPU运行中（已记录快照）' if running else status['active_state_zh']
    scope = launch['scope_counts']
    health = observation.get('health')
    if health is None and observation.get('mode') == 'gpu-terminal':
        terminal_rows = observation['runner']['runs']
        health = dict(registered_paths=scope['total_paths'],
            completed_paths=sum(r['status'] in ('COMPLETE', 'VIDEO_REJECTED', 'TEXT_REJECTED') for r in terminal_rows),
            running_paths=sum(r['status'] == 'RUNNING' for r in terminal_rows),
            failed_paths=sum(r['status'] == 'TECH_FAILED' for r in terminal_rows),
            not_reached_paths=scope['total_paths'] - len(terminal_rows),
            active_path=next((r['id'] for r in terminal_rows if r['status'] == 'RUNNING'), None))
        if status.get('terminal_acceptance_ref'):
            accepted = load(status['terminal_acceptance_ref'])
            if (accepted['capture_sha256'] != digest((ROOT / status['observation_ref']).read_bytes())['sha256']
                    or accepted.get('full_protocol_accepted') is not True):
                raise ValueError('Terminal status must bind actual complete acceptance')
    if health is None:
        raise ValueError('A saved technical health or original terminal runner is required')
    progress = (f"{health['completed_paths']}/{health['registered_paths']}路径完成、"
                f"{health['running_paths']}运行、{health['not_reached_paths']}未到达、"
                f"{health['failed_paths']}失败")
    if health.get('active_path'):
        progress += f"；当前路径`{health['active_path']}`"
    active['reader']['result'] = f"生产CPU已接受；GPU启动于{local_time(launch['started_unix'])}。快照：{progress}。"
    if status.get('terminal_acceptance_ref'):
        active['reader']['result'] = (f"原完整卡已接受；实际{accepted['finance']['actual_GPUh']:.6f} GPUh。"
                                      f"终态：{progress}；独立价格门槛见下一步。")
    active['evidence_or_planned_scope'] = active['reader']['result']
    master['status_counts'] = {state: sum(r['state'] == state for r in rows)
                               for state in sorted({r['state'] for r in rows})}
    master['operation_policy'].update(
        current_running_card=active['id'] if running else None,
        current_running_cards=[active['id']] if running else [],
        snapshot_observed_at=status['evidence_observed_at'],
        active_launch_ref=status['launch_ref'])
    actions = '\n'.join([
        '| 动作 | 做什么 | 作用 |', '|---|---|---|',
        '| **C：直接缓存读出** | 使用已有缓存与原WorldCache读出链 | 节省深层计算 |',
        '| **A：修正缓存读出** | 用当前浅层增量与过去真实D锚点修正，CFG两支共享强度 | 以较小额外成本降低读出误差 |',
        '| **D：完整刷新** | 两CFG支均进行完整深层计算，更新真实锚点 | 支付计算成本，获得当前真实深层结果 |'])
    schedule = '；'.join(f"{c['kind']}：**{c['scheduled_local']}**" for c in status['next_checks'])
    snapshot = (f"**已保存的实验观测：{status['evidence_observed_at']}（Asia/Shanghai）。** "
                f"{status['active_state_zh']}。{progress}。\n\n"
                f"范围：{scope['requests']} CAL / {scope['formal_source_time_cells']}正式区间格 / "
                f"{scope['total_paths']}完整路径（{scope['formal_paths']}正式+{scope['full_warmup_paths']}warm）/ "
                f"{scope['total_collected_source_time_cells']}总格 / {scope['total_readout_pair_trials']}读出试验；"
                f"整卡上限{launch['billed_limit_GPUh']} GPUh。{schedule}。\n\n"
                f"{link(status['run_report_ref'], '本卡完整记录')} · {link(status['observation_ref'], '观测原件')} · "
                f"{link('research/02_CURRENT_STATE.md', '当前状态')}。{status['snapshot_note']}")
    followup = status.get('price_refresh_CPU')
    if followup:
        fl = load(followup['launch_ref'])
        fo = load(followup['observation_ref'])
        if fo['launch'] != fl or fo['registration']['source_revision'] != fl['source_revision']:
            raise ValueError('Price CPU source/launch differs from its saved observation')
        phase = followup['status_zh']
        active['reader']['result'] += '价格补测：' + phase + '。'
        active['evidence_or_planned_scope'] = active['reader']['result']
        snapshot += (f"\n\n**当前独立价格补测：{phase}。** "
                     f"CPU启动于{local_time(fl['started_unix'])}，最近观测{local_time(fo['observed_unix'])}。"
                     f"{link(followup['launch_ref'], '价格CPU启动原件')} · "
                     f"{link(followup['observation_ref'], '价格CPU观测')}。"
                     "新GPU提交为0；完整价格卡保持10路径/1624正式格/24360读出、11.5 GPUh上限。")
    run_rows = [('实验ID', active['id']), ('run', launch['run_id']), ('launch ID', launch['launch_id']),
                ('运行源码', launch['source_revision']), ('stage', launch['stage']),
                ('GPU UUID', launch['gpu_uuid']), ('容器', launch['container']),
                ('启动时间', local_time(launch['started_unix'])),
                ('注册SHA256', launch['registration_sha256']), ('配置SHA256', launch['config_sha256']),
                ('CPU证明SHA256', launch['production_CPU_sha256'])]
    for role, identity in observation['original_processes'].items():
        saved_key = {'supervisor': 'supervisor_identity', 'runner': 'child_identity', 'post': 'post_identity'}.get(role)
        saved = observation.get('supervisor', {}).get(saved_key, {})
        ticks = identity.get('start_ticks')
        if ticks is None and saved.get('pid') == identity['pid']:
            ticks = saved.get('start_ticks')
        ended = '（已退出）' if observation.get('original_live_handles', {}).get(role) is False else ''
        run_rows.append((role, f"PID {identity['pid']} / start_ticks {ticks}{ended}"))
    run_details = '| 字段 | 冻结身份 / 已记录状态 |\n|---|---|\n' + '\n'.join(
        f'| {k} | `{v}` |' for k, v in run_rows)
    run_details += (f"\n\n{link(status['launch_ref'], '唯一启动原件')} · "
                    f"{link(status['cpu_acceptance_ref'], 'CPU完整接受')} · "
                    f"{link(status['admission_ref'], '准入与检查安排')}\n\n"
                    f"{scope['ordinary_pairs']}普通pairs / {scope['ordinary_CFG_calls']}CFG / {scope['loads']}次模型加载。"
                    f"原规划{launch['forecast_GPUh']:.6f} GPUh。")
    if status.get('terminal_acceptance_ref'):
        run_details += (f"实际已结算{accepted['finance']['actual_GPUh']:.6f} GPUh；"
                        f"{link(status['terminal_acceptance_ref'], 'GPU完整接受')}。")
    else:
        run_details += '规划为估算，终态按完整实际费用结算。'
    if followup:
        run_details += (f"\n\n**当前价格CPU任务**：`{fl['stage']}`，源码`{fl['source_revision']}`；"
                        f"PID {fl['identity']['pid']} / start_ticks {fl['identity']['start_ticks']}；"
                        f"容器`{fl['container']}`。实际状态：{phase}。"
                        "原1624的已接受身份和费用列在上表，不作为新补测的启动授权。")
    headlines = '\n'.join(f"- **{f['title']}**（{f['short_scope']}）：{f['result']} {refs(f['refs'])}"
                           for f in status['headline_results'])
    details = '\n\n'.join(f"### {i+1}. {f['title']}\n\n{f['result']}\n\n{f['scope']} {refs(f['refs'])}"
                             for i, f in enumerate(status['headline_results']))
    queue = '| 顺序 | 当前阶段 | 下一项验收 / 动作 |\n|---|---|---|\n' + '\n'.join(
        f"| {id} | {cell(by_id[id]['reader']['title'])}：{cell(by_id[id]['reader']['status'])} | "
        f"{cell(by_id[id]['reader']['next_action'])} |" for id in status['next_sequence'])
    groups = [('现行自动生成器路线', lambda id: id.startswith('PG-')),
              ('机制与历史方法开发', lambda id: id.startswith('D') or id == 'R01'),
              ('共同评价、归因与后续卡', lambda id: id.startswith('N') or id == 'Z01'),
              ('独立探索', lambda id: id.startswith('X-')),
              ('v6设计与现行队列的关系', lambda id: id.startswith('REV-'))]
    tables = []
    for name, predicate in groups:
        lines = [f'## {name}', '', '| ID · 实验 / 状态 | 结果或登记范围 | 下一步 | 优先证据 |', '|---|---|---|---|']
        for row in rows:
            if not predicate(row['id']):
                continue
            r, id = row['reader'], row['id']
            lines.append(f"| <a id=\"{id.lower()}\"></a>**{id} · {cell(r['title'])}**<br>{cell(r['status'])} | "
                         f"{cell(r['result'])} | {cell(r['next_action'])} | {refs(r['evidence_refs'], master)} |")
        tables.append('\n'.join(lines))
    mapping_table = '| 稳定ID | 论文/说明名 | 内部别名 | 实现入口 |\n|---|---|---|---|\n' + '\n'.join(
        f"| `{e['id']}` | {cell(e.get('paper_name_zh', e['paper_name_en']))} | "
        f"{cell(', '.join(e.get('internal_aliases', [])) or '—')} | "
        f"{refs(e.get('implementation_paths', [])[:2]) or '见机器映射'} |" for e in mapping['entries'])
    values = dict(actions=actions, snapshot=snapshot, run_details=run_details, headlines=headlines,
                  results_detail=details, research_summary=status['research_summary'], queue=queue,
                  row_count=str(len(rows)), master_tables='\n\n'.join(tables), mapping_table=mapping_table)
    outputs = {}
    for template in sorted((ROOT / 'docs/templates').glob('*.md')):
        target = template.name.replace('__', '/')
        body = template.read_text()
        for key, value in values.items():
            body = body.replace('{{' + key + '}}', value)
        if re.search(r'\{\{\w+\}\}', body):
            raise ValueError(f'unresolved template variable: {template.name}')
        notice = '<!-- Generated by docs/tools/render_repository_docs.py; edit canonical JSON or docs/templates/, then render. -->\n\n'
        outputs[target] = localize(notice + body, target).encode()
    # History index uses Git paths, without reading or hydrating hundreds of old files.
    tracked = subprocess.check_output(['git', 'ls-files', '--', 'research/*.md'], cwd=ROOT, text=True).splitlines()
    def order(path):
        match = re.match(r'(\d+)_', Path(path).name)
        return (0, -int(match.group(1))) if match else (1, path)
    history = '# 完整研究记录索引\n\n'
    history += f'共{len(tracked)}份已跟踪研究Markdown，按编号倒序；编号表示记录顺序，不表示全部独立实验。'
    history += '历史文件中的“当前/下一步”指其记录当时；最新状态以[当前状态](repo:research/02_CURRENT_STATE.md)为准。\n\n'
    history += '\n'.join('- ' + link(p, Path(p).stem.replace('_', ' ')) for p in sorted(tracked, key=order)) + '\n'
    outputs['docs/HISTORY_INDEX.md'] = localize(history, 'docs/HISTORY_INDEX.md').encode()
    # Existing hashes bind historical evidence; only navigation files changed by this renderer are refreshed.
    for path, data in outputs.items():
        if path in mapping['file_bindings']:
            mapping['file_bindings'][path] = digest(data)
    for binding in master['source_bindings'].values():
        if binding['path'] in outputs:
            binding.update(digest(outputs[binding['path']]))
    outputs[MAPPING] = encoded(mapping)
    master['latest_mapping_sha256'] = digest(outputs[MAPPING])['sha256']
    outputs[MASTER] = encoded(master)
    return outputs


def validate_archive():
    manifest = load(ARCHIVE)
    for entry in manifest['files']:
        actual = digest((ROOT / entry['archived_path']).read_bytes())
        if any(actual[k] != entry[k] for k in ('sha256', 'bytes')):
            raise ValueError(f'archived original modified: {entry["archived_path"]}')


def validate_links(outputs):
    for target, data in outputs.items():
        if not target.endswith('.md'):
            continue
        for raw in re.findall(r'\]\(([^)]+)\)', data.decode()):
            path = raw.split('#', 1)[0]
            if path and '://' not in path and not (ROOT / target).parent.joinpath(path).exists():
                if os.path.relpath((ROOT / target).parent / path, ROOT) not in outputs:
                    raise ValueError(f'missing document link: {target} -> {raw}')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true', help='read-only: fail on stale generated documents or broken evidence')
    args = ap.parse_args()
    validate_archive()
    outputs = build()
    validate_links(outputs)
    changed = [p for p, data in outputs.items() if not (ROOT / p).exists() or (ROOT / p).read_bytes() != data]
    if args.check and changed:
        print('STALE generated files:\n' + '\n'.join(changed))
        return 1
    if not args.check:
        for path in changed:
            (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / path).write_bytes(outputs[path])
    print(f'{"PASS" if args.check else "RENDERED"}: {len(outputs)} outputs; {len(changed)} changed; archive hashes and evidence links valid; no server/GPU access.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
