# sensitivity8 resume r3

用户2026-11-05 00:30北京时间批准：「批准从 PIPE_009 续跑，约 9.84 GPUh」。仅此一个新run `cara-native-sensitivity8-resume-r3-20261105`，硬限11.0GPUh；已结算r2不重启。累计仅记实际GPUh，新单卡>8GPUh需本人批准，本卡已有批准。

本补充登记只接续原PREREGISTRATION.md及pipeline_r2补充协议：新队列116=2 fresh warm＋原PIPE_009…122的114请求，原编号保持；r2的PIPE_003…008六条COMPLETE（3控制＋3敏感度）在manifest按原slot/result与latent/video SHA固定。启动时各验一次产物hash并预置控制索引；最终CPU评分包含六条，无新增重复样本或计费。原r1五Native及F17 clean16继续只读复用，F17非劣原FAIL/p=0.300保持，s·Δv函数、seed、输入、五控制、全112后缀分母不变。

包含15bb3d39每请求gc.collect修复。新生产输出host_memory.jsonl每请求GC后记录RSS、cgroup current和peak。此服务器实测cgroup v1，current/peak分别取memory.usage_in_bytes/memory.max_usage_in_bytes；peak为容器累计高水位，current含文件页缓存，均以bytes计，不伪称逐请求瞬时峰值。

正式报价中心9.842431872190623GPUh，工程范围8.019354858550322–10.801045382298438；墙钟中心9小时50分33秒，单卡硬限11.0GPUh/小时。42次保存＋109次恢复；2fresh warm保守成本不扣。GC代价和真实40g峰值尚未GPU验证，范围不是保证。40g容器限额、50GiB fresh宿主内存、90°C自动停、4GiB低水位及600s释放余量全部保持。

独立新64GiB输出卷（旧r2 64GiB及r1 256GiB原件保持只读）；最多一份新record状态，14suffix后仅删除该run自己的state_before文件，保留小产物。新峰值约50.24GiB＋4GiB低水位及ext4开销。无heartbeat/cron/automation或持续监控；启动后仅一次短首批确认。

R=/data20t/gaokuangda/worldcache_workspace
S=$R/.sync/cara-budget-calibration-GPU-native-sensitivity8-resume-r3-20261105
O=$R/outputs/cara-native-sensitivity8-resume-r3-20261105
日志：S/runner.log、host-guardian.log、guardian.json、supervisor.json、billing.json；O/collection.json、host_memory.jsonl。
路由：~/.local/bin/intranet-ssh two-card（FRP优先，连接建立前可退Tailscale，不重放远程命令）；ops的--route relay使用该入口，中央仅走既有账本通道。

从Mac仓库根目录人工只读检查（每次换新receipt文件名）：

```sh
P=plans/cara_next_stage_20261104/sensitivity
M=$P/resume_r3/manifest.json
.venv/bin/python "$P/ops.py" status --manifest "$M" --route relay --receipt /tmp/cara_resume_r3_status_manual.json
```

终态后捕获并唯一结算，失败费用照常计入；响应丢失恢复同一交易：

```sh
.venv/bin/python "$P/ops.py" capture --manifest "$M" --route relay --receipt /tmp/cara_resume_r3_terminal.json
.venv/bin/python - <<'PY'
import json
from pathlib import Path
v=json.loads(Path('/tmp/cara_resume_r3_terminal.json').read_text())
Path('/tmp/cara_resume_r3_settle_input.json').write_text(json.dumps(dict(capture=v,launch_sha256=v['files']['launch']['sha256'])))
PY
.venv/bin/python "$P/ops.py" settle --manifest "$M" --route relay --input /tmp/cara_resume_r3_settle_input.json --receipt /tmp/cara_resume_r3_settlement.json
```

116/116完整、释放/恢复Default/原进程结束及唯一结算后才CPU评分、分析；已有scorer只恢复：

```sh
.venv/bin/python - <<'PY'
import json
from pathlib import Path
c=json.loads(Path('/tmp/cara_resume_r3_terminal.json').read_text())
s=json.loads(Path('/tmp/cara_resume_r3_settlement.json').read_text())
Path('/tmp/cara_resume_r3_score_input.json').write_text(json.dumps(dict(capture=c,settlement=s)))
PY
.venv/bin/python "$P/postrun.py" score --manifest "$M" --route relay --input /tmp/cara_resume_r3_score_input.json --receipt /tmp/cara_resume_r3_score_launch.json
# 原CPU scorer退出0且scores.json为COMPLETE_PENDING_ANALYSIS后：
.venv/bin/python "$P/postrun.py" analyze --manifest "$M" --route relay --receipt /tmp/cara_resume_r3_analysis.json
```

评分在S/released-score-control/scores.json，分析在complete_analysis.json。8旧完成中2warm只存档，六正式产物加入完整评分；不把复用称为新独立结果。

启动前状态：中央未有本run，服务器无本stage/输出/容器；ledger累计220.7842113659855、其他预留16.5、历史格式可用12.715788634014501GPUh。源提交、Linux CPU入口、新卷、fresh准入完成后才一次预留11.0并启动。实际launch、启动时间/ETA、预留回执和首批内存值由启动确认后补记。
