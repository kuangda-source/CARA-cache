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


唯一启动与首条确认（2026-11-05）：

- run_id：`cara-avslc-minitest-r1-20261105`；launch_id：`08565678d6ef4df8a45c32b711208ea2`；GPU：`GPU-cebf7119-cf03-23b9-e192-cd196332b704`。
- GPU冻结源码：`0b60043038438147a7644a22d311170457c0ca04`（启动前已commit+push）；scope：`e44d6a74994fa1c20b967c779f503f4879b3b1f6af35d5a672e5e56448204b15`。四臂16formal＋2warm，八个F17/G17旧对照只复用；原mask、α=1、light C及两参数集预测未调参。
- guardian实际计费/启动北京时间 **2026-11-05T18:42:51.268368+08:00**；Docker StartedAt=`2026-11-05T10:42:52.912386102Z`（UTC）。报价中心 **1.389370089431008GPUh**、工程范围[1.1973634065041578, 1.4853734308944329]，墙钟中心1小时23分22秒，预计完成北京时间 **2026-11-05T20:06:13.000690+08:00**（报价估计）。硬限 **1.5GPUh**，硬截止 **2026-11-05T20:12:51.268368+08:00**；停止新工作阈值 **2026-11-05T20:02:51.268368+08:00**，600s释放余量不变。
- 建议人工中途检查约第9/18条结束：北京时间 **2026-11-05T19:24:36.507934+08:00**（按累计请求报价估计，非预约）。本轮不安排中途/结束例程，不发通知。
- 实际路由FRP `two_card_relay`，由`~/.local/bin/intranet-ssh two-card` / ops `--route relay`选择；未退Tailscale。
- 中央唯一预留 **seq101 AVSLC_MINITEST_WHOLE1_5_RESERVE，1.5GPUh**。预留前used230.13805245018418/reserved16.5/历史格式available3.3619475498158238；预留后used230.13805245018418/reserved18.0/历史格式available1.8619475498158238。旧16.5未知责任保持；cap250仅为兼容字段，不是新的累计政策上限，累计实际待终态唯一结算后更新。
- Linux CPU生产入口及36条完整tiny路由通过，原CPU退出0、CUDA=false。fresh admit MemAvailable=57283866624 bytes（53.349758GiB），资产/源码/owner双锁/闲置GPU/存储均通过。
- 新私有卷/dev/loop55 ext4，image=`/media/minchen/4def5c03-8324-4cba-ac0b-9fda7c79dc7b/gkd/cara_cal66_sm86_workspace/.sync/storage-reservations/avslc-minitest-r1/output.ext4`，16GiB、output_device1847；输出bind在本run新卷上。Memory=MemorySwap=42949672960 bytes（40g），50GiB host/90°C/4GiB低水位全部保持，未碰旧卡卷。
- 一次有界前台确认于北京时间2026-11-05T18:44:45.862575+08:00结束：容器Running=true/OOMKilled=false；guardian PID1286393、supervisor PID1286476、runner PID1286518的原PID/start ticks均存活；目标GPU唯一runner占24,418MiB，Exclusive_Process、58°C；collection=RUNNING，0/18完成，首条AVSLC_001 RUNNING。未等待首条结束或全卡完成。确认reader已退出，此后不再远端检查或改动运行stage。

正常回执为本报告目录的precheck_reduced.json、linux_cpu.json、storage.json、admission.json、central_reservation.json、start_confirmation.json。沿用上文status及终态capture→唯一settle→CPU score→analyze命令；不重复预留、启动或评分，无monitor/heartbeat/cron/automation。
