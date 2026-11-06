# 已付probe参考与深层工作源：源码时钟核对及下一对照

2026-10-12。此项来自对冻结WorldCache代码的只读核对，不使用388尚未完整验收的teacher胜负，也不改在途source4d51485/652、16选点、γ、风险定义或费用。静态证据见[源码审计](../reports/wc_probe_and_working_source_clock_source_audit_20261012.json)。

## 核对到的定义差异

实际pinned WC SHA `b485cb8f...`：

- paid `delta_y` 在源码323行计算当前浅层`test_x`与`previous_internal_states`的相对L1变化。
- C分支457/458行把`previous_internal_states`更新为当前probe，把`previous_input`更新为当前输入；该分支没有写`probe_residual_cache`或`residual_cache`。
- D/P实际深算分支530/532行更新深层残差与工作probe残差。物理P在此处仍是“执行深层、其中部分MLP近似”的计算路径，不晋升可信D校准历史。
- 成对前向编译保留原源码，仅改选择边界；定义上最近probe参考、工作残差出生点、可信D校准点是不同对象。counter70的缓存清空尾部必须单独处理。

这说明，通常连续C期间，paid `δ_y`是最近probe参考的短程变化，深层来源年龄仍随C增长。不能仅因为rho按working birth索引，就称δ_y是在测从那个出生点到现在的浅层累计变化。也不能把`probe_residual_cache`（probe减原输入、工作出生时保存）和`previous_internal_states`（每步更新的probe绝对输出）当同一个张量。

这不是已确认的实现错误；旧π0和RA沿用这个信号仍可能有效。它说明下一误差表必须把测量对象说清楚：最近变化小与深层缓存仍准确不是同一命题。静态源码审计也不替代实际缓存/别名/flow全轨迹观察，当前报告没有新增GPU、teacher或这样的runtime shadow。

## 对既定16点分析的影响

389主分析保持已登记的`(δ_y+b_proxy)^2`及source/phase表，不追改目标、不按未完成标签挑特征。此feature是经验代理；四格固定目标年龄3/2/2/1，因此留一场景不能证明跨来源年龄泛化。继续单独报告source、working birth/age、true-D anchor/age和实际读出。

H2的未来漂移外推需另外核对它使用的σ区间：若测量是近一步变化，分母也应与该观测间隔一致；不能默认它是source出生到现在的累计变化。这里仅登记待核对，不预先判定当前H2公式错误。

随后已读取两版event/controller：当前slope确实是paid δ除以`|σ_birth−σ_current|`，刷新后再乘新出生点到未来的σ间隔。纯代数线性probe/固定归一化对照中，旧出生σ=2、前一步1.1、当前1、下一步0.9、已付一步δ=0.1时，现式对新来源下一步给0.01，一步斜率给0.1；平方代理为1/100。出生恰为前一步时两者一致。这个控制只说明观测间隔和状态间隔混用可产生结构差异，不能用它宣称真实视频误差100倍或H2负结果已经归因。[源码绑定及两控制](../reports/wc_probe_reference_sigma_span_algebra_cpu_20261012.json)。

下一版应把观测间隔、到working源的当前差分和更新后新源区间显式分开；不简单换分母后沿用旧κ/λ，不追改已完成H1/H2或在途16。既定389模型与低成本CPU observer先做完，再实测是否影响选择与终点。

## 低成本区分实验登记

先做纯CPU observer：两flow、完整普通π0路径，观察每分支的当前输入/probe、上一probe参考、working probe残差、来源出生点、可信D校准点、counter尾部清空和对应输入/σ。要求全部36guided、动作、终态与无observer基线一致，不修改任何缓存、RNG、条件或选择。区分张量对象身份和数值同一性，避免把相等数值当成同一个历史对象。

如果CPU证实契约，在后续实际卡的普通父重放中增加**parent-only**的廉价来源统计，不重新执行同状态teacher：

1. 保留已付最近probe变化δ_y及其参考时刻。
2. 记录从实际working probe残差到当前`probe-original_input`的差分，标明坐标和归一化分母。
3. 区分working age、true-D参考龄和近一步σ跨度/working出生σ跨度。
4. 在原16固定点核对输入和父轨迹哈希，与388原件teacher/C/A/P标签一一绑定；不新增或补选状态。

可先比较当前source/phase表、加入source age的受限模型、直接来源差分模型。新增假设在读到对应完整标签前登记；拟合只用开发数据，保留有害状态和缺失格。融合γ及主16分析不变。来源差分不是免费特征：其范数/reduction、同步、保持第一CFG分支统计的内存与恢复状态均需计时和归属，再决定是否部署。

若与390四父/八后缀合并，只在普通parent上观察，子后缀不得推进parent observer时钟；恢复全部scalar状态或显式保持正确前缀。按合计完整范围/费用验收，不因为名为observer就免除源码/生产CPU/唯一GPU和<=8规则。当前只登记，没有启动新真实卡，也不扩大原暂缓P13h或替换E2原76。

## 公平对照保留

后续论文主比较继续保留官方WorldCache、RA、合理少步Native，以及同mask/同实际费用的简单调度。现有五方法三档64科学位置曲线仍是已登记的开发问题；如补这些强对照，须整体修订曲线范围并估费，不能暗中删减原控制或把不同批次秒数拼成同卡结论。
