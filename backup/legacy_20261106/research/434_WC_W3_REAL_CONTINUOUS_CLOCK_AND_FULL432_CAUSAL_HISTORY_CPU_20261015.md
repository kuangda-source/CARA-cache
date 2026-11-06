# W3 真实连续时间坐标与432步因果历史

2026-10-15，接续[433 PA封口](433_WC_P_ACR_WHOLE528_LAUNCH_CPU_AND_NEXT_DECISION_20261015.md)。**W3 历史的连续sigma缺口已经通过真实scheduler CPU重建补齐，12条H1轨迹／432步全部对齐。** 当前仍缺真实同状态C/A/D标签，没有拟合预测器、在线动作或视频收益。PA528具体许可保持待回复，新GPU没有提交。

## 如何取得真实坐标

读取已接受715cae7／R2的runtime绑定，核对实际UniPC SHA f6a06c75与RF SHA c6c68f29。真实RF初始化 `num_train_timesteps=1000,shift=1,use_dynamic_shifting=False`；调用原scheduler的 `set_timesteps(35,device='cpu',shift=1,use_kerras_sigma=True)`，不导入或初始化生成模型。

服务器使用原生产Python／原diffusers／Torch2.7.1，真实类完整导入，CUDA、权重、下载禁止。生成36个int64 timesteps和37个float32 sigmas（含终点0）。原生产逻辑的Karras路径在当前固定设置下与输入内容无关；全部12条已保存的H1 timestep序列逐位匹配。**这是固定版本scheduler重放，不是原运行逐步保存的sigma**，二者在回执中明确区分。不能仅把整数timestep除1000当成连续sigma。

原原件、E0记录和715cae7 PA stage不修改。真实CPU审计约10.99秒，GPU／模型／权重0，预算SHA前后一致。[原生重放回执](../reports/wc_w3_actual_schedule_native_CPU_replay_20261015.json)、[实际调用点](../reports/wc_w3_actual_schedule_callsite_readonly_20261015.json)。

## 全部历史与隔离检查

按四场景×三λ完整12条H1、432步重建T1当前13维和T2前缀27维；先按全部整数时钟匹配，再使用对应原生连续sigma。每步依旧只取已付两支probe标量、当前来源／年龄／root floor及旧合法支持，保护步缺probe保持缺失，D31的age7回退保留。

12条逐一检验：改变第30步以后的漂移不会改变前29步特征；改变旧H1 `scores` 中的误差估计／费用评分不会改变任何特征；修改一项原timestep被拒绝。原E0对象保持不变，没有把旧估计误差当新teacher。

432条的source、sigma和前缀schema已独立复核，12项D31回退保留。历史ID仍只是回执行身份，不能当物理可恢复snapshot或与别轨迹标签硬合并。[完整重构](../reports/wc_w3_h1_full12_continuous_clock_causal_prefixes_cpu_r1_20261015.json.gz)、[独立接受](../reports/wc_w3_h1_continuous_clock_prefixes_independent_acceptance_20261015.json)。

## 对下一步的影响

这解决了“有漂移历史但没有连续坐标”的准备缺口，今后实际同配置新采集可记录native sigma并与该重放桥接。**真实C/A/D教师标签仍是首要缺口**；当前0标签、0拟合、0额外GPU，没有新的regret或调度收益。

拟议W3八个EXPL_DEV提示词／64位置的名单、同状态采集器、原父等价与完整成本仍待锁定；不能用这432条旧CAL特征充当新独立测试，也不能用H1表误差反向监督自己。P与W3仍独立，F/B不恢复，原A/H1与正式五项补验保持。

下一安全工作为W3真实标签采集的完整范围和CPU接线；实际新GPU仍须明确恢复许可。原PA528源715cae7／7.529994forecast和已有询问保持，不重复询问、不覆盖stage或重置预算。
