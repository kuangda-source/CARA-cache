# Euler35 协议差异与 CPU 边界

2026-11-01。E1是当前唯一待推进GPU问题；Euler仅E0源码和CPU准备，不作为E1前置依赖。本轮没有改变原UniPC代码、模型权重或已冻结输出。

## 源码核对与已完成控制

从两卡当前runtime只读取得三份固定源码，与原登记SHA吻合：

| 源文件 | SHA256 |
|---|---|
| video2world_model_rectified_flow.py | `9b53e3f024e5cbb2cb3778819e1a6fd353923c13ad9b868d99602051640a65e8` |
| text2world_model_rectified_flow.py | `c6c68f297859e11c76d2921667a29cabfecef3a7b5d3ab831bf9bb54b25b7d87` |
| fm_solvers_unipc.py | `f6a06c75f059693ade6c802e99f6058575969b6a71ef18ab05e7ed46701053d3` |

实际视频子类的CFG函数为`v_c + guidance*(v_c-v_u)`，请求7即8C−7U，先C后U。不能误用文本父类的`v_u + guidance*(v_c-v_u)`；本次CPU直接执行视频子类未改动的CFG闭包AST。原UniPC把flow输出换算为`x0=x−sigma*v`，因此Euler使用`x_next=x+(sigma_next−sigma)*v`，不另翻转速度符号。

已完成：原UniPC36网格与原卡逐值相同；Euler原型35更新/70CFG；常速度解析终点、手工CFG轨迹核对误差均为0；错误时间步和额外更新拒绝；六个现有19D布局的噪声坐标映射均定额、无重复且保留前七和末点。没有加载模型或调用CUDA。

- [完整sigma/timestep和SHA契约](euler/sigma_grid_and_call_contract.json)
- [CPU接受回执](../../reports/cara_euler35_E0_CPU_acceptance_r1_20261101.json)
- [隔离的数值原型](../../src/wcomr/cara_euler_protocol_r1.py)

## 两个不同问题

| 项目 | E-SOLVER | E-PAPER |
|---|---|---|
| 科学问题 | 单独更换更新器 | 论文式协议重建 |
| 网格 | 使用原UniPC完整37个sigma（含终点0），36更新/72CFG | 明示35正sigma+终点0，35更新/70CFG |
| 超参 | 保留原所有WC等配置 | 独立登记论文式WC设置 |
| 当前状态 | Euler能消费同一显式网格；未完成真实UniPC/Euler配对 | Karras rho7重建原型已CPU控制；论文未公开精确sigma数组 |
| 可以声称 | 设计了可比控制 | paper-style reconstructed |
| 不能声称 | 已证纯solver因果效应 | 官方逐位复现、Euler视频已接受 |

本次35网格是明确的新重建：EDM sigma从200到0.01、rho7、35个等距rho坐标点，再变换sigma/(1+sigma)，保存float32 sigma及原规则int64时间步。它与原请求35产生36个正sigma的路径不同。不得从两个协议的速度差直接推导缓存增量。

## WC参数与仍需处理的差异

[WorldCache原文4.1与附录](https://arxiv.org/html/2603.22286v1)描述Euler35；本地README和论文式配置需分列。论文式目标为阈值0.08、motion2.0、saliency0.12、warp空间scale0.5、ATS系数4。完整sigma、精确实现版本与运行环境不能由这些参数唯一确定。

当前wrapper共享`worldcache_num_steps`作为分支计数horizon和ATS系数输入：horizon70时系数是5，不能一边保留70调用末尾重置，一边声称系数已是4。将horizon改35会在中途重置，同样不是正确适配。未来需隔离新增Euler适配，明确分开“70分支调用horizon”和“ATS beta4”，通过边界CPU后才能用。

原F19等规则是36更新的策略，不能直接复制整数步号。原型采用归一化log-SNR坐标的有序一一匹配，固定保护前七/末点；示例不选择科学方法，不是已经成立的跨网格生成算法。D24保护点对应关系、区间年龄/尾部间隔约束、22D/25D预算配方需随E1胜出方法前瞻冻结，不从Euler输出补调。

## E0尚未关闭的硬门

1. 将显式Euler更新器接入完整生产Native/WC wrapper并验证同初噪、每步、最终latent及RGB；当前只有实际CFG函数与数值原型CPU，**完整wrapper CPU未接受**。
2. 单独实现WC horizon/ATS解耦，保留原UniPC行为及源码身份；不把新版参数塞进正在使用的旧入口。
3. 固定noise-coordinate策略生成约束、source/grid SHA、Euler自己的Native参考和双时钟。
4. 真实权重Native/allD对照是未来单独授权Euler卡的前置路径，不能由微型CPU替代。

后续Euler GPU必须等UniPC端点支持并冻结一套方法；任何2输入×4角色的8视频只是正式部分，控制、warm、重复、失败分母和全额费用另列。不使用保护TEST进行Euler开发。
