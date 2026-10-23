# PG-P1生产入口与完整报价接续

最新证据：[656](../../research/656_CARA_PG_P1_PRODUCTION_ENTRY_CPU_ACCEPTED_AND_FULL64_QUOTE_20261023.md)。保持P1/P2原设计、原CAL_SELECT和当前价格GPU不变。

入口：`wcomr.policy_generator_r1.production_sampling.execute(inference, sample, policy=..., profile=..., **accepted_clean_kwargs)`。任意策略必须由`compile_policy`重建并逐字段一致；仅支持已接受Cosmos36步profile。执行返回完整请求分段时钟、实际36步语义历史与回退原因，A不写D锚点。

整卡引擎：`production_batch.run`。回调为Native完整请求、策略完整请求与同请求Native评分、独立Native时钟接受、可信bundle转换、首次SELECT增量曝光核查、持久化回执和实际GPU费用读取。此引擎已经通过本地完整状态顺序和失败控制；**真实GPU监督器/评分/时钟/终态回调的组合接受仍须完成**。

已验CPU：

```bash
.venv/bin/python scripts/audit_cara_pg_p1_production_cpu_r1.py \
  --capture reports/cara_PG_P1_production_CPU_terminal_r2_20261023.json \
  --output reports/<new_unique_acceptance>.json
```

无需重复启动CPU。接受源`56f31419`已包含入口、整卡引擎及原生成器代码；若生产闭包实质改变，另建stage并补受影响CPU，不能改当前价格stage。

复核本轮准备包：

```bash
.venv/bin/python scripts/prepare_cara_pg_p1_card_r1.py \
  --cpu-capture reports/cara_PG_P1_production_CPU_terminal_r2_20261023.json \
  --cpu-acceptance reports/cara_PG_P1_production_CPU_accepted_r2_20261023.json \
  --quote manifests/cara_PG_P1_full64_whole_quote_r1_20261023.json \
  --output reports/<new_unique_preparation>.json
```

上限64路径、40对评分、2304pairs/4608CFG，forecast8.844444/limit10.5 GPUh。原draft及recipe原件保留；这张新完整报价取代旧“报价留空”的当前状态，未改变科学设计。报价只用完整接受的BANK24历史耗时做规划，干净B仍在P1本卡Native阶段取得。

下一步把已接受独占价格/旧标签双SHA和真实生命周期接入新不可变PG-P1 stage，按10.5完整上限、fresh余额/UUID/锁/磁盘/内存准入。现有价格验收自动化仍负责完整接受后接续；本轮没有新GPU预约或提交。
