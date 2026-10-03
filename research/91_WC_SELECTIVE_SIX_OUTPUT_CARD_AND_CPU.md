## 实际部署通过，source27df749冻结

[实际部署回执](../reports/wc_selective_human_r1_deployment_20261004.json)：冻结source27df749a79ca3cb9fc3789a01bf1a73fa62211a2/deploy1，53payload+mid共54份文件逐一验证；actual r1/r2 CPU原件与33当前依赖、内部scope22、旧teacher与上一轮D/S原件视频、官方prepare、native-meta mode/buffers、source/assets/import/package和人物condition身份全部匹配。CUDA未初始化，原累计12h账本不变、磁盘约564GB，f1锁可获取。当前无新GPU/预付；下一fresh准入后仅提交此2400秒卡一次。

# 小层组与低频S六输出对照：源码、CPU与具体成本

2026-10-04。沿[90 已完成固定刷新诊断](90_WC_FIXED_HUMAN_RESULTS_AND_SMALL_GROUP_NEXT.md)，依当前自主推进goal和原累计12GPUh选择独立 WC-SELECTIVE-HUMAN-R1-20261004-A/wc-selective-human-r1。[具体卡](../manifests/wc_selective_human_r1_execution_20261004.json)/[配置](../configs/wc_selective_human_r1.json)。旧104点、旧人物四输出单次身份均保持终态，不复用授权窗口；本卡最多一次2400秒全cost、2370秒child/kill5，当前尚未GPU提交或reservation。

## 对照与问题

只用曝光human_199/seed0，保持原模型/条件、35请求/36实际UniPC、72 CFG、93帧768×432/16fps、WC70 horizon/14warm/最后两dense，以及同一38-deep离线官方掩码。S是sim0.1/cdf0.98/no-PV，6/23/27必须dense，不增加在线误差标签或当前/未来真值。

六输出全分母：官方adaptive D与固定D两条严格D/D，先通过九门、五处原生状态和完整pipeline。随后共用入口RNG、每臂真实prepare的四条测量如下。

| 测量 | S层 | S刷新频率 | 所回答的问题 |
|---|---|---|---|
| fixed D | 无 | 无 | 共同参考；三份D视频必须一致 |
| full S | 2..27除6/23/27，共23层 | 每个原本合格的刷新 | 当前代码必须复现上一轮full-S视频 |
| small S | 2/3/5 | 每个原本合格的刷新 | 只缩小空间/层范围的影响 |
| cadenced S | 同full S的23层 | 每CFG第1、3、5…个合格刷新用S，第2、4、6…个全D | 保持层范围，减少S频率并补充真D锚点 |

“合格”沿原warm/skip/paid-probe/两个过去真D等条件；计数按CFG分开，随着call70的原生cycle清空。低频未选S时确实执行全部deep D，得到的是本轨迹当前状态的真D；不意味着回到官方D轨迹。小组只要有一个S层，其整组缓存残差仍标为approximate，不混入true-D历史。全部六条实际deep动作必须仍等于38掩码，层/频率分别改变，避免同时改变两个因素。

先检查官方D与上一轮D视频SHA一致；轻量D也必须匹配。full S必须复现上一轮811365…90e1视频才进入两个新变体；不通过即技术止步，保留六输出分母及已完成文件。full-S重复是曝光开发复现，不是独立CONF。四测量顺序固定D→full-S→small-S→cadenced-S，各只有一次；保留首次核使用和必要mask/选择/来源/核检查成本，D/D观察wall排除，host分段不作独立CUDA耗时。

## 接口与实际CPU

[policy](../src/wcomr/selective_refresh_policy.py)冻结排序层集合、正整数cadence；[adapter](../src/wcomr/selective_refresh_diagnostic.py)沿固定掩码，仅对合格refresh选择层和S/D，计数可随来源snapshot恢复，负数或换策略拒绝。[六输出核心](../src/wcomr/selective_output.py)保留严格D/D、RNG/真实prepare与历史输出止步。[light sampling](../src/wcomr/light_sampling.py)新增明确reference_then_candidates序列选项，默认balanced保持。

[实际CPU r1](../reports/wc_selective_six_output_cpu_r1_20261004.json)87.790秒，旧固定四输出6条回归与首版新六输出12条控制通过。新增历史输出止步后，[实际r2](../reports/wc_selective_six_output_cpu_r2_20261004.json)58.031秒通过当前14条selective控制；r1→r2只改selective core/test两叶，r2实际覆盖当前33份依赖，旧default路径源码不变，[源绑定审计](../reports/wc_selective_six_output_cpu_audit_20261004.json)。没有把旧CPU追认后来修改的文件。

控制覆盖flow OFF/ON实际完整36/72/prepare六臂、三D产物一致、full-S所有sampler/pipeline边界逐位复现旧接口、指定层与逐CFG频率、间隔实际D来源重建、call70失效/尾dense、selector计数snapshot恢复、负历史拒绝、D/D失败、kernel失败、历史S不复现止步与全部hooks/modes/buffers清理。两轮Torch2.7.1+cu128都禁止CUDA且未初始化，账本不变；Toy模型、CPU核stand-in和mock writer不是实际稀疏核/视频、人物质量或速度结果。

[范围/成本/预算CPU22](../reports/wc_selective_human_r1_scope_cpu_20261004.json)通过六输出/固定三变体、同参考/历史止步、offline角色、完整成本、原累计12h/no-inflight/余额等变更拒绝。actual旧teacher和上一轮D/S原件/视频SHA绑定仍须在实际部署门核验，未因本地scope成功就称资源通过。

## 成本与执行边界

[完整成本草案](../reports/wc_selective_human_r1_cost_draft_20261004.json)：两D/D各保守381.751秒，四measure各旧最大214.335秒再加10%选择成本余量，加载95.916秒、bookkeeping75秒，再乘1.2并加30秒结算，合计2282.988秒≤独立2400秒。这是规划，不是实际GPU耗时。2400秒预付将计入原12h，终态包括导入/加载/失败/flush/释放按实际替换；当前累计7.7514316824275165/39jobs、余4.2485683175724835h保持，无新增GPU。

准备冻结53份payload与mid-config，并同步GitHub；实际核验CPU原件/对应源码、旧teacher/上一轮原件与两视频、官方prepare、native-meta mode/buffers、source/assets/import/package与当前human条件，然后fresh UUID/sm86/VRAM/compute/f1锁/无inflight/余额/磁盘准入，仅提交一次。不修改旧stage/原件，不自动后续卡、扫描、训练或新增人工评审。

终态独立检查六视频93帧、共同掩码、每种policy的实际执行层与逐CFG频率、间隔真D和近似cache来源、配置源码/全费用/原句柄锁GPU释放，自动算同一D参考下三候选PSNR/SSIM/temporal/帧差指标。小组层仅来自原104点单场景排序，不能作为人物安全性保证；候选是否有保真和净成本优势待实际证据。当前没有质量接受或论文前沿，Native/少步/调过WC/CONF仍缺，W3收益标签与训练保持后置。
