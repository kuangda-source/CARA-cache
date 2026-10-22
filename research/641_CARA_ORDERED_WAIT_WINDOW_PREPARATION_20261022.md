# 按序完成等待期准备

**五项本地准备已完成：完整1624四卡入口、两个CAL_SELECT、P1分析/费用接口、强基线接口、论文机制图与伪代码。** 当前BANK24保持原句柄、10月22日20:33半程和10月23日00:17全程安排。新卡实际CPU在BANK24完整验收和既定同D/X-R离线分析之后执行。

## 1. 完整1624独立四卡入口

控制器 `scripts/wc_four_card_policy_assets_r1.py` 提供 prepare、deploy-cpu、recover、capture、accept、launch-gpu。新物理run `wc-policy-interval-assets-cal4-full1624-ada-r1`、stage `.sync/wc-policy-assets-fourcard-full1624-r1-20261022` 与当前BANK24分开。原科学run/config、四CAL、1624正式格、14完整路径、2030含warm格、13020读出试验及具体12GPUh批准保持。

当前部署包为 `manifests/wc_policy_assets_fourcard_full1624_package_r3_20261022.json`：185件overlay与1818件已验基础资料0冲突，7份生成源码可逆还原；R1/R2未发布中间包保留在ignored .sync。部署时对每件文件校验已提交HEAD字节，重新核验完整BANK24接受。

同一host PID容器承载原supervisor/runner、继承原flock FD；CPU隐藏GPU且项目只读，GPU绑定UUID、原账本结算后执行CPU post。旧两卡CLI关闭；未知派发只读恢复原stage/intent，不重新派发。原完整数值/生产/终态验收器复用。

新完整报价使用已接受BANK24实际load/最长完整请求，保留原额外读出、搬运、写读SHA、moments/完整输出相等审计和余量。它仍是完整采集规划价，不冒称已测独立动作单价。超过12则保留整卡，不缩格或拆卡。已批12无需重新确认。

完整新机CPU仍为原3命令：12单元、28数值路径/4060重载格/26040试验、4实际Cosmos请求/12拒绝；新增真实子进程FD/parent/namespace/竞争锁检查。本地11适配控制、原12采集回归通过，实际新机完整CPU尚未运行。

## 2. CAL_SELECT 已冻结

规则提交 `9fe9b778` 先发布；上游请求读取修正 `ba9c19f6` 再发布后才生成身份。选择读取已提交的7份曝光清单、1044个来源审计条目及固定WorldCache上游commit `60a486df6d2e6d2aa3c21815895aac157a88e95d`。排除58个成员，剩余105 AV组和880非AV组，分别按固定salt哈希取1个：

- `av_animal_dear_1_0`，seed0。
- `industry_057`，seed0。

原始prompt、request、source-group和SHA均在 `plans/cara_policy_generator_20261020/CAL_SELECT_INPUTS_R1_20261022.json`；recipe/P1 card已填写。未读取质量、未做拒绝筛选，拒绝不补选。固定身份仍需首次端点评分前核对服务器历史曝光元数据；若发现真实身份重叠，保留原冻结/冲突记录并修订选择协议，不按质量换样。最终TEST排除这两来源组。选样6项控制通过，当前结果可从已发布规则重现。

## 3. P1分析与费用接口已实现

入口 `scripts/analyze_cara_policy_calibration_r1.py`，格式与方法伪代码见 `plans/cara_policy_generator_20261020/ANALYSIS_AND_CONTROLS_R1_20261022.md`。复用原实测选择器，完整输出prompt等权LPIPS/时间、最差输入、尾部差距、代理与终点排序、离散成本保守量/实际残差、首批到修订增量。拒绝、失败、缺失保留完整分母。

物理费用event去重计费，逻辑Q单列，复用旧端点仍计信息，物理去重不增加免费候选。完整价覆盖须由原账单核实；当前没有P1实际端点或费用。

## 4. 公平对照接口已实现

`src/wcomr/policy_generator_r1/comparison_preparation.py`：原强前密C/A、固定C或全A1的refresh-only、端点评分前冻结的pure-proxy、同Q≤8的prefix/periodic简单搜索。共用实际B、CAL输入和原选择规则。P2待P1结果后固定完整矩阵与报价，不改P1原4+4规则。

分析与对照10项控制、原生成器与资产桥24项回归通过。连同11适配、6选样和12原采集，共63项相关本地检查通过。证据 `reports/cara_ordered_preparation_local_acceptance_20261022.json`，均非新增神经实验。

## 5. 机制图与方法文字已准备

`paper/figures/cara_window24_mechanism_r1_20261022/matched25D_readout.{pdf,svg,png}` 和 `provenance.json` 已生成，PNG视觉检查及SVG全部四场景柱形核对完成。原capture/acceptance SHA逐件复核，完整四CAL三臂25D对比未筛样。

论文主句：相同完整刷新位置与25次D下，持续修正降低终点失真；四场景均改善，A3相对C的等权LPIPS降低26.6335%，相对A1降低19.7690%。下一条主线是校准驱动的联合策略能否在同真实时间、可比校准成本下胜过强简单调度，并保持冻结后的新输入表现。

## BANK24之后的直接执行顺序

1. 按639原launch/capture独立接受BANK24全24、费用和退出，再完成既定同D配额/X-R离线分析。
2. 调用新控制器 `deploy-cpu`，参数为 `--package manifests/wc_policy_assets_fourcard_full1624_package_r3_20261022.json --bank-launch reports/wc_four_card_BANK24_full24_GPU_retry2_actual_launch_20261022.json --bank-capture <该次真实完整capture> --bank-acceptance <该次独立accepted> --output <新唯一CPU-launch.json>`。路径形式保持一致以复算原accept。该命令先算完整Ada报价，确认≤已批12，再单次新CPU；新GPU前再次检查实际资源和账本。
3. 按返回started_unix注册CPU半程+450秒、终态+1080秒。`capture --mode cpu-halfway|cpu-terminal --launch-ref <CPU-launch> --output <新唯一文件>`；完整终态用 `accept --kind cpu --capture <CPU-terminal> --output <新CPU-accepted>`。未知用 `recover --output <新恢复文件>`，只恢复原句柄。
4. 新CPU接受后，用 `launch-gpu --cpu-launch ... --cpu-capture ... --cpu-acceptance ... --bank-launch ... --bank-capture ... --bank-acceptance ... --gpu-uuid <fresh准入UUID> --output <新GPU-launch>`。从实际返回时间注册半程/终态；`capture --mode gpu-admission|gpu-halfway|gpu-terminal`，终态 `accept --kind gpu`。原12GPUh上限/完整范围不变。
5. 完整1624原件/参照相等和费用接受且generator_input_ready后，接PG-P1→P2→P3→P4原登记队列；P1还需真实价格、任意合法mask完整生产验证、完整自适应卡报价。每个新长卡按实际启动安排半程和全程验收。

本轮0服务器实验查询、0新CPU/GPU派发、不改当前BANK24已部署source或计时；54科研行不因准备和图表重绘新增接受。已有终态自动化接续本文件，不另建重复检查。
