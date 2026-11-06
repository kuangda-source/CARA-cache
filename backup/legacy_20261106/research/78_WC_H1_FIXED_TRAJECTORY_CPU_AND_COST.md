# H1 固定轨迹三来源×复用长度：CPU 接口与成本草案

2026-10-03。状态 `CPU_WIRING_PASS_COST_DRAFT_NO_H1_GPU`。[H0 r2](77_WC_H0_MODE_REPAIR_AND_R2_CARD.md)的局部互补结果与旧失败保持；本轮只准备既定[65 来源×寿命设计](65_WC_HIERARCHICAL_PROVENANCE_LIFETIME_DESIGN.md)的第一层诊断。没有新 GPU、真实模型寿命、候选视频或可重启闭环分叉结果。104 点 r4 的单次 1800 秒授权已执行完，不用它授权下一实验。

## 1. 唯一问题与首轮范围

问题：同一刷新输入、同一后续官方轨迹和复用公式下，dense、matched-full、sparse 三种参考的局部误差是否随复用长度产生不同变化？首轮保留一个深层组 2..27，避免同时引入分组调度。不是当前训练/推理路由器。

首轮草案沿用 H0 的第二个已曝光 CAL 场景 `common_sense_6487f37f-ef57-49ca-afdc-d898922b5191`、seed0、93 帧、432×768、guidance7、Cosmos-Predict2.5-2B、共享 eval、官方 WorldCache/UniPC-Karras。35 请求步实际36更新的完整网格保持；诊断只执行前21次更新/42CFG。它是开发用中间分支点，尚未覆盖65设计的早/中/晚分层与独立场景。

H0 实测 step17/call33、34为两 CFG 的 eligible official full；先将这一位置作为草案固定来源点，要求新运行现场仍为 full、已支付 probe、有两份严格过去同 CFG 的真实 full 历史。失败不换点、不改阈值，不使用 shadow 来补历史。

| 来源点 | 同 CFG age | 未来 solver step | CFG calls | 三来源配对格数 |
|---|---:|---:|---|---:|
| step17 / calls33,34 | 1 | 18 | 35,36 | 6 |
| 同上 | 2 | 19 | 37,38 | 6 |
| 同上 | 4 | 21 | 41,42 | 6 |

固定分母6个来源臂、18个未来来源×age格，源/未来失败保持；没有自动补点或缺格平均。anchor 时 dense/matched-full/S 各1 warmup+3 hot，层6/23/27原 dense 回退、sim0.1/cdf0.98/noPV沿H0。未来每格只执行同一便宜缓存公式+head，不计算候选稀疏注意力、不复用旧QK mask。

## 2. 共同复用算子与来源语义

[h1_reference.py](../src/wcomr/h1_reference.py)保存 request/model/condition/CFG/group、来源 step/call/kind、严格过去真实 dense counter和不可变参考。matched-full/S均标记 approximate，不能作为 deployed true dense 锚点，也不写入 online cache 或只接受真 dense 的校准器。来源、CFG、条件、组、age、策略或快照发生漂移即失败。

对每个 CFG 取共同过去真实参考 `(R_p,P_p)`、当前真实浅层 probe 残差 `P_s`，只改变当前刷新得到的深层 `R_s^D/R_s^MF/R_s^S`。未来当前输入与已支付 probe 从同一官方轨迹读取；私有副本使用固定官方 cached branch：

```text
private deep window = [R_p, R_s^source]
private probe window = [P_p, P_s]
private residual_cache = R_s^source
current probe/input = unchanged official trajectory
prediction = exact pinned Gamma + optical-flow/warp branch + current head
```

官方源码 SHA `b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903`，由已有 `cached_branch_source`直接抽出共同公式，不重新解释或改写上游 warp。Gamma的浅层历史共同，但 flow依赖预测 hidden，因此来源误差可能改变后续 warp，不能假定来源误差线性可加。

Held reference在age0冻结到age4。中间即使官方轨迹重新 full，它也不随之更新；各来源共享这个固定反事实协议。它回答“当初保存的这份参考现在复用有何误差”，不等于官方继续刷新后的自然缓存轨迹。

## 3. 真值、控制与结果口径

[h1_lifetime.py](../src/wcomr/h1_lifetime.py)在来源点从相同已付 probe重放三个完整深层组+head；dense重复必须与当前部署 full 的 hidden/velocity逐位一致。只有当前官方路径更新部署缓存。所有来源快照保存在独立私有对象，结束再校验版本和原值 SHA。

未来三来源预测及评分原件都先完成并序列化，之后才计算同状态当前 true-D shadow两遍；两遍必须逐位一致，实际官方 full时还须与其真实 deep输出逐位一致。Shadow仅评分，不进入预测、调度或部署状态。每处恢复 RNG、buffer，默认 dense 算子与 `_w1_shadow_active`，保持官方输出/缓存/计数。共享输入、九项 parity与step13/21各36组件恢复门仍需新 GPU runner实际集成；本轮尚未把CPU toy当成这些完整真实模型门。

来源6个raw文件；未来每个CFG/age状态保存三候选+一个teacher，合24个，全部共30文件/60张量。它们是局部误差评分证据，不能当作latent+UniPC完整历史/RNG/CFG缓存齐全的可重启状态，也不是专家训练标签。

未来相对同状态当前D分别记录 residual/velocity 的 MSE、reference energy、relative RMSE和方向余弦。完整报告每格，以及配对有符号 `E_S(k)-E_D(k)`、`E_MF(k)-E_D(k)`。这个差不是稀疏误差的独立范数，负值可能来自抵消。先沿H0的5%作描述性局部保真筛查，并展示dense-held本身的误差；若三来源都漂移严重，不能专门归因于稀疏来源。

不预设误差随age单调，不从采样1/2/4推断连续安全寿命。两CFG来自一个已曝光场景，不能拟合可靠的统计交互或声称独立确认。当前固定轨迹不会用候选velocity更新latent；闭环寿命/最终视频及预算匹配策略需另外完整分叉卡。

## 4. 实际 CPU 回执与修复

[CPU r3](../reports/wc_h1_lifetime_cpu_r3_20261003.json)在已有Cosmos Python/Torch2.7.1+cu128中执行，禁止CUDA lazy init、无权重/真实模型前向，15.868秒完成。六项 reference 控制、四组 flow OFF/ON×全算/人工未来复用控制、一个非finite来源失败控制通过。每组42 paired calls/6 source arms/18 lifetime cells/30 raw；输出、buffers、缓存及计数完全一致，raw文件SHA与独立读取误差复算一致。外层inference_mode下的私有快照仍为可检查版本的普通no-grad张量。

CPU人工复用控制仅用于同时执行缓存分支，并在age3真实刷新部署缓存，证明它不会刷新held reference；GPU草案仍用固定官方原代码/原调度，不带该人工改写。Toy模块与合成kernel不提供真实稀疏精度、时间或寿命证据。

两次CPU失败都保留：[r1](../reports/wc_h1_lifetime_cpu_r1_20261003.json)复制namespace后没有重新绑定函数globals，诊断被绕过而完整coverage门失败；[r2](../reports/wc_h1_lifetime_cpu_r2_20261003.json)人工强制cache分支未设置局部`residual_x`，flow ON控制失败。分别修复独立AST函数绑定、人工分支变量设置后r3通过；没有删coverage门、补选点或追认旧失败。全部CPU轮次GPU账本不变。

## 5. 成本与下一执行门

[成本草案](../reports/wc_h1_lifetime_cost_draft_20261003.json)使用已审计H0真实组+head最大hot中位3.191秒、真实20步baseline201.970秒，及旧较保守前缀/加载观测。42-call前缀每臂按241.435秒；24次来源组和12次未来teacher组各给5秒；72次便宜reuse给150ms/次。H0 observed-baseline扣除中位replay估计后的未分类开销约82.964秒，按30/8评分文件数放大到311.114秒；它包含首用、状态检查、复制、哈希、IO等，不是独立IO实测。再加20%规划余量和30秒结算，包络 **1354.365秒**。

因此完整18格草案不能按1200秒规划准入。1800秒可容纳此估算，但只是下一张独立卡的候选上限，当前不执行、不复用r4已消耗授权，也不为挤进时间删除teacher重放或矩阵格。已有raw shape推算30文件约4.061GB、24份held张量约3.058GB，尚未包括活跃teacher/candidate工作空间和allocator峰值；历史H0监测峰24912MiB不是H1显存实测。当前数据盘584.697GB空闲只是资源观测，不等于GPU准入。

现场预算仍5.05310433089345/12GPUh、34jobs、余6.94689566910655h；指定GPU24MiB/no compute，未新增GPU成本。下一先完成单独runner、共享prepared-input/RNG与九门/恢复的CPU集成、失败完整回执；再冻结新identity/source/payload、明确单窗cost/timeout与实际assets/import/package gates，最后fresh GPU/全局锁/无inflight/预算准入。当前没有H1 GPU source/card封版，没有自动下一窗、H2、RV或训练。
