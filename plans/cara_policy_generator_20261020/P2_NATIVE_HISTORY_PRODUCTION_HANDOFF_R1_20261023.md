# PG-P2 历史诊断与少步 Native 生产接续

本轮只准备 P2，不变更正在运行的 PG-P1 source/stage/配置/句柄，不提交 GPU，不写费用账本。完整 P1 终态及最终策略仍是依赖；CPU 通过表示实现控制通过，不是历史失配或少步 Native 的科学结果。

## 已实现入口

| 模块 | 入口及行为 |
|---|---|
| 少步 Native | `p2_native_sampling.execute`；18–35 请求步，逐项核对固定 UniPC 的 timesteps/sigmas、首末完整 Block 调用数；生产使用原网络 class forward，不安装 WC 缓存 |
| 历史失配 | `p2_history_sampling.execute`；在策略自身轨迹的同一状态上，对真实 `[p,s]` 和影子邻接 `[s−1,s]` 两窗口分别执行 C/A_HALF/A_ONE；shadow D 不提交给父轨迹 |
| 请求与原件 | `p2_production_requests.Requests`；原请求身份、seed、策略和步数绑定；保存视频/最终 latent/请求 JSON 的 SHA；原目录已存在就拒绝重复执行 |
| 完整计时块 | `p2_production_batch.run_timing`；先 28 条 CARA/Native35 基准，再最多 56 条 Native 候选，按登记顺序轮换；只读实测时间，完整位置先保存，不丢弃拒绝或失败 |
| 历史矩阵 | `p2_production_batch.run_history`；最多 6 路，策略 fingerprint 去重但角色保留；3 个间隔组各取首个合法点，空组保留 |
| 原件复核 | `p2_history_analysis.audit_record`；重读双分支张量，验证 SHA、来源/状态身份及误差重算；A_ONE 对较早锚点逐位不变，常量秩相关/零分母为 null |

以上 Python 模块在 `src/wcomr/policy_generator_r1/`。采样只处理冻结的计划；任何循环/监督仍必须由已接受的完整卡控制器持有锁、费用和独占上下文。当前不提供绕过这些条件的裸 GPU 派发命令。

历史记录导出两窗口双分支 C/A_HALF/A_ONE（A_ONE 即 Phi）及共同 D；记录父状态、输入、两真实锚点及邻接影子锚点身份。不导出完整隐藏状态 bank。教师参照使用旧 1624 同 member/source/target 的二次误差代理，明确区分它与新自身轨迹的实测误差。影子请求费用计入整卡，但不进入部署延迟表。

原规则维持：首两 CAL_FIT、seed0，最终 CARA 与 SELECT 已选择的最强可行简单控制；最多 6 路/36 额外 D pairs/108 paired readouts。P1 已接受的同成员/seed/策略 CAL_FIT 原件作为 GPU shadow-OFF 参照，绑定原 video 和 latent，不增加未报价的 OFF 路径。

## CPU 验证与接受

隔离 stage 使用固定镜像、无 GPU 设备、1 CPU/4 GiB、离线运行，不修改现有 P1 stage。入口为 `check_cara_pg_p2_production_cpu_r1.py`：

- 实际 Cosmos SetupArguments，以及四 CAL × 18 步数共 72 真实请求构造与 72 个无 guardrail 拒绝控制。
- 实际 NLTK 分词、93 帧生产 writer/解码/ffprobe、继承 FD 锁控制。
- 两种 flow × 24 条完整小张量路径 = 48 条：每种 flow 包含 18 个 Native 步数、alpha=.5/1 两组历史 OFF/ON 四路、生产请求适配器 Native/history 两路。
- 历史 OFF/ON 全36 guided、最终 latent、93帧 RGB 逐位一致；三种间隔组、6 次 shadow pair、双分支保存重读、原件 SHA/锚点身份改写被拒绝。
- 整块计时 84 位置、顺序轮换、质量字段拒绝、缺失/重复/独占失败控制；秩并列与零分母控制。

CPU 小张量使用固定上游真实调度器/采样/RF/WC 代码及显式小权重/简化 attention 和 decoder。没有加载真实 Cosmos 生成权重，不声称生成画质或 GPU 性能通过。实际 tokenizer/codec 是单独真实生产边界检查。

使用独立接受器 `scripts/audit_cara_pg_p2_production_cpu_r1.py --capture <完整原 CPU 回执> --output <新接受>`。以最新 research/663 和当前状态指针为准；早期失败原件保留，运行中的 capture 即使文件名含 terminal 也不是终态。

## P1 通过后的确定性绑定

```sh
.venv/bin/python scripts/prepare_cara_pg_p2_after_p1_r1.py \
  --p1-capture <PG-P1完整原终态.json> \
  --p1-acceptance <PG-P1独立接受.json> \
  --cpu-capture reports/cara_PG_P2_native_history_CPU_complete_r4_20261023.json \
  --cpu-acceptance reports/cara_PG_P2_native_history_CPU_accepted_r4_20261023.json \
  --output <新唯一P2绑定.json>
```

该命令重算 P1 全部原件/评分/选择/独占/账单接受，检查接受回执绑定原 capture SHA，再独立重算 P2 CPU 接受。只从原 SELECT 可行排序选择简单控制，不从诊断效果选它。没有合法最终策略或可行简单控制则明确停止绑定。输出精确历史矩阵、P1 shadow-OFF 原件身份和全 Native 调度网格；不提前选择新 DEV。

随后还要完成整个 P2 的监督、独占、评分和终态组合 CPU，绑定最终全部对手/来源分组/新 DEV 规则及完整报价。Native 计时选择发生在新 DEV 质量之前；CAL 时间 ±2% 匹配不等于新 DEV 时间已经匹配。无法匹配就保留实测相邻夹点或 NO_CAL_TIME_MATCH，不增加查询补搜。

## 完整费用准备

`manifests/cara_PG_P2_whole518_planning_quote_r1_20261023.json` 是**未去重完整 P2 上界**，可由 `prepare_cara_pg_p2_whole_quote_r1.py` 重算。它包含：

| 范围 | 完整路径上界 |
|---|---:|
| CARA/Native35 基准与四个 Native 候选重复计时 | 84 |
| 两策略历史诊断，含 warm | 6 |
| 同 Q 简单搜索完整校准，含 Native、warm、FIT、SELECT | 64 |
| refresh-only C/A 与 pure-proxy 的 CAL/warm/SELECT | 24 |
| 16 新 prompt × 2 seed × 最多 10 方法角色 | 320 |
| 新 DEV 每方法两 warm | 20 |
| **合计** | **518** |

10 个角色包括 CARA、前密 C/A、refresh-only C/A、pure-proxy、同 Q 简单搜索、Native35，以及无 ±2% 匹配时的两个少步 Native 夹点。实际相同策略按身份复用，保留每个方法的信息查询账；当前未领取任何去重折扣，也未观察新质量。

另计 36 shadow D pairs、108 paired readouts、346 组全93帧 LPIPS、最多1600个独立质量维度位置、模型加载、搜索、分支导出与哈希、独占收尾。生成以已接受 BANK24 的最大完整请求 306.199 秒估算；质量以已接受 N10 五维逐项最大时间估算，再统一加 25% planning margin 与 15% limit margin。评分资源占有时间已计入，不把 CPU 评分期间仍占卡的费用漏掉。

完整 P2 forecast **67.878889 GPUh**，保守 limit **78.5 GPUh**。其中 Native/历史90路子模块 forecast **11.408889 GPUh**、limit **13.5 GPUh**，已经包含在整体，不是额外费用或独立派发授权。这些是准备报价，不是实测 P2 耗时，也不是最终批复。

当前已保存账本 available=66.437172 GPUh（P1尚预留10.5）。完整未去重上界暂时高于该余额；等 P1 原结算及策略去重后重算实际完整矩阵和余量。不得以分割 Native/历史/主表来规避整卡≥12 GPUh的明确批准规则，也不自动改动累计226 GPUh。只有届时可审阅的最终范围、完整报价和实际资源明确后才提交具体批准问题；本轮继续完成无需GPU的工作。

## 2026-10-23 后续接续更新

整卡组合代码与本地75项/接受器15项控制已完成；新远端组合CPU被40GiB磁盘门槛拦住，未启动。继续以 [P2组合CPU接续](P2_COMBINATION_CPU_HANDOFF_R1_20261023.md) 为准。用户明确最终预算等P1接受和策略去重后决定；上述数值保持为历史上界。
