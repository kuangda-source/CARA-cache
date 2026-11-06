# 联合风险基线CPU对齐：已有完整浅层信号，成对probe接口与本模型校准仍需准备

2026-10-09。**已有数据足以准备联合风险基线的输入，但不能把联合公式直接插入当前单分支路由就称为RA-CFGCache比较。** 本轮查清了两个实际差异：当前WorldCache信号带saliency加权；当前闭包先完成条件分支，再计算无条件分支probe。二者都需要在方法定义与成本比较中处理。

原H-T48新seed GPU继续，没有改冻结配置或新提交。上一goal turn完成了飞书与相关工作核对，属于progress；本轮完成事前登记、实际CPU完整输入导出与源码顺序核对，同时现场核实原进程仍活，也属于progress及verified wait，不是等待批准或执行受阻。

## 本轮做了什么

按[H-T49 CPU登记](../plans/WORLD_CACHE_CFG_JOINT_BASELINE_READINESS_CPU_20261009.md)先提交`de6296a`，随后源码绑定到`d0b674592a8fedfa88f13adf8cc6972ff52ee54e`执行一次[标准库CPU程序](../scripts/analyze_wc_cfg_joint_baseline_readiness_cpu.py)。wall **0.051822秒**，完整回执见[CPU结果](../reports/wc_cfg_joint_baseline_readiness_cpu_r1_20261009.json)及[原stdout](../reports/wc_cfg_joint_baseline_readiness_cpu_r1_20261009.log)。没有读教师评分、加载大张量、拟合模型/阈值或执行生成器。

输入为已曝光且已完成的H-T45原终态capture、runner压缩原件、实际服务器两份模型源码片段与当前路由源码，以及固定版本官方Di/Tea代理。输入字节SHA与原runtime配置SHA全部绑定。实际服务器WorldCache文件SHA `b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903`、RF文件SHA `9b53e3f024e5cbb2cb3778819e1a6fd353923c13ad9b868d99602051640a65e8`与该旧卡一致；只读读取，没有修改运行目录。

全部两父、五起点×四动作×两重复=**40对/80个动作事件**保持，导出**10份同状态proxy记录**，含四细胞的paid input/probe drift、动态阈值、累积量、原生建议、实际动作、两分支真实full历史、solver配置指纹及执行序号映射。它们是五个相关起点的两次重复，不是十个独立科研样本。

## 查到的具体结果

| 核对项 | 实际观察与含义 |
| --- | --- |
| paid drift可用性 | 80/80事件包含有限的当前浅层信号；五起点的四动作在两重复中均有相同input/probe drift，10/10记录实测相同。没有假定跨动作proxy相同 |
| guidance定义 | 原请求guidance7，实际闭包`c+7*(c-u)`；标准`u+s*(c-u)`对应s=8。原FP32顺序保持 |
| WorldCache proxy | saliency开关实际开启，`delta_y`被weighted_rel_drift替换；不能把字段同名当成官方Di未加权proxy复现 |
| 分支anchor | S22、S23_after_CC、S23_after_DD共有相同最新full步；after_DC/CD是不同anchor。共三起点/六重复共享，二起点/四重复混合；不人为取max/min当共享anchor |
| 当前调用顺序 | 原velocity_fn先执行完条件denoise，再执行无条件denoise。原路由decide只接收当前分支的delta_x/delta_y；第一次深层决策前没有当前另一侧probe |
| 校准资源 | 本登记没有Cosmos自身rho表或传播先验。公开其他模型表、实际teacher cosine均没有当作在线输入 |

源自[官方Di代理](https://github.com/yiming-l21/RA-CFGCache/blob/e17d6a74ac2f7ca68d9ee9b8af8bfd9bc3886d8a/models/wan/racfgcache_utils/proxies/di_proxy.py)的代理选择与组合结构，只作源码对齐；没有执行或复现其端到端结果。上述输入导出也没有评估新调度的质量或速度。

## 下一步设计如何收紧

先完成原H-T48整卡，保留其原S22主假设和四个自身S23。联合baseline接入另用独立源码，不改在跑77文件：

1. 在同一次真实CFG更新中，先获得两侧当前浅层probe，再共同选择CC/DD；恢复后继续各自深层。需要完整父OFF/ON及原输出控制，前缀不能重复计费后又省略计时，也不能只比较proxy公式。
2. 区分“WC原加权proxy＋RA式组合”与“官方Di式proxy＋RA控制”。若改用未加权定义，应同时保留当前WC及简单共同刷新对照，阈值/校准在开发划分登记；不因一种接口更容易跑而替换原比较对象。
3. 给共享anchor联合控制建立自己的父轨迹；不要把after_DC/CD混合anchor状态硬塞入一个共享anchor表来宣称RA失败。混合历史仍可作为联合动作扩展的探索性诊断，须单列。
4. 先查可复用的校准资产，再形成完整成本与范围。若确需生成新校准，另登记具体卡、完整必要控制/重复与预算，不未经准备扩大一批视频；实际历史是否超出校准先验，仍需真实终点/未来成本干预。

此处是比较方法准备，没有新科学正负结论，也未选择新GPU。单次超过2GPUh需要具体确认，累计50GPUh及不增加不必要人评保持；不是因为baseline暂未准备好就否定W3或标记整个goal受阻。

## 原新种子任务的现场进展

[现场回执](../reports/wc_cfg_mechanism_confirmation_r1_joint_readiness_live_20261009.json)在服务器epoch `1791503156.5583017`确认原3409913/3409924/3409914仍活，source00b06e6不变。OFF父完成；ON已经进入真实嵌套动作对照，S22已保存2个完整局部pair，S23_after_CC的四动作×两重复8对完整，其他三个S23待。不是仅停留在初始化或旧21/36日志。

完整40对/120张量/20重复、两视频全93、224条件/76solver、有符号能量和最终费用仍待。没有接受一个完成起点作为整卡成功，也不在GPU活着时评分成功子集。已结算底数26.279085386/50GPUh，第63在途额度预留50仍待原完整wall结算；现有释放后CPU程序继续等待原GPU，不重启/重投。
