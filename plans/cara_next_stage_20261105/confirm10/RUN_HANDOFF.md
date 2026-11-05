# confirm10 — 用户批准五臂 Phase A

run_id `cara-generator-v1-confirm10-r1-20261105`。用户2026-11-05原话：「批准 confirm10：先去掉 Native-k18 上卡，k18 接线验收后单独补跑；硬限按重报的数」。本卡只含Native36/F17/R18C/R16C/R21C；k18和次要(c)为deferred supplement，不自动启动补卡。manifest authority已按此批准开启；launch/预留/首条证据记录于末尾。

51请求=10输入×5角色+1条首输入F17 warm，40个93帧CPU LPIPS pair。指定CAL35完整请求公式不变：合计11145.981832s，中心 **3.739050004222224GPUh**，范围 **3.119828791333335–4.048660610666668**，硬限 **4.1GPUh**（范围上界向上取0.1）。墙钟中心3小时44分21秒，范围3小时7分11秒–4小时2分55秒；含600s load+600s release。

采用一张空闲A6000 `GPU-cebf7119-cf03-23b9-e192-cd196332b704`，不占另一张GPU。50GiB host admission、90°C、4GiB低水位及40g Memory/MemorySwap不变，新16GiB私有卷、不存逐步state。源码先commit+push，既有ops Linux生产CPU→存储→fresh admit→唯一预留4.1→一次dispatch。冻结stage在启动后不再同步。

旧cap250及16.5未知责任保留；当前预算政策为不设累计上限，单run>8需用户本人批准，累计used只在实际结算时增加。ops仅对显式携带新预算政策和直接批准的卡使用该政策；本次中央job记用户原话/日期。负的旧available只是兼容算式，不代表新政策余额。

本地准备（cwd为Codex项目根）：

```sh
worldcache_omr/.venv/bin/python worldcache_omr/plans/cara_next_stage_20261105/confirm10/prepare.py
worldcache_omr/.venv/bin/python worldcache_omr/plans/cara_next_stage_20261105/confirm10/cpu_check.py
```

只做首条开始的一次短status确认，此后由用户另行安排半程和最终验收；无监控/cron/例程。半程建议第26/51个请求结束，实际时间按启动时间和累计请求报价在末尾填写。Phase B的k18接线只改本地源码并用独立CPU-only stage验收，不动本run stage，也不预留/启动k18。

以下为本次唯一运行的的只读status与收尾模板；收尾在终态才执行：

```sh
PY=worldcache_omr/.venv/bin/python
P=worldcache_omr/plans/cara_next_stage_20261104/sensitivity
M=worldcache_omr/plans/cara_next_stage_20261105/confirm10/manifest.json
"$PY" "$P/ops.py" status --manifest "$M" --route relay --receipt /tmp/cara_confirm10_status_manual.json
"$PY" "$P/ops.py" capture --manifest "$M" --route relay --receipt /tmp/cara_confirm10_terminal.json
"$PY" - <<'PY_SETTLE'
import json
from pathlib import Path
c=json.loads(Path('/tmp/cara_confirm10_terminal.json').read_text())
Path('/tmp/cara_confirm10_settle_input.json').write_text(json.dumps(dict(capture=c,launch_sha256=c['files']['launch']['sha256'])))
PY_SETTLE
"$PY" "$P/ops.py" settle --manifest "$M" --route relay --input /tmp/cara_confirm10_settle_input.json --receipt /tmp/cara_confirm10_settlement.json
```

唯一结算包含失败实际费用；响应丢失只恢复同一交易。只有51/51完成、原进程结束/GPU释放/Default恢复且唯一结算后，才CPU评分一次：

```sh
"$PY" - <<'PY_SCORE'
import json
from pathlib import Path
c=json.loads(Path('/tmp/cara_confirm10_terminal.json').read_text())
s=json.loads(Path('/tmp/cara_confirm10_settlement.json').read_text())
Path('/tmp/cara_confirm10_score_input.json').write_text(json.dumps(dict(capture=c,settlement=s)))
PY_SCORE
"$PY" "$P/postrun.py" score --manifest "$M" --route relay --input /tmp/cara_confirm10_score_input.json --receipt /tmp/cara_confirm10_score_launch.json
# 原scorer退出0且scores.json=COMPLETE_PENDING_ANALYSIS后：
"$PY" "$P/postrun.py" analyze --manifest "$M" --route relay --receipt /tmp/cara_confirm10_analysis.json
```

计划服务器R=/data20t/gaokuangda/worldcache_workspace；S=$R/.sync/cara-budget-calibration-GPU-generator-v1-confirm10-r1-20261105；O=$R/outputs/cara-generator-v1-confirm10-r1-20261105。进度O/collection.json；日志S/{runner.log,host-guardian.log,guardian.json,supervisor.json,billing.json}；CPU输出S/released-score-control/{scores.json,complete_analysis.json,outcome_summary.json,COMPLETE_RESULTS.md}。最终拷回repo的reports/cara_generator_v1_confirm10_r1_20261105/（当前未创建结果目录）。新参考来自O的十个正式NATIVE35，不读取旧Native；CPU scorer不对Native自比做LPIPS。

验收先完整报告三冻结ratio的预测/测量误差，再给主ΔLPIPS均值/95%prompt bootstrap/逐输入方向及两级预写结论；另列三预算单调性、Native-k18比较和所有实测T_DD。不按新结果改模型、mask、prompt、seed或阈值。所有预算本轮保持不动。
