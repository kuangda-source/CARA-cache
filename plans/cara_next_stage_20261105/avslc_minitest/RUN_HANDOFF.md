# AVSLC 执行交接：报价阻塞，未启动

run_id：cara-avslc-minitest-r1-20261105；launch_id尚未创建。用户批准约1.2GPUh、硬限1.5。只读确认中央无job/events，服务器无对应stage/容器/输出；两GPU无计算进程，目标GPU GPU-cebf7119-cf03-23b9-e192-cd196332b704，Default/24MiB/45°C。中央实际累计230.13805245018418、旧reserved16.5、历史格式available3.3619475498158238。

**不启动的精确原因：**指定CAL35完整T_request四参数插值（light C项0）×1.1＋600s模型加载＋600s释放，22请求正式中心1.64295897071669GPUh，高于1.5硬限。工程范围1.4048452184651705–1.7620158468424494GPUh，墙钟中心1小时38分35秒。即使不加warm，20正式中心1.5236053925398065仍超硬限；本轮不删warm、不压低报价、不提高硬限。背景约1.2来自T_DD×历史actual/T_DD比例，与指定完整请求公式及固定加载/释放余量不同。

|arm|正式请求|D/A/C|完整T_request报价(s/次)|
|---|---:|---|---:|
|G17_ATAIL|4|17/19/0|204.748434|
|G17_CALL|4|17/0/19|185.863276|
|G17_A21_24|4|17/8/11|193.814922|
|R18C|4|18/0/18|192.635537|
|R17A|4|17/11/8|196.796789|

20正式request合计3895.435830s；2warm合计390.611710s（O1 CALL＋ATAIL）；总合计4286.047541s。没有fresh Native/F17/G17。中心5914.652295s超过1.5小时5400s；既有600s释放余量不变。

本地准备：prepare.py编译现有interval_grammar并冻结mask/计数/源预测/八旧对照。cpu_check.py执行五角色×flow on/off的十条完整36步tiny路径、旧对照合并与13对比/report writer合成控制；这不是Linux生产入口准入。postprocess.py仅打分20新视频，独立analyze读取固定旧report，产出complete_analysis.json、outcome_summary.json、COMPLETE_RESULTS.md。现有ops.payload仅增加声明的postrelease_inputs入冻结stage，无新框架。

未运行Linux CPU、私有卷provision、fresh admit、reserve或dispatch；无launch_id、新容器、新服务器stage或新卷。未降低50GiB/90°C/4GiB，容器仍按40g计划。报价/硬限冲突解决前，沿用既有FORMAL_QUOTE_AWAITING_APPROVAL门阻止prepare/reserve/dispatch。precheck原件在reports/cara_avslc_minitest_r1_20261105/precheck.json；本轮没有admission/reservation/start_confirmation，不能伪造。

后续仅在报价与批准硬限一致后才能按原流程执行；不可使用下列收尾命令启动或重放。两卡路由intranet-ssh two-card、ops --route relay，不改运行中卡路由。prereg_next.json和principle_refit_report.md按原字节入库；不修改其他报告或生成文档。

本地复现（Codex项目根cwd）：

```sh
worldcache_omr/.venv/bin/python worldcache_omr/plans/cara_next_stage_20261105/avslc_minitest/prepare.py
worldcache_omr/.venv/bin/python worldcache_omr/plans/cara_next_stage_20261105/avslc_minitest/cpu_check.py
```

未来有原launch后只读status（每次新receipt文件名；本轮未启动）：

```sh
PY=worldcache_omr/.venv/bin/python
P=worldcache_omr/plans/cara_next_stage_20261104/sensitivity
M=worldcache_omr/plans/cara_next_stage_20261105/avslc_minitest/manifest.json
"$PY" "$P/ops.py" status --manifest "$M" --route relay --receipt /tmp/cara_avslc_status_manual.json
```

未来终态capture→唯一settle；响应丢失恢复同一交易：

```sh
"$PY" "$P/ops.py" capture --manifest "$M" --route relay --receipt /tmp/cara_avslc_terminal.json
"$PY" - <<'PY_SETTLE'
import json
from pathlib import Path
c=json.loads(Path('/tmp/cara_avslc_terminal.json').read_text())
Path('/tmp/cara_avslc_settle_input.json').write_text(json.dumps(dict(capture=c,launch_sha256=c['files']['launch']['sha256'])))
PY_SETTLE
"$PY" "$P/ops.py" settle --manifest "$M" --route relay --input /tmp/cara_avslc_settle_input.json --receipt /tmp/cara_avslc_settlement.json
```

未来22/22完成、释放/Default恢复/原进程结束、唯一结算后，原CPU评分仅一次：

```sh
"$PY" - <<'PY_SCORE'
import json
from pathlib import Path
c=json.loads(Path('/tmp/cara_avslc_terminal.json').read_text())
s=json.loads(Path('/tmp/cara_avslc_settlement.json').read_text())
Path('/tmp/cara_avslc_score_input.json').write_text(json.dumps(dict(capture=c,settlement=s)))
PY_SCORE
"$PY" "$P/postrun.py" score --manifest "$M" --route relay --input /tmp/cara_avslc_score_input.json --receipt /tmp/cara_avslc_score_launch.json
# 原scorer退出0、scores.json=COMPLETE_PENDING_ANALYSIS后：
"$PY" "$P/postrun.py" analyze --manifest "$M" --route relay --receipt /tmp/cara_avslc_analysis.json
```

计划服务器R=/data20t/gaokuangda/worldcache_workspace；S=$R/.sync/cara-budget-calibration-GPU-avslc-minitest-r1-20261105；O=$R/outputs/cara-avslc-minitest-r1-20261105。进度O/collection.json；日志S/{runner.log,host-guardian.log,guardian.json,supervisor.json,billing.json}；收尾S/released-score-control/{scores.json,complete_analysis.json,outcome_summary.json,COMPLETE_RESULTS.md}。本轮均未创建。

中途和结束检查由用户后续安排，本轮不创建例程或通知。无实际start，不能提供北京时间ETA、hard stop或halfway时刻；未来按实际start及前11/22条累计请求报价计算约50%请求的建议检查点。
