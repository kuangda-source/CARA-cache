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
        if status.get('CAL66_GPU'):
            admission=load(status['CAL66_GPU']['admission_ref'])
            if not admission.get('actual_unique_runner_accepted') or admission['launch_id']!=launch['launch_id']:
                raise ValueError('Loading snapshot requires original unique runner proof')
            progress='原runner上下文已核验；尚未写出路径完成量'
        else:
            raise ValueError('A saved technical health or original terminal runner is required')
    else:
        progress=(f"{health['completed_paths']}/{health['registered_paths']}路径完成、"
                  f"{health['running_paths']}运行、{health.get('not_reached_paths', health['registered_paths']-health['completed_paths']-health['running_paths']-health['failed_paths'])}未到达、"
                  f"{health['failed_paths']}失败")
        if health.get('active_path'):
            progress+=f"；当前路径`{health['active_path']}`"
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
    if status.get('CAL66_GPU'):
        snapshot=f"CAL66完整{scope['total_paths']}路径；{progress}。{schedule}。"
    else:
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
        if followup.get('production_CPU_accepted'):
            fa = load(followup['acceptance_ref'])
            if (fa['capture_sha256'] != digest((ROOT / followup['observation_ref']).read_bytes())['sha256']
                    or fa['source_revision'] != fl['source_revision']
                    or fa['registration_sha256'] != fl['registration_sha256']
                    or not fa['production_CPU_accepted'] or not fa['full_GPU_lifecycle_CPU_accepted']):
                raise ValueError('Price CPU completion must bind full independent acceptance')
        phase = followup['status_zh']
        active['reader']['result'] += '价格补测：' + phase + '。'
        active['evidence_or_planned_scope'] = active['reader']['result']
        snapshot += (f"\n\n**当前独立价格补测：{phase}。** "
                     f"CPU启动于{local_time(fl['started_unix'])}，最近观测{local_time(fo['observed_unix'])}。"
                     f"{link(followup['launch_ref'], '价格CPU启动原件')} · "
                     f"{link(followup['observation_ref'], '价格CPU观测')}。"
                     f"新GPU提交为{followup.get('GPU_submissions', 0)}；完整价格卡保持10路径/1624正式格/24360读出、11.5 GPUh上限。")
    run_rows = [('实验ID', active['id']), ('run', launch['run_id']), ('launch ID', launch['launch_id']),
                ('运行源码', launch['source_revision']), ('stage', launch['stage']),
                ('GPU UUID', launch['gpu_uuid']), ('容器', launch['container']),
                ('启动时间', local_time(launch['started_unix'])),
                ('注册SHA256', launch['registration_sha256']), ('配置SHA256', launch['config_sha256']),
                ('CPU证明SHA256', launch['production_CPU_sha256'])]
    for role, identity in observation.get('original_processes', {}).items():
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
                    f"{scope.get('ordinary_pairs', scope.get('guided_pairs'))}pairs / {scope.get('ordinary_CFG_calls', scope.get('CFG_calls'))}CFG / {scope['loads']}次模型加载。"
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
    price_gpu = status.get('price_refresh_GPU')
    if price_gpu:
        pl, po = load(price_gpu['launch_ref']), load(price_gpu['observation_ref'])
        if po['launch'] != pl or pl['source_revision'] != fl['source_revision']:
            raise ValueError('Price GPU observation/source differs from its actual launch')
        if abs(datetime.fromisoformat(price_gpu['observed_at']).timestamp() - po['observed_unix']) > .00001:
            raise ValueError('Price GPU observation timestamp differs')
        def original_record(key):
            item = po['files'][key]
            raw = item['raw_utf8'].encode()
            if not item['exists'] or digest(raw)['sha256'] != item['sha256'] or len(raw) != item['bytes']:
                raise ValueError('Price captured original bytes differ: ' + key)
            return json.loads(raw)
        grant, ready = original_record('grant'), original_record('ready')
        if grant['runner'] != ready['identity'] or grant['gpu_uuid'] != pl['gpu_uuid']:
            raise ValueError('Price actual CUDA owner identity differs')
        if price_gpu['hardware_admitted']:
            gate = load(price_gpu['exclusive_active_ref'])
            if not gate['observation_passed'] or gate['snapshot']['gpu_uuid'] != pl['gpu_uuid']:
                raise ValueError('Price actual active exclusivity proof required')
            apps = gate['snapshot']['compute_apps']
            if len(apps) != 1 or any(apps[0][k] != grant['runner'][k] for k in ('pid', 'start_ticks', 'uid')):
                raise ValueError('Price exclusive proof belongs to another runner')
        ph = po['health']
        pp = (f"{ph['completed_paths']}/{ph['registered_paths']}路径完成、"
              f"{ph['running_paths']}运行、{ph['not_reached_paths']}未到达、{ph['failed_paths']}失败")
        if ph.get('active_path'):
            pp += f"；当前路径`{ph['active_path']}`"
        ps = pl['scope_counts']
        snapshot = (f"**当前独占价格补测：{price_gpu['status_zh']}。** "
                    f"实际启动{local_time(pl['started_unix'])}，观测{price_gpu['observed_at']}。{pp}。\n\n"
                    f"范围：{ps['requests']} CAL / {ps['total_paths']}路径（{ps['formal_paths']}正式+{ps['warm_paths']}warm）/ "
                    f"{ps['formal_cells']}正式格、{ps['total_cells']}总格 / {ps['total_readout_trials']}读出；"
                    f"单卡上限{pl['billed_limit_GPUh']} GPUh。{schedule}。\n\n"
                    f"{link(price_gpu['launch_ref'], '唯一实际恢复启动')} · {link(price_gpu['observation_ref'], 'GPU技术观测')} · "
                    f"{link(price_gpu['exclusive_active_ref'], '实际独占接受')} · {link(status['run_report_ref'], '完整记录')}。"
                    f"{status['snapshot_note']}\n\n"
                    f"原1624已完整接受、实际{status['actual_original_GPUh']:.6f} GPUh已结算，"
                    f"{link(status['terminal_acceptance_ref'], '原1624接受')}；新价格完整生产CPU接受保持，"
                    f"{link(followup['acceptance_ref'], '价格CPU接受')}。当前技术准入不代表价格终态接受或PG闭环结果。")
        job = po['pool']['jobs'][pl['run_id']]
        rows_gpu = [('run', pl['run_id']), ('launch ID', pl['launch_id']), ('生产源码', pl['source_revision']),
                    ('stage', pl['stage']), ('GPU UUID', pl['gpu_uuid']), ('容器', pl['container']),
                    ('guardian', f"PID {pl['guardian_identity']['pid']} / start_ticks {pl['guardian_identity']['start_ticks']}"),
                    ('supervisor', f"PID {job['supervisor_pid']} / start_ticks {job['supervisor_start_ticks']}"),
                    ('runner', f"PID {grant['runner']['pid']} / start_ticks {grant['runner']['start_ticks']} / UID {grant['runner']['uid']}"),
                    ('实际启动', local_time(pl['started_unix'])), ('GPU模式', po['current_GPU']['compute_mode'])]
        run_details = ('| 当前价格GPU字段 | 实际身份 |\n|---|---|\n' + '\n'.join(
            f'| {k} | `{v}` |' for k, v in rows_gpu) + '\n\n**已接受原1624身份（历史，不重复运行）**\n\n' + run_details)
        active['reader']['result'] = f"原1624已接受；独立价格补测已实际独占启动。{pp}；完整价格结果待终态接受。"
        active['evidence_or_planned_scope'] = active['reader']['result']
        master['operation_policy'].update(active_launch_ref=price_gpu['launch_ref'], snapshot_observed_at=price_gpu['observed_at'])
        if price_gpu.get('terminal_acceptance_ref'):
            pa = load(price_gpu['terminal_acceptance_ref'])
            if (not pa['full_protocol_accepted'] or not pa['clean_action_prices_accepted']
                    or pa['capture_sha256'] != digest((ROOT / price_gpu['observation_ref']).read_bytes())['sha256']
                    or pa['launch_id'] != pl['launch_id']):
                raise ValueError('Clean price status must bind original independent acceptance')
            asset = by_id['PG-P1-ASSETS']
            asset['state'] = 'FULL_LABELS_AND_EXCLUSIVE_PRICES_ACCEPTED'
            asset['reader'].update(status='原标签与独占价格完整接受',
                result=f"原1624标签保持；独占价格10/10完整接受，实际{pa['actual_GPUh']:.6f} GPUh，原卡已结算释放。",
                next_action='以新双SHA bundle接已接受CPU的PG-P1，检验闭环策略。')
            asset['evidence_or_planned_scope'] = asset['reader']['result']
    pg = status.get('PG_P1_GPU')
    if pg:
        gl, go, gc = load(pg['launch_ref']), load(pg['observation_ref']), load(pg['CPU_acceptance_ref'])
        if (go['launch'] != gl or gl['source_revision'] != gc['source_revision']
                or not gc['production_CPU_accepted'] or not gc['full_GPU_lifecycle_CPU_accepted']
                or abs(datetime.fromisoformat(pg['observed_at']).timestamp() - go['observed_unix']) > .00001):
            raise ValueError('PG observation/launch/CPU identity mismatch')
        def pg_record(key):
            item = go['files'][key]; raw = item['raw_utf8'].encode()
            if not item['exists'] or digest(raw)['sha256'] != item['sha256'] or len(raw) != item['bytes']:
                raise ValueError('Changed PG original: ' + key)
            return json.loads(raw)
        gr, ready = pg_record('grant'), pg_record('ready')
        gate = load(pg['exclusive_active_ref'])
        apps = gate['snapshot']['compute_apps']
        if (gr['runner'] != ready['identity'] or gr['source_revision'] != gl['source_revision']
                or not gate['observation_passed'] or gate['snapshot']['gpu_uuid'] != gl['gpu_uuid']
                or len(apps) != 1 or any(apps[0][k] != gr['runner'][k] for k in ('pid','start_ticks','uid'))):
            raise ValueError('PG real sole-context identity mismatch')
        gh = go.get('health')
        gp = ('原runner已建立CUDA上下文，生产入口初始化中' if gh is None else
              f"{gh['phase']}；{gh['completed_paths']}/64位置已完成、{gh['failed_paths']}失败")
        snapshot = (f"**当前PG-P1：GPU3硬独占运行中。** 实际启动{local_time(gl['started_unix'])}，观测{pg['observed_at']}。{gp}。\n\n"
                    f"范围：4 CAL_FIT / 2 CAL_SELECT，Q≤8（首批4+一次细化4），最多64路径/40评分/2304pairs/4608CFG，单load；"
                    f"forecast{gl['forecast_GPUh']:.6f} GPUh，上限{gl['billed_limit_GPUh']} GPUh。{schedule}。\n\n"
                    f"{link(pg['launch_ref'], '唯一实际PG启动')} · {link(pg['observation_ref'], 'PG技术观测')} · "
                    f"{link(pg['exclusive_active_ref'], '真实独占核验')} · {link(status['run_report_ref'], '完整接续记录')}。{status['snapshot_note']}\n\n"
                    f"原1624标签完整接受；独占价格补测10/10完整接受、实际{pa['actual_GPUh']:.6f} GPUh已结算，"
                    f"{link(price_gpu['terminal_acceptance_ref'], '独立价格接受')}。PG-P1尚无科学结果；CPU和独占准入不代表策略优势。")
        active = by_id['PG-P1']; active['state'] = status['active_state']
        active['reader'].update(status='GPU运行中（原卡独占）',result=gp+'；新独占价格已接受，按干净Native时钟B=.80生成候选。',
            next_action='保持原64位置及Q≤8，半程只读技术检查；完整终态独立复算候选/评分/决策及财务。')
        active['evidence_or_planned_scope'] = active['reader']['result']
        master['operation_policy'].update(current_running_card='PG-P1',current_running_cards=['PG-P1'],active_launch_ref=pg['launch_ref'],snapshot_observed_at=pg['observed_at'])
        fields=[('run',gl['run_id']),('launch ID',gl['launch_id']),('source',gl['source_revision']),('stage',gl['stage']),
                ('GPU UUID',gl['gpu_uuid']),('容器',gl['container']),('guardian',gl['guardian_identity']['pid']),
                ('runner',f"PID {gr['runner']['pid']} / start_ticks {gr['runner']['start_ticks']} / UID {gr['runner']['uid']}")]
        run_details='| 当前PG-P1字段 | 原始身份 |\n|---|---|\n'+'\n'.join(f'| {k} | `{v}` |' for k,v in fields)
    if pg and pg.get('terminal_acceptance_ref'):
        ta = load(pg['terminal_acceptance_ref'])
        if (not ta['full_protocol_accepted'] or ta['launch_id'] != gl['launch_id']
                or ta['source_revision'] != gl['source_revision']
                or ta['capture_sha256'] != digest((ROOT / pg['observation_ref']).read_bytes())['sha256']
                or any(go['original_live_handles'].values())):
            raise ValueError('PG accepted terminal does not bind original capture/source/exit')
        sc = ta['scientific']
        result = (f"原件与财务完整接受；实际{ta['actual_GPUh']:.6f} GPUh。"
                  f"64登记位置中执行{sc['executed_paths']}路径、{sc['scored_pairs']}评分、{sc['query_attempts']}候选查询；"
                  + ('已冻结所选策略。' if sc['selected_policy'] is not None else '未选出满足冻结预算的策略，PG-P2尚不准入。'))
        next_action = ('按冻结策略去重后确定P2完整范围和报价。' if ta['PG_P2_input_ready'] else
                       pg.get('analysis_next_action', '保留原终态与费用，离线分析预算不可行原因；不追加查询、不改阈值、不直接启动P2。'))
        snapshot = (f"**PG-P1已结束并完成原件验收。** {result}\n\n"
                    f"观测：{pg['observed_at']}。原半程/终态检查已关闭，无重复提交。\n\n"
                    f"{link(pg['observation_ref'], '完整原终态')} · {link(pg['terminal_acceptance_ref'], '独立接受')} · "
                    f"{link(status['run_report_ref'], '完整记录')}。{status['snapshot_note']}")
        active['reader'].update(status=status['active_state_zh'],result=result,next_action=next_action)
        active['evidence_or_planned_scope'] = result
        master['operation_policy'].update(current_running_card=None,current_running_cards=[],snapshot_observed_at=pg['observed_at'])
        run_details += '\n\n' + result + '\n\n' + next_action
    history = status.get('history104_GPU')
    if history:
        hl, ho, hc = load(history['launch_ref']), load(history['observation_ref']), load(history['CPU_acceptance_ref'])
        hg = load(history['exclusive_active_ref'])
        if (ho['launch'] != hl or hc['source_revision'] != hl['source_revision']
                or not hc['production_CPU_accepted'] or not hc['full_GPU_lifecycle_CPU_accepted']
                or abs(datetime.fromisoformat(history['observed_at']).timestamp() - ho['observed_unix']) > .00001
                or hg['launch_id'] != hl['launch_id'] or hg['gpu_uuid'] != hl['gpu_uuid']
                or not hg['exclusive_gate']['observation_passed']
                or hg['capture_sha256'] != digest((ROOT / hg['capture_ref']).read_bytes())['sha256']):
            raise ValueError('History104 original launch/CPU/exclusive evidence mismatch')
        hh = ho.get('health') or {}
        hp = f"{hh.get('phase', '入口初始化')}；{hh.get('completed_paths', 0)}/104完成、{hh.get('failed_paths', 0)}失败"
        snapshot = (f"**当前104路径验证卡：GPU3硬独占运行中。** 实际启动{local_time(hl['started_unix'])}，观测{history['observed_at']}。{hp}。\n\n"
                    f"范围：4 CAL、10角色、80正式+20warm+4诊断；3744pairs/7488CFG，单load。释放GPU并结算后执行72配对/6696帧CPU评分。"
                    f"forecast{hl['forecast_GPUh']:.6f}、硬上限{hl['billed_limit_GPUh']} GPUh；部署257.771秒及累计226 GPUh保持。{schedule}。\n\n"
                    f"{link(history['launch_ref'], '唯一实际启动')} · {link(history['observation_ref'], '最新技术观测')} · "
                    f"{link(history['exclusive_active_ref'], '真实独占核验')} · {link(history['report_ref'], '组合检查与执行记录')}。\n\n"
                    "原P1原件与财务完整接受，但未选出预算可行策略。104卡CPU与独占准入不代表GPU结果；P2仍等待可行冻结策略。")
        hr = by_id['PG-P1-H104']; hr['state'] = history['status']
        hr['reader'].update(status='GPU3硬独占运行中', result=hp+'；组合CPU已接受，完整结果待终态。')
        hr['evidence_or_planned_scope'] = hr['reader']['result']
        master['operation_policy'].update(current_running_card='PG-P1-H104',current_running_cards=['PG-P1-H104'],
            active_launch_ref=history['launch_ref'],snapshot_observed_at=history['observed_at'])
        if history.get('failure_technical_summary_ref'):
            failure = load(history['failure_technical_summary_ref'])
            if (failure['launch_id'] != hl['launch_id'] or failure['full_protocol_accepted']
                    or any(ho['original_live_handles'].values())
                    or ho['container']['state']['ExitCode'] == 0):
                raise ValueError('History104 failed-terminal evidence mismatch')
            hp = (f"磁盘满提前退出；旧health记录{hh.get('completed_paths', 0)}/104完成；"
                  "GPU已释放、原锁自由，完整验收未通过。账单写入失败，11.9GPUh预约保留待恢复")
            snapshot = (f"**当前104路径验证卡：采集提前失败。** 观测{history['observed_at']}。{hp}。\n\n"
                        "原104路径范围、alpha调度、部署257.771秒及累计226 GPUh不变。原完成时间预计失效；"
                        "先保全失败原件并恢复存储与费用证据，不重派、不补跑、不分析部分结果。"
                        f"{schedule}。\n\n{link(history['report_ref'], '失败记录与接续')} · "
                        f"{link(history['observation_ref'], '原句柄失败终态')} · "
                        f"{link(history['failure_technical_summary_ref'], '技术失败汇总')}。\n\n"
                        "原P1原件与财务已接受，但无预算可行策略；P1修复与P2仍等待完整证据。")
            hr['reader'].update(status='磁盘满提前退出，费用待恢复', result=hp)
            hr['evidence_or_planned_scope'] = hp
            master['operation_policy'].update(current_running_card=None,current_running_cards=[])
        if history.get('failed_settlement_ref'):
            settlement=load(history['failed_settlement_ref']);bill=settlement['receipt'];after=settlement['after']
            if (bill['launch_id']!=hl['launch_id'] or bill['actual_is_exact'] is not False
                    or after['jobs'][hl['run_id']]['actual_GPUh']!=bill['charge_GPUh']
                    or after['jobs'][hl['run_id']]['status']!='SETTLED' or after['cap_gpu_hours']!=226):
                raise ValueError('Failed104 reconstructed settlement binding differs')
            cpu_text='恢复CPU检查进行中'
            if history.get('recovery_CPU_acceptance_ref'):
                recovery_cpu=load(history['recovery_CPU_acceptance_ref'])
                if not recovery_cpu.get('storage_ENOSPC_lifecycle_CPU_accepted'):raise ValueError('Recovery storage CPU proof missing')
                cpu_text='恢复整卡CPU与真实ENOSPC检查已通过'
            hp=(f"旧104保持失败；费用按保守重建值{bill['charge_GPUh']:.2f}GPUh结算（非精确原账单），原11.9预约已释放。"
                f"32GiB独立输出卷与48MiB跨盘控制日志已准备；{cpu_text}。")
            snapshot=(f"**104恢复准备：旧卡已结算，新GPU未启动。** {hp}\n\n"
                      "最终恢复为新的完整104、单load、原alpha与两轮顺序；forecast11.423207/硬上限11.9GPUh，释放后72组CPU评分。"
                      "部署257.771秒、累计226GPUh保持。用户明确先不重跑，旧72路径不拼接或分析调参。\n\n"
                      f"{link(history['recovery_report_ref'],'结算、保护与CPU验收')} · {link(history['recovery_final_quote_ref'],'最终完整报价')}。")
            hr['reader'].update(status='旧卡失败已结算；新104待重跑授权',result=hp,
                next_action='保持新GPU提交0；按完整104恢复合同，等待新的明确启动授权。')
            hr['evidence_or_planned_scope']=hp
            master['operation_policy'].update(current_running_card=None,current_running_cards=[])
        if history.get('terminal_acceptance_ref'):
            accepted=load(history['terminal_acceptance_ref'])
            if (not accepted['full_protocol_accepted'] or accepted['launch_id']!=hl['launch_id']
                    or accepted['source_revision']!=hl['source_revision']
                    or accepted['capture_sha256']!=digest((ROOT/history['observation_ref']).read_bytes())['sha256']
                    or any(ho['original_live_handles'].values()) or not ho['own_UUID_lock_free']
                    or ho['container']['state']['ExitCode']!=0):
                raise ValueError('History104 complete terminal binding differs')
            result=(f"104/104路径、72组/6696帧评分与独占、财务完整接受；实际{accepted['actual_GPUh']:.6f} GPUh。"
                    + ('计时模型通过。' if accepted['timing_model_validated'] else '计时模型未通过原判据，须独立成本验证后才能接P1。'))
            snapshot=(f"**104 R2已完整验收并完成离线分析。** {result}\n\n"
                      "原GPU、容器及锁已释放，终态检查已关闭；部署257.771秒、0.80×新Native与累计226 GPUh不变。"
                      "尚未选择最终策略，PG-P2不准入。\n\n"
                      f"{link(history['observation_ref'],'完整原终态')} · {link(history['terminal_acceptance_ref'],'独立接受')} · "
                      f"{link(history['analysis_ref'],'完整分析')} · {link(history['report_ref'],'结果与接续')}。")
            hr.update(full_protocol_accepted=True,evidence_or_planned_scope=result,claim_relation='COMPLETE_CAL_DESCRIPTIVE_EVIDENCE')
            hr['reader'].update(status='完整接受；计时模型待修复',result=result,
                next_action='保持预算与原alpha，先登记成本修复及独立验证；保留历史强基线与24/25D边界，不自动重派P1/P2。')
            master['operation_policy'].update(current_running_card=None,current_running_cards=[])
        fields=[('run',hl['run_id']),('launch ID',hl['launch_id']),('source',hl['source_revision']),('stage',hl['stage']),
                ('GPU UUID',hl['gpu_uuid']),('容器',hl['container']),('guardian',hl['guardian_identity']['pid']),
                ('runner',f"PID {hg['runner']['pid']} / start_ticks {hg['runner']['start_ticks']} / UID {hg['runner']['uid']}")]
        run_details='| 当前104路径卡字段 | 原始身份 |\n|---|---|\n'+'\n'.join(f'| {k} | `{v}` |' for k,v in fields)
        master['status_counts'] = {state: sum(r['state'] == state for r in rows) for state in sorted({r['state'] for r in rows})}
    cost = status.get('cost112_GPU')
    if cost:
        cl, co, cc = load(cost['launch_ref']), load(cost['observation_ref']), load(cost['CPU_acceptance_ref'])
        cg = load(cost['exclusive_active_ref'])
        if (co['launch'] != cl or cc['source_revision'] != cl['source_revision']
                or not cc['production_CPU_accepted'] or not cc['storage_ENOSPC_lifecycle_CPU_accepted']
                or cg['launch_id'] != cl['launch_id'] or cg['gpu_uuid'] != cl['gpu_uuid']
                or not cg['exclusive_gate']['observation_passed']
                or cg['capture_sha256'] != digest((ROOT/cg['capture_ref']).read_bytes())['sha256']
                or abs(datetime.fromisoformat(cost['observed_at']).timestamp()-co['observed_unix']) > .00001):
            raise ValueError('Cost112 original launch/CPU/exclusive evidence mismatch')
        ch = co.get('health') or {}
        progress = f"{ch.get('phase','入口初始化')}；{ch.get('completed_paths',0)}/112完成、{ch.get('failed_paths',0)}失败"
        result = progress + '；新模型尚未独立验收，P1继续等待。'
        snapshot = (f"**当前COST112独立计时验证：硬独占运行中。** 实际启动{local_time(cl['started_unix'])}，观测{cost['observed_at']}。{result}\n\n"
                    "保留原10角色、强基线与alpha；20warm+8独立全D时钟参照+80正式+4诊断，4032pairs/8064CFG，单load。"
                    "系数由已接受104完整数据冻结，本卡72个目标只验证、不重拟合。释放GPU结算后72组/6696帧CPU评分。\n\n"
                    f"forecast{cl['forecast_GPUh']:.6f}、硬上限{cl['billed_limit_GPUh']} GPUh；部署257.771秒、0.80×新Native及累计226 GPUh保持。{schedule}。\n\n"
                    f"{link(cost['launch_ref'],'唯一实际启动')} · {link(cost['observation_ref'],'最新技术观测')} · "
                    f"{link(cost['exclusive_active_ref'],'真实独占')} · {link(cost['report_ref'],'归因及独立验证记录')}。\n\n"
                    "原104 R2完整接受，原计时模型最坏低估2.618秒未通过2秒门槛；新卡通过后才接新P1生产验证与完整报价。")
        cr = by_id['PG-P1-C112']; cr['state'] = cost['status']
        cr['reader'].update(status='独立计时验证硬独占运行中', result=result)
        cr['evidence_or_planned_scope'] = result
        master['operation_policy'].update(current_running_card='PG-P1-C112',current_running_cards=['PG-P1-C112'],
            active_launch_ref=cost['launch_ref'],snapshot_observed_at=cost['observed_at'])
        fields=[('run',cl['run_id']),('launch ID',cl['launch_id']),('source',cl['source_revision']),('stage',cl['stage']),
                ('GPU UUID',cl['gpu_uuid']),('容器',cl['container']),('guardian',cl['guardian_identity']['pid']),
                ('runner',f"PID {cg['runner']['pid']} / start_ticks {cg['runner']['start_ticks']} / UID {cg['runner']['uid']}")]
        run_details='| 当前112路径卡字段 | 原始身份 |\n|---|---|\n'+'\n'.join(f'| {k} | `{v}` |' for k,v in fields)
        if cost.get('terminal_acceptance_ref'):
            ca = load(cost['terminal_acceptance_ref'])
            if (not ca['full_protocol_accepted'] or ca['launch_id'] != cl['launch_id']
                    or ca['source_revision'] != cl['source_revision']
                    or ca['capture_sha256'] != digest((ROOT/cost['observation_ref']).read_bytes())['sha256']
                    or any(co['original_live_handles'].values()) or not co['own_UUID_lock_free']
                    or co['container']['state']['ExitCode'] != 0
                    or cost['timing_model_validated'] != ca['timing_model_validated']):
                raise ValueError('Cost112 complete terminal binding differs')
            ct = ca['scientific']['timing']
            result = (f"112路径、72组/6696帧评分及23控制完整接受；实际{ca['actual_GPUh']:.6f} GPUh。"
                      f"计时平均绝对相对误差{ct['mean_absolute_relative_error']*100:.3f}%，最大低估{ct['maximum_underestimate_seconds']:.3f}秒；"
                      + ('原计时门通过。' if ca['timing_model_validated'] else '最大低估未过原2秒门槛，新P1不准入。'))
            snapshot = (f"**COST112已完整验收，计时模型{'通过' if ca['timing_model_validated'] else '未通过'}。** {result}\n\n"
                        f"本卡按0.80×新Native得到实际预算{ct['budget_seconds']:.3f}秒，绝对上限257.771秒、固定6秒余量与累计226 GPUh不变。"
                        "原GPU、容器与锁已释放，检查已关闭；热降频证据保留，不剔除样本、不重新拟合或自动追加GPU。\n\n"
                        f"{link(cost['observation_ref'],'完整原终态')} · {link(cost['terminal_acceptance_ref'],'独立接受')} · "
                        f"{link(cost['analysis_ref'],'完整计时与温控诊断')} · {link(cost['report_ref'],'结果和后续')}。")
            cr.update(full_protocol_accepted=True, timing_model_validated=ca['timing_model_validated'],
                      claim_relation='COMPLETE_INDEPENDENT_TIMING_VALIDATION', evidence_or_planned_scope=result)
            cr['reader'].update(status='完整接受；计时门'+('通过' if ca['timing_model_validated'] else '失败'), result=result)
            master['operation_policy'].update(current_running_card=None,current_running_cards=[])
            if cost.get('root_cause_analysis_ref'):
                cause = load(cost['root_cause_analysis_ref'])
                if (cause['inputs'][cost['observation_ref']] != ca['capture_sha256']
                        or cause['coefficients_changed'] or cause['thresholds_changed']
                        or cause['new_GPU_submissions']):
                    raise ValueError('Cost112 attribution must preserve complete evidence and frozen gates')
                snapshot += ("\n\n后续归因已完成：最大低估中，同块全D参照差异1.356秒，余下3.650秒分布在主流水线、外层处理与写入。"
                             "更近/双参照最大值仍不能过2秒，温控因果份额尚不能识别。先补运行条件与阶段计时的CPU等价验证，不重跑。 "
                             + link(cost['root_cause_report_ref'],'归因结论') + ' · '
                             + link(cost['repair_plan_ref'],'修复、独立验证与P1接续方案'))
        master['status_counts']={state:sum(r['state']==state for r in rows) for state in sorted({r['state'] for r in rows})}
    repair = status.get('P1_repair102_preparation')
    if repair:
        ra, rt, rq, repair_exposure = (load(repair[k]) for k in ('CPU_acceptance_ref','CPU_terminal_ref','quote_ref','exposure_ref'))
        if (not ra['production_entry_CPU_accepted'] or ra['source_revision'] != rt['launch']['source_revision']
                or not repair_exposure['scoped_no_execution_evidence'] or rq['scope_counts']['maximum_paths'] != 102
                or repair['new_GPU_submissions'] != 0 or repair['specific_quote_authorized']):
            raise ValueError('P1 repair preparation evidence mismatch')
        snapshot += ("\n\n**新P1准备：入口CPU已独立接受，GPU未启动。** 新的同输入全D时钟块、三条历史强基线、原alpha及一次有限恢复已接入；"
                     "Q≤8候选之外另有3条固定比较布局，完整最多102路径/58组评分。"
                     f"预计{rq['forecast_complete_GPUh']:.4f} GPUh、建议上限{rq['billed_limit_GPUh']:g} GPUh，尚未专项批准；原112的11.9、累计226与部署257.771秒不变。"
                     "新102监督/捕获/财务终态组合仍须独立CPU接受，且必须等待112完整计时门，不能凭入口CPU派卡。 "
                     + link(repair['report_ref'],'准备与报价记录') + ' · ' + link(repair['CPU_acceptance_ref'],'入口CPU接受'))
        if cost and cost.get('terminal_acceptance_ref') and not cost['timing_model_validated']:
            snapshot += " 当前112已完整结束且计时门失败，原102参照方案不能直接接续；先审阅完整误差诊断，保留入口CPU原件与未执行报价。"
        by_id['PG-P1']['reader']['next_action'] = by_id['PG-P1-R102']['reader']['next_action']
    shared = status.get('shared_exploration_preparation')
    if shared and shared.get('CPU_acceptance_ref'):
        sa, sc, sq, pool, exposure = (load(shared[k]) for k in
            ('CPU_acceptance_ref','CPU_terminal_ref','quote_ref','pool_ref','exposure_ref'))
        if (not sa['production_entry_CPU_accepted'] or sa['complete_CPU_paths'] != 76
                or sa['capture_sha256'] != digest((ROOT/shared['CPU_terminal_ref']).read_bytes())['sha256']
                or sa['source_revision'] != sc['launch']['source_revision']
                or not exposure['scoped_clear'] or len(pool['members']) != 48
                or sq['scope']['total_paths'] != 106 or shared['new_GPU_submissions'] != 0
                or shared['GPU_dispatch_ready']):
            raise ValueError('Shared exploration source/CPU/pool preparation differs')
        snapshot = ('**当前推进Shared-CAL106探索准备，GPU未启动。** Shared24/25通用构造、原α与强基线已绑定；'
            '唯一激进档20D，少步Native26/28/30。新生产入口76条CPU采样路径完整接受，48组新输入通过范围内曝光核查。\n\n'
            f"完整106路径：76正式、20计时重复、8warm、2诊断；预计{sq['quote']['forecast_GPUh']:.6f} GPUh，拟上限11.5 GPUh，未预留。"
            '累计226 GPUh及最终min(257.771秒,0.8×新Native)不变。整卡监督/释放后评分/终态组合和质量资源CPU仍须完成；入口CPU不代表GPU准入。\n\n'
            '用户已授权新的探索/确认合同：探索不再以前一计时模型的2秒门为前置，最终方法仍须独立实测预算确认。'
            '旧104/112计时失败和原P1空选择保留，新的纯计时卡与GRAPH102暂缓。\n\n'
            + link(shared['report_ref'],'本轮准备与验收') + ' · ' + link(shared['contract_ref'],'探索/确认合同')
            + ' · ' + link(shared['CPU_acceptance_ref'],'入口CPU接受') + ' · ' + link(shared['quote_ref'],'完整范围与报价'))
        sr = by_id['PG-SHARED-CAL106']
        sr['production_entry_CPU_accepted'] = True
        sr['reader'].update(status='入口CPU已接受；GPU未授权未启动',
            next_action='补齐新整卡监督、释放后评分和终态组合及质量资源CPU；保留本轮不启动GPU的边界。')
        for old_id in ('PG-P1','PG-P1-C112','PG-P1-R102'):
            by_id[old_id]['reader']['next_action']='旧失败和费用保留；新纯计时卡与GRAPH102暂缓，转入Shared-CAL106准备。'
        run_details = ('| 当前准备字段 | 内容 |\n|---|---|\n'
            f"| CPU source | `{sa['source_revision']}` |\n| CPU stage | `{sc['launch']['stage']}` |\n"
            '| CPU资源 | 1CPU / 4GiB / GPU隐藏，已退出0 |\n| GPU提交 / 预算预留 | 0 / 0 |')
    if shared and shared.get('combination_CPU_acceptance_ref'):
        ca=load(shared['combination_CPU_acceptance_ref']);cc=load(shared['combination_CPU_terminal_ref'])
        if (not ca['full_GPU_lifecycle_CPU_accepted'] or not ca['post_CPU_resource_limits_verified']
                or not ca['original_scoring_failure_receipts_retained']
                or ca['capture_sha256']!=digest((ROOT/shared['combination_CPU_terminal_ref']).read_bytes())['sha256']
                or ca['source_revision']!=cc['launch']['source_revision']
                or ca['registered_paths']!=106 or ca['independent_quality_positions']!=228
                or ca['GPU_dispatch_ready'] or ca['independent_quality_models_CPU_accepted']):
            raise ValueError('CAL106 combination CPU evidence differs')
        snapshot=snapshot.replace('整卡监督/释放后评分/终态组合和质量资源CPU仍须完成；入口CPU不代表GPU准入。',
            '整卡监督、释放后评分与终态组合CPU已接受；独立质量模型资源CPU仍待完成，不能据组合通过启动GPU。')
        snapshot+=' · '+link(shared['combination_CPU_acceptance_ref'],'组合CPU接受')
        by_id['PG-SHARED-CAL106']['reader'].update(status='入口与整卡组合CPU已接受；模型CPU待完成；GPU未启动',
            next_action='补齐独立质量模型资源和真实CPU；本轮不启动GPU，报价与原预算不变。')
        run_details+=f"\n| 组合CPU source | `{ca['source_revision']}` |\n| 组合CPU stage | `{cc['launch']['stage']}` |\n| 组合边界 | 106位置/72配对/228独立指标调度；真实93帧LPIPS；独立质量模型未加载 |"
    cal66 = status.get('CAL66_preparation')
    if cal66:
        c66, test66 = load(cal66['manifest_ref']), load(cal66['design_CPU_ref'])
        if (c66['scope']['total_paths'] != 66 or c66['scope']['LPIPS_pairs'] != 48
                or c66['scope']['independent_quality_positions'] != 156
                or test66['source_sha256'][cal66['manifest_ref']] != digest((ROOT/cal66['manifest_ref']).read_bytes())['sha256']
                or c66['GPU_dispatch_ready'] or cal66['new_GPU_submissions'] != 0):
            raise ValueError('CAL66 design evidence differs')
        snapshot = ('**下一卡已调整为CAL66，GPU未启动。** 4旧CAL、13正式角色：52正式、6重复、6预热、2历史桥接；'
            'Shared24/25保留原α，新增同布局全phase A与age3对照。20D推后，若新DEV为正优先补齐。\n\n'
            f"完整报价预计{c66['quote']['forecast_GPUh']:.6f} GPUh，拟上限8 GPUh，未批准执行、未预约。"
            '累计226 GPUh及最终min(257.771秒,0.8×新Native)不变。16项本地设计CPU检查通过，'
            '不等于CAL66生产/整卡组合接受；独立质量模型CPU仍待完成。\n\n'
            'CAL106保留为未执行的被替代方案，原入口和组合CPU接受仍有效作为组件复用依据。'
            '新输入池完成过范围内来源组审计，首次使用前仍需增量核查。\n\n'
            + link(cal66['report_ref'],'设计变更与核查') + ' · ' + link(cal66['contract_ref'],'比较及决策合同')
            + ' · ' + link(cal66['manifest_ref'],'66路径与完整报价') + ' · ' + link(cal66['design_CPU_ref'],'本地设计检查'))
        by_id['PG-SHARED-CAL106']['reader'].update(status='未执行方案已由CAL66替代；原CPU接受保留',
            next_action='按闭包复用已验组件，不派发旧106；执行准备转CAL66。')
        for old_id in ('PG-P1','PG-P1-C112','PG-P1-R102'):
            by_id[old_id]['reader']['next_action']='保留旧失败与费用；纯计时及GRAPH102暂缓，推进CAL66设计。'
        run_details = ('| 当前设计字段 | 内容 |\n|---|---|\n'
            '| 正式 / 重复 / 预热 / 桥接 | 52 / 6 / 6 / 2 |\n'
            '| 更新 / CFG调用 / 加载 | 2296 / 4592 / 1 |\n'
            '| 释放后评分 | 48对LPIPS/4464帧，52视频×3独立指标 |\n'
            '| CPU状态 | 本地设计16项通过；变更生产入口与组合接受待完成 |\n'
            '| GPU提交 / 预算预留 | 0 / 0 |')
        if cal66.get('production_CPU_accepted'):
            entry=load(cal66['entry_CPU_acceptance_ref'])
            if (not entry['production_entry_CPU_accepted'] or entry['complete_CPU_paths']!=60
                    or entry['capture_sha256']!=digest((ROOT/cal66['entry_CPU_terminal_ref']).read_bytes())['sha256']):
                raise ValueError('CAL66 production CPU evidence differs')
            snapshot=snapshot.replace('16项本地设计CPU检查通过，不等于CAL66生产/整卡组合接受；独立质量模型CPU仍待完成。',
                '15角色/60路径真实生产入口CPU已接受；整卡组合正在修复验收，独立质量模型CPU仍待完成。')
            snapshot+=' · '+link(cal66['entry_CPU_acceptance_ref'],'CAL66生产CPU接受')
            run_details=run_details.replace('本地设计16项通过；变更生产入口与组合接受待完成','生产入口60路径接受；组合与真实模型CPU验收推进中')
        if cal66.get('combination_CPU_accepted'):
            ca=load(cal66['combination_CPU_acceptance_ref'])
            if (not ca['full_GPU_lifecycle_CPU_accepted'] or not ca['storage_ENOSPC_lifecycle_CPU_accepted']
                    or not ca['post_CPU_resource_limits_verified'] or not ca['real_LPIPS93']
                    or (ca['registered_paths'],ca['LPIPS_pairs'],ca['LPIPS_frames'],ca['independent_quality_positions'])!=(66,48,4464,156)
                    or ca['capture_sha256']!=digest((ROOT/cal66['combination_CPU_terminal_ref']).read_bytes())['sha256']
                    or ca['GPU_submissions'] or ca['ledger_written']):
                raise ValueError('CAL66 full combination CPU evidence differs')
            snapshot=snapshot.replace('整卡组合正在修复验收，独立质量模型CPU仍待完成。',
                '66位置整卡监督、历史原件桥接、释放后48/156评分和终态组合CPU已接受；真实质量模型CPU仍待完成。')
            snapshot+=' · '+link(cal66['combination_CPU_acceptance_ref'],'CAL66组合CPU接受')
            run_details=run_details.replace('生产入口60路径接受；组合与真实模型CPU验收推进中','生产入口60路径与整卡组合接受；真实模型CPU验收推进中')
        if cal66.get('quality_models_CPU_accepted'):
            models=load(cal66['quality_models_CPU_acceptance_ref'])
            if (not models['CPU_accepted'] or models['accepted_models']!=5
                    or models['capture_sha256']!=digest((ROOT/cal66['quality_models_CPU_terminal_ref']).read_bytes())['sha256']
                    or models['GPU_submissions'] or models['ledger_written']):
                raise ValueError('CAL66 original model CPU evidence differs')
            snapshot=snapshot.replace('真实质量模型CPU仍待完成。','五个原始质量模型真实CPU前向已接受；完整93帧评分探针另行验收。')
            snapshot+=' · '+link(cal66['quality_models_CPU_acceptance_ref'],'原模型CPU接受')
            run_details=run_details.replace('真实模型CPU验收推进中','五模型CPU接受；93帧评分探针推进中')
        if cal66.get('complete_CPU_preparation_accepted'):
            all_cpu=load(cal66['complete_CPU_preparation_ref'])
            video=load(cal66['quality_video_CPU_acceptance_ref'])
            if (not all_cpu['CPU_preparation_accepted'] or not video['CPU_accepted']
                    or all_cpu['registered_paths']!=66 or all_cpu['real_original_models_accepted']!=5
                    or all_cpu['real_video_metric_probes']!=3 or all_cpu['probe_frames']!=93
                    or video['capture_sha256']!=digest((ROOT/cal66['quality_video_CPU_terminal_ref']).read_bytes())['sha256']
                    or all_cpu['binding_sha256']!=digest((ROOT/cal66['quality_binding_ref']).read_bytes())['sha256']
                    or all_cpu['quote']['forecast_GPUh']!=c66['quote']['forecast_GPUh']
                    or not all_cpu['CPU_planning']['within_original_CPU_envelope']
                    or all_cpu['GPU_submissions'] or all_cpu['new_GPUh_reserved'] or all_cpu['GPU_dispatch_ready']):
                raise ValueError('CAL66 final separate CPU gates or unchanged quote differ')
            snapshot=snapshot.replace('五个原始质量模型真实CPU前向已接受；完整93帧评分探针另行验收。',
                '五个原始质量模型CPU与完整93帧三指标探针也已接受；四项CPU证据已独立合并复核，尚无新GPU结果。')
            snapshot+=' · '+link(cal66['complete_CPU_preparation_ref'],'完整CPU准备与报价复核')
            run_details=run_details.replace('五模型CPU接受；93帧评分探针推进中','五模型及93帧三指标CPU接受')
            run_details+='\n| CPU评分规划 | 探针与历史LPIPS外推并加余量约4.72小时，原6小时/2CPU/8GiB上限不变；非整批实测 |'
    cal66_gpu=status.get('CAL66_GPU')
    if cal66_gpu:
        launch66=load(cal66_gpu['launch_ref'])
        if launch66['run_id']!='cara-shared-cal66-ada-r1' or launch66['billed_limit_GPUh']!=8 or launch66['scope_counts']['total_paths']!=66:
            raise ValueError('CAL66 launch differs from authorized full card')
        snapshot=('**CAL66完整66路径已单次启动，正在运行。** '+cal66_gpu['started_local']+'，'+cal66_gpu['GPU_label']+'实际硬独占及唯一原runner上下文已核验。'
            '52正式、6计时重复、6warm、2历史桥接，原α与强基线不变。\n\n'
            '预计占卡6.48GPUh，单卡硬上限8GPUh；累计226GPUh和最终min(257.7712338712067秒,0.8×fresh Native)不变。'
            '32GiB私有输出卷和跨盘48MiB控制日志已准入。GPU释放并结算后，执行48组LPIPS/4464帧及52视频×3独立指标，CPU限2核/8GiB/6小时。\n\n'
            +link(cal66_gpu['launch_ref'],'唯一实际启动')+' · '+link(cal66_gpu['admission_ref'],'硬独占与存储准入')+' · '+link(cal66_gpu['report_ref'],'执行与检查安排'))
        run_details=('| 当前执行字段 | 内容 |\n|---|---|\n'
            '| GPU提交 / 新预约 | 1 / 8 GPUh |\n'
            '| 独占设备 | '+cal66_gpu['GPU_label']+' |\n'
            '| 半程检查 | '+cal66_gpu['halfway_local']+' |\n'
            '| 首次收件检查 | '+cal66_gpu['terminal_check_local']+'；若评分未完按原句柄继续 |\n'
            '| 证据边界 | 当前只有技术准入；不分析部分结果或调参 |')
        by_id['PG-SHARED-CAL66']['reader'].update(status='GPU已实际硬独占启动，完整结果待收件',next_action='按原launch半程技术检查，GPU释放后CPU评分，再完整独立验收。')
        by_id['PG-SHARED-CAL66']['state']='GPU_EXCLUSIVE_RUNNING'
        by_id['PG-SHARED-CAL66']['reader']['result']='完整66路径单次运行；原alpha与强基线、8/226GPUh及最终部署预算不变；暂无新CAL科学结论。'
        by_id['PG-SHARED-CAL66']['evidence_or_planned_scope']=by_id['PG-SHARED-CAL66']['reader']['result']
        master['operation_policy'].update(current_running_card='PG-SHARED-CAL66',current_running_cards=['PG-SHARED-CAL66'],active_launch_ref=cal66_gpu['launch_ref'],snapshot_observed_at=cal66_gpu['observed_unix'])
        master['status_counts']={state:sum(r['state']==state for r in rows) for state in sorted({r['state'] for r in rows})}
    failure66=status.get('CAL66_failure')
    if failure66:
        failed=load(failure66['terminal_ref']);finance=load(failure66['finance_ref'])
        if (failed['launch']['launch_id']!=launch66['launch_id'] or failed['container_state']['Running']
                or failed['container_state']['ExitCode']==0 or any(failed['live_handles'].values())
                or not finance['authoritative_ledger_settled'] or finance['full_protocol_accepted']):
            raise ValueError('CAL66 failed terminal identity/settlement differs')
        cost=finance['exact_actual_GPUh']
        snapshot=('**CAL66已提前失败退出，0/66路径完成。** '+failure66['ended_local']+'，模型加载后的首请求尝试修改冻结的InferenceArguments.seed，触发ValidationError。'
            '未进入后续采集与CPU评分；原α、强基线、66分母和预算不变。\n\n'
            f'精确结算{cost:.6f} GPUh，原预约已释放；四个原句柄退出、设备锁释放，GPU模式恢复。磁盘保护及跨盘账单完整。'
            '原半程与完整验收检查已取消，旧完成ETA失效；没有重跑。\n\n'
            +link(failure66['report_ref'],'技术失败与费用记录')+' · '+link(failure66['terminal_ref'],'原失败终态')+' · '+link(failure66['finance_ref'],'独立财务核验'))
        run_details=('| 字段 | 当前原件状态 |\n|---|---|\n'
            '| 完整分母 | 66；0完成、1失败、其余未到达 |\n'
            '| 直接错误 | 修改冻结InferenceArguments.seed |\n'
            f'| 实际GPUh | {cost:.9f}，权威账本已结算 |\n'
            '| GPU/锁 | 原句柄退出、模式已恢复、锁释放 |\n'
            '| 磁盘/日志 | 私有卷约31.18GiB可用，48MiB跨盘日志完整 |\n'
            '| 后续检查 | 原两次检查已删除；无新采集/评分ETA |\n'
            '| 证据边界 | 技术失败、财务已核验；无新科学结果、未重跑 |')
        active66=by_id['PG-SHARED-CAL66'];active66['state']=status['active_state']
        active66['reader'].update(status=status['active_state_zh'],result=f'完整66分母保留，0完成；首请求冻结参数异常。精确费用{cost:.6f} GPUh已结算；无科学结果。',next_action='先修真实冻结参数适配并验证；保留失败原件，不自动重跑。')
        active66['reader']['evidence_refs']=list(dict.fromkeys(active66['reader']['evidence_refs']+[failure66['report_ref'],failure66['terminal_ref'],failure66['finance_ref']]))
        active66['evidence_or_planned_scope']=active66['reader']['result']
        master['operation_policy'].update(current_running_card=None,current_running_cards=[],snapshot_observed_at=failed['observed_unix'])
        master['status_counts']={state:sum(r['state']==state for r in rows) for state in sorted({r['state'] for r in rows})}
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
