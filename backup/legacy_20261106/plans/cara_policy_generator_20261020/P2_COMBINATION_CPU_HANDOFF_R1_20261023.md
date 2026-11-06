# PG-P2 整卡组合 CPU 接续

最新质量与绑定准备见 `plans/cara_policy_generator_20261020/P2_QUALITY_AND_CARD_BINDING_R1_20261023.md` 和 `research/667_CARA_PG_P2_REAL_QUALITY_ENTRY_AND_CARD_BINDING_PREPARED_20261023.md`。原R2组合CPU保持已接受；新增质量入口本地准备不等于五模型实际CPU。P1接续脚本现在还要求原组合CPU的 `--combination-capture` 和 `--combination-acceptance`。预算继续等P1验收和去重。

## 2026-10-23 22:54 最新接续：组合 CPU 已接受

已完成本人旧文件452个重复对象的只读无损去重，释放11.97GiB，保留原路径/SHA及恢复清单；P1原runner与登记源码不变。完整记录见 `research/666_CARA_LOSSLESS_ARCHIVE_AND_PG_P2_COMBINATION_CPU_20261023.md`。R2组合CPU原容器22:54:33退出0，22:54:52完整收件；`reports/cara_PG_P2_combination_CPU_check_r2_20261023_05.json` 与 `reports/cara_PG_P2_combination_CPU_accepted_r2_20261023.json` 已独立接受。48采样/72请求、真实93帧LPIPS、6生命周期、32组合检查通过；五项质量模型仍仅协议/分母控制。**复用本次原件，不再部署或重跑组合CPU。**

R4原入口CPU继续用于现有P1绑定脚本，新组合接受为附加证据；最终实际卡runner/采集器、质量模型资源及P1策略绑定仍需核验。P2预算等P1完整结果及物理策略去重后确定，没有新增GPU预算或提交。下述旧资源失败与执行命令保留为历史，已由本节替代当前状态。

用户要求：不影响 P1；预算等 P1 完整接受、策略物理去重后再确定。本次不重算预算、不提交 GPU、不预留费用。旧 518 路报价只保留为历史未去重上界。

## 本次交付与实际边界

- `p2_combination`：完整登记分母先保存；请求和评分失败保留原件/未到达位置，拒绝重写角色与少步 Native 更新数。完整93帧 LPIPS 复用已接受实现；5项独立质量维度沿 N10 原始证据验证，不合成总分，失败不能变成 NA。
- `p2_terminal.accept_lifecycle`：核对 frozen source/manifest/授权、原 guardian/runner/容器/UUID/锁、连续独占≤45秒、实际费用和权威结算、独立 post 原件。科学原件审计另由 `audit_registered`/历史双分支审计及 P1 OFF 原件复核组合，不能用生命周期通过代替科学接受。
- P2 专用 supervisor/hostguardian 与六类真实 CPU 子进程/行政命令 fixture；继承 P1 的监督结构但独立文件，不编辑 P1 实现或 stage。
- `check_cara_pg_p2_combination_cpu_r1.py` 在新源闭包内重做48路径真实采样CPU、实际93帧LPIPS回调、六类生命周期和32组合检查；`audit_cara_pg_p2_combination_cpu_r1.py` 独立接受全部原件。

本地75项检查通过，包含32项新增组合/终态检查和43项已有接续控制；独立接受器1个显式合成正例+14个反例通过。全518路径、346组LPIPS、1600质量位置和账本均为**合成控制数据**，不是模型输出或真实开销。该本地阶段的真实48路径采样CPU以R4为准；后续R2组合执行已独立重做并接受，见文首。

**历史R1阶段（已由文首R2接受替代）：当时新的生产组合CPU未启动。** 当时部署在创建stage之前被原40 GiB磁盘门槛拦住。原柄核查确认 stage/container/launch 全不存在；没有任何原任务可恢复，也没有 GPU/账本/模式操作。旧 CPU 目录总量不足1GiB，系统盘仅约0.21GiB空闲，未清理或迁移任何文件。不得把 `CONNECTION_OR_REMOTE_CHECK_UNKNOWN` 的统一包装误判为 SSH 不通：已核实实际是准入 assertion，连接可读。

## 资源允许后的执行（历史命令，R2已完成）

先读当前状态及 research/665，确认没有新的同任务回执。保持 MemAvailable≥24GiB、原共享盘空闲≥40GiB；不降低准入线、不清理其他用户或P1文件。新P2源闭包和控制器应先提交推送，并核对Git HEAD。

```sh
.venv/bin/python scripts/wc_four_card_cara_pg_p2_combination_cpu_r1.py deploy \
  --stage-name cara-pg-p2-CPU-combination-r2-20261023 \
  --output reports/cara_PG_P2_combination_CPU_launch_r2_20261023.json
.venv/bin/python scripts/wc_four_card_cara_pg_p2_combination_cpu_r1.py capture \
  --launch-ref reports/cara_PG_P2_combination_CPU_launch_r2_20261023.json \
  --output <新唯一技术或完整回执.json>
.venv/bin/python scripts/audit_cara_pg_p2_combination_cpu_r1.py \
  --capture <完整退出0原回执.json> --output <新独立接受.json>
```

若日期/stage已存在，先读取该stage原启动和容器；UNKNOWN只核查原句柄，不能盲重派。每个CPU容器仍为GPU隐藏、1CPU/4GiB、只读root、离线；实际生产模型生成权重不加载。评分仅真实加载既有CPU LPIPS权重，五项质量模型本次只有协议/分母控制，最终资源绑定及真实模型入口核验仍须完成。

## P1 接受后的绑定顺序

1. 独立接受原 P1 终态与策略；复用R4采样CPU绑定历史角色、原P1 OFF参照、Native18–35网格，不从诊断效果选策略。
2. 复用已接受R2组合CPU及原件；最终 raw branch/OFF 回调必须接真实张量/逐帧核验，不能使用fixture布尔值。实际P2整卡runner、采集器、模型资源与生产授权在最终manifest上绑定验证。
3. 物理策略去重，保留全部方法角色与查询账。Native匹配在新DEV质量之前冻结。明确全部CAL/新DEV来源分组及seed。
4. **到此才确定完整实际矩阵和预算**，结合P1实际结算与226池余额办理原流程中的整卡批准。不得把旧78.5GPUh上界当作批准或自动拆成90路子卡。

`p2_combination_stage.validate` 当前明确拒绝真实GPU准入，直到上述绑定完成。已有 P1 半程00:52、全程05:32保持；只向同一终态检查补充本接续，不新增重复任务。
