# V1：固定来源估值、整父计划留出与完整FIT选择组件

P0运行期间，V1的标量标签到候选计划CPU链路已接通，11项本地控制通过。当前可从完整64标签结构生成phase、phase+age、phase+age+previous-gap三组模型，各自用同一个双来源DP输出精确19D/22D的至多top3计划。完整FIT选择组件要求两个FIT、每候选全93帧，按输入等权Alex、代理成本、D序列字典序选择；缺失、失败或旧CHECK混入会拒绝选择。

这是合成标签与合成尺度的CPU组件证据；真实同状态采集、来源证明及完整生产入口仍待。没有真实V1标签拟合、端点收益或P1 GPU授权。

## 已固定的计算细节

[组件合同](../plans/cara_next_stage_20261101/source_lifecycle/V1_FIXED_ESTIMATION_COMPONENT_CONTRACT_R1.json)绑定原V1协议与64标签设计，保持原sigma/age/gap低阶特征及ridge1e-4。输入先各自对标签取平均，再对两个FIT等权；截距不惩罚，特征不标准化，使用FP64增广最小二乘SVD求解。负预测截零并报告比例。上述实现选择在真实标签产生前固定，不搜索阶数、系数或ridge。

每次留出一条完整父计划，横跨两个FIT：48行训练、16行验证，共4折。报告每输入误差、输入等权误差、截零、边际坐标超出训练范围和未见(t,a,b)比例。每个最终候选也报告预测状态的截零与覆盖范围。来源间距的增量由真实采集后的留出表现和完整视频判定；合成信号测试只验证信息流和计算。

入口要求原设计的64个不同FIT/parent/C-state，绑定父计划指纹、两个CFG分支最近两D来源、C/shadow D同状态标识及shadow前后父状态保持。目标由实际CFG差的FP64平方和除以元素数形成。拒绝旧S归一化标签、Native另一条轨迹、重复/缺失/外来位置或父写入。这里检查的是记录的结构和声明；生产采集器原终态及同状态/隔离控制仍须独立证明这些声明。

## 可运行入口与验证

- [估值与选择实现](../src/wcomr/cara_source_lifecycle_estimation_r1.py)
- [离线CLI](../scripts/fit_cara_source_lifecycle_v1_r1.py)：`--labels 完整标量包 --weights 原UniPC尺度导出 --output 新文件`。合成包必须显式加`--fixture-only`，原文件禁止覆盖；输出始终保留“待完整视频选择”和“生产来源尚未接受”。
- [11项本地CPU回执](../reports/cara_v1_fixed_estimation_CPU_component_r1_20261102.json)及[测试](../tests/test_cara_source_lifecycle_estimation_r1.py)：完整标量到18个候选位置的真实CLI、独立正规方程驻点核查、输入等权、整父计划留出、来源间距区分、负预测截零、全93帧选择与拒绝控制通过。

正式尺度入口只接受原36更新、精确sigmas/timesteps、固定UniPC源及当步corrector/predictor响应系数的平方；终点敏感度、部分尺度或异网格导出会拒绝。测试中的合成尺度不形成正式权重冻结。

测试开发中曾出现重复传入`actual_updates`的夹具构造错误，修正后最终11项全部通过；没有生产执行失败或GPU重试。原P0中央115份源码仍逐值匹配其已接受proof，运行stage未修改。

## 当前执行与剩余推进

[01:49原运维回执](../reports/cara_v1_P0_point20_goal_operational_r1_20261102_0149.json)确认P0四原句柄均活跃、4/14完成且0失败，独占唯一CUDA PID3110391，88°C，原90°C保护与1.95GPUh硬限保持。02:13半程、03:03原终验继续按[原交接](../plans/cara_next_stage_20261101/source_lifecycle/P0_POINT20_POST_LAUNCH_HANDOFF_20261102.md)执行，不创建重复检查。

下一步补真实标量采集器与父轨迹隔离/消费控制，组成完整Linux生产入口和完整P1报价；P0完整两状态接受后再判断机制是否继续。用户已选择P0先行，完整P1单独审阅；本次不缩减top3、公平搜索或强对照，也不启动P1 GPU。原四旧CAL/保护输入、旧冻结、搜索目标与费用口径保持。
