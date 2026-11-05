# AVSLC 四臂执行交接

run_id：cara-avslc-minitest-r1-20261105。用户批准四臂缩减方案，重新报价中心≤1.5GPUh后上卡，硬限1.5不变。launch_id、实际启动、首批确认及预留后的ledger在下方唯一启动记录中填写；没有实际回执前不声称启动。

指定CAL35完整T_request四参数插值（light C项0）×1.1＋600s模型加载＋600s释放，18请求正式中心 **1.389370089431008GPUh**，工程范围 **1.1973634065041578–1.4853734308944329GPUh**，墙钟中心1小时23分22秒。中心≤硬限1.5，保留两warm；不另删臂、不抬硬限。原阻塞方案未创建任何stage/launch/reserve；旧precheck.json仅作当时未启动记录。

|arm|正式请求|D/A/C|完整T_request报价(s/次)|
|---|---:|---|---:|
|G17_CALL|4|17/0/19|185.863276|
|G17_A21_24|4|17/8/11|193.814922|
|R18C|4|18/0/18|192.635537|
|R17A|4|17/11/8|196.796789|

16正式request合计3076.442094s；2warm合计379.678198s（O1 CALL＋A21_24）；总合计3456.120293s。没有fresh Native/F17/G17。中心5001.732322s；既有600s释放余量不变。

本地准备：prepare.py编译现有interval_grammar并冻结mask/计数/源预测/八旧对照。cpu_check.py执行四角色×flow on/off的八条完整36步tiny路径、旧对照合并与10对比/report writer合成控制；这不是Linux生产入口准入。postprocess.py仅打分16新视频，独立analyze读取固定旧report，产出complete_analysis.json、outcome_summary.json、COMPLETE_RESULTS.md。复用现有ops、runner、Requests及postrun，不改采样算法或模型参数。

按既有流程先确认无重复run，再完成Linux CPU生产入口、16GiB私有卷与fresh admit，唯一预留1.5GPUh并启动。50GiB/90°C/4GiB不变，容器Memory/MemorySwap为40g。正常回执在reports/cara_avslc_minitest_r1_20261105/；仅实际生成的CPU/storage/admission/reservation/start_confirmation可作为证据。

两卡路由intranet-ssh two-card、ops --route relay，不改运行中卡路由。prereg_next.json和principle_refit_report.md为原始预测来源，manifest仅保留本次四臂预测；原报告不改。下列收尾命令不启动GPU、不重放旧对照。

本地复现（Codex项目根cwd）：

```sh
worldcache_omr/.venv/bin/python worldcache_omr/plans/cara_next_stage_20261105/avslc_minitest/prepare.py
worldcache_omr/.venv/bin/python worldcache_omr/plans/cara_next_stage_20261105/avslc_minitest/cpu_check.py
```

只读status（每次新receipt文件名）：

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

18/18完成、释放/Default恢复/原进程结束、唯一结算后，原CPU评分仅一次：

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

服务器R=/data20t/gaokuangda/worldcache_workspace；S=$R/.sync/cara-budget-calibration-GPU-avslc-minitest-r1-20261105；O=$R/outputs/cara-avslc-minitest-r1-20261105。进度O/collection.json；日志S/{runner.log,host-guardian.log,guardian.json,supervisor.json,billing.json}；收尾S/released-score-control/{scores.json,complete_analysis.json,outcome_summary.json,COMPLETE_RESULTS.md}。

中途和结束检查由用户后续安排，本轮不创建例程或通知。按前9/18条请求累计报价，中途约在实际start＋2505.24s（41分45秒），仅建议人工检查；实际北京时间随启动回执填写。启动后仅一次短确认，无连续监控。
