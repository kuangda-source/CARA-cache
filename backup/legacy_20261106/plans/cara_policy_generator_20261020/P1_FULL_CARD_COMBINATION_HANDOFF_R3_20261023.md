# PG-P1 整卡组合接续

本接续仅用于已注册的4 CAL_FIT、2 CAL_SELECT、Q≤8、完整64位置上限；不增加历史shadow或少步Native路径。后两者继续在P1冻结后的独立完整卡中执行。旧1624原标签不重跑，当前独占价格stage不修改。

## 一次性接续顺序

1. 使用原价格实际恢复launch，完成独立价格终态接受与原账单结算，确认原GPU上下文和锁已释放。复用原件；不得重新派价格卡。报告1624格三轮价格波动、顺序漂移与聚合放大。
2. 读取657的**完整组合CPU接受**，而不是仅656的采样入口接受。核对源闭包、原容器exit0、GPU隐藏、真实93帧LPIPS、真实子进程生命周期和终态复算。CPU失败原件保留，不能凭部分步骤通过派GPU。
3. 重新运行CAL_SELECT的本地+四卡输出身份核查；完整曝光原件须在30分钟以内。只审查身份元数据，不查看SELECT结果；有未知命中先解释清楚，不换输入。
4. 用新控制器`prepare`建立不可变PG stage，绑定旧标签、新独占价格、两份独立接受、组合CPU和完整报价原件。代码从已接受CPU stage复制；保留已接受SM89预算端口，不用仓库历史SM86文件覆盖。
5. 对实际空闲UUID做fresh preflight，再单次launch-gpu，立即admission capture。价格卡仍运行、任一自有GPU任务已预约、GPU忙、MPS、内存/磁盘/余额不足均等待。只在空闲卡设置EXCLUSIVE_PROCESS；凭据只内存/管道，不改忙卡、不驱逐他人。UNKNOWN或已有intent只recover原句柄。
6. 按实际返回的半程/终态时间安排检查，复用现有终态自动化。开始GPU意味着监督器启动，不等于硬件已准入；必须读取原runner PID/start/UID、UUID及唯一真实上下文握手。
7. 终态capture后accept-gpu。原监督/runner/容器退出、原锁释放、连续独占监测、实际账单权威结算、原始请求/视频/latent/93帧评分与候选决策独立复算必须一致。没有可行策略也保留完整64分母，不能改规则继续试。只有有合法最终策略才接PG-P2。

## 操作命令

所有输出使用新唯一路径。下面`${...}`由本次实际原件赋值；不得把占位符当成已有接受。

```bash
.venv/bin/python scripts/audit_cara_cal_select_exposure_r1.py --output "${FRESH_EXPOSURE}"

.venv/bin/python scripts/wc_four_card_cara_pg_gpu_r1.py prepare \
  --cpu-capture "${FULL_CPU_CAPTURE}" --cpu-acceptance "${FULL_CPU_ACCEPTANCE}" \
  --price-capture "${ACCEPTED_PRICE_CAPTURE}" --price-acceptance "${PRICE_ACCEPTANCE}" \
  --exposure "${FRESH_EXPOSURE}" --stage-name cara-pg-p1-full64-ada-r1-20261023 \
  --output "${NEW_STAGE_REFERENCE}"

.venv/bin/python scripts/wc_four_card_cara_pg_gpu_r1.py preflight \
  --stage-ref "${NEW_STAGE_REFERENCE}" --gpu-uuid "${IDLE_UUID}" --output "${FRESH_PREFLIGHT}"
.venv/bin/python scripts/wc_four_card_cara_pg_gpu_r1.py launch-gpu \
  --stage-ref "${NEW_STAGE_REFERENCE}" --gpu-uuid "${IDLE_UUID}" --output "${ACTUAL_PG_LAUNCH}"
.venv/bin/python scripts/wc_four_card_cara_pg_gpu_r1.py capture \
  --launch-ref "${ACTUAL_PG_LAUNCH}" --mode admission --output "${NEW_ADMISSION}"
# UNKNOWN: recover --stage-ref "${NEW_STAGE_REFERENCE}" --output "${NEW_RECOVERY}"
# 终态：capture --launch-ref "${ACTUAL_PG_LAUNCH}" --mode terminal --output "${NEW_TERMINAL}"
#       accept-gpu --capture "${NEW_TERMINAL}" --output "${NEW_ACCEPTANCE}"
```

## 执行与接受边界

- `production_batch.run`固定先Native warm2+FIT4；真实完整请求边界包含安装、guardrails、采样、解码、写视频及清理。预算B=.80由这4条干净Native均值决定，不能用旧共享GPU计时。
- Native时钟接受保存独占监测前缀SHA，原请求/视频SHA，且必须在任何候选之前。终态重新核对此前缀确为完整监测日志的前缀。
- 一个驻留Cosmos实例，候选2 warm+4 FIT；物理去重保留角色别名，不赠送额外查询。第一批≤4，单次联合细化≤4；之后冻结候选，再作SELECT新增曝光核查、2 Native和≤8策略SELECT。
- LPIPS固定已接受AlexNet与线性权重、CPU float32、全部93帧432×768、原PTS；不得裁剪、缩放或抽帧。逐帧原分数、原视频SHA与完整均值保存。它衡量相对Native保真，不是独立视觉质量指标。
- GPU保持期间的CPU搜索、评分、文件保存都进入整卡实际GPUh；逐请求部署时钟排除诊断和评分。CPU post在GPU释放后运行，不虚增部署速度收益。
- 监督器每2秒采样；独立接受拒绝相邻或末次到结算超过45秒的监测空白、外部上下文和身份不一致。即使采样、评分或遥测失败，仍结算原实际费用、释放原租约，保留未达位置。终态没有自动重放。
- 独立终态从原始FIT/SELECT请求和全部逐帧评分重建图、DP、第一批、细化、角色去重、最终排序及策略；不是只信任runner写出的selected字段。
- 完整报价原件`manifests/cara_PG_P1_full64_whole_quote_r1_20261023.json`：forecast8.844444、limit10.5 GPUh，64路径、40对评分、2304pairs/4608CFG、单load。新卡独立预约，cap226，旧两卡16.5未知责任继续保留。报价未预扣加速或去重收益。
- 历史失配和少步Native保持P2既有设计、另行完整报价；不挪用当前价格11.5或P1的10.5上限。
