# confirm10 — PREPARE / QUOTE ONLY

计划run_id `cara-generator-v1-confirm10-r1-20261105`；没有launch_id、stage、私有卷、预留或启动。`manifest.json` 的phase为PREPARE_QUOTE_PENDING_USER_APPROVAL，三项authority及GPU_dispatch_ready均false。**所有新run须用户本次go-ahead，当前不得sync/prepare远端、预留或启动。** 本轮远端操作仅relay只读身份检查；不查询/写入中央预留。建议硬限5.0GPUh不是执行批准。

62请求=10输入×6角色+2warm（首输入F17、Native-k18）。CAL35完整请求合计13339.467544s；中心 **4.409281749555557GPUh / 4小时24分33秒**，工程范围 **3.6682002193333347–4.779822514666669GPUh / 3小时40分06秒–4小时46分47秒**，建议硬限5.0GPUh。不是idea的粗估3.5h；这里计入十个全新Native36、完整请求非loop开销、两warm、10%及1200s加载/释放。逐角色报价与锚见quote.json。

本地执行（cwd始终Codex项目根；不会连接服务器）：

```sh
worldcache_omr/.venv/bin/python worldcache_omr/plans/cara_next_stage_20261105/confirm10/prepare.py
worldcache_omr/.venv/bin/python worldcache_omr/plans/cara_next_stage_20261105/confirm10/cpu_check.py
```

本次CPU检查：F17、R16C/R18C/R21C各flow on/off，共8条完整36步tiny sampler路径，实际action无fallback、latent有限、CUDA=false；10prompt合成分析覆盖BETTER、SECONDARY_NONINFERIOR、INCONCLUSIVE和报告先列冻结预测。未加载生产权重；未运行Linux生产入口/真实93帧评分，不宣称Native-k18生产路由通过。

**启动前尚需的小接线（本轮只记录，不修改共享runner/src）：**

1. `src/wcomr/cara_f19_speed190_requests_r1.py` 的 `Requests.__call__` 从本manifest角色取 `role['requested_steps']` 和 `slot['seed']`；native分支用 `role['schedule']`；T_DD wrapper用 `role['expected_updates']`。本卡已为所有角色填写这些值，NATIVE35=35/36，NATIVE_K18=18/19。当前旧入口仍固定35/36，不能启动此manifest。
2. 复用 `p2_native_sampling.execute` 的已验18..35请求域、全block计数和固定UniPC网格。原网格见reports/cara_PG_Native18to35_committed_scheduler_CPU_20261023.json。无需改sampler/vendor；为18/19及35/36两条Native增加/适配现有tiny CPU fixture后，再跑相同Linux生产入口证明。LinuxCPU原fixture也使用固定35/36，不能把目前8条mask检查当其替代。
3. Native-k18按仓库惯例实际19D，预计T_DD136.90s，较R18C130.09s约+5.2%；当前不是已实测严格等时基线。若用户要**恰好18次实际更新**，requested17目前被底层拒绝，需要另外决定协议，不在本卡暗改。

得到明确go-ahead且接线/CPU通过后，才走既有ops：无同名run/launch/容器/输出检查→冻结源码和Linux CPU→新16GiB私有卷→fresh admit→一次中央预留→一次dispatch。两卡relay；50GiB host内存、90°C、4GiB低水位和40g Memory/MemorySwap保持。输出只有MP4、终点latent/ordinary history，无逐步state；沿用gc修复。此处不提供或执行GPU启动命令。

只设一次人工半程检查及最终验收，无持续监控/例程。半程约第31/62个请求结束，按已冻结顺序累计公式约start+2小时13分（实际检查时间在未来launch时按真实start填写）；最终按4小时24分33秒中心估计。没有当前start/ETA。

以下仅是**未来实际获批并运行后**的只读status与收尾模板；本轮不执行：

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

唯一结算包含失败实际费用；响应丢失只恢复同一交易。只有62/62完成、原进程结束/GPU释放/Default恢复且唯一结算后，才CPU评分一次：

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
