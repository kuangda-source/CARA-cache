# W3完整采集器CPU：72父路径、288状态、3456次配对

2026-10-15，接续435。**独立W3采集器已实现，本地原支持控制通过；完整服务器CPU尚未验收。** 原PA528/source715cae7与当前许可问题不动，新GPU不提交。

## 已实现的采集逻辑

每个普通H1更新保留原CFG两支执行与C/A/P0/D选择。固定标签位置额外执行C/A/D并逐次恢复物理模型／求解器／latent／条件／RNG和CPU owned状态，之后只将普通H1返回送入UniPC。三次额外计算不会推进因果历史、校准或来源。

历史只从普通父的pre-action来源／年龄、paid probe、原gain／支持与实际sigma构建。第一步UniPC还未初始化内部index时，读取其真实首网格并保留raw index=None；其余核对实际index等于step-1，不从整数timestep推sigma。标签以post-RF真实两支误差、CFG8/−7、FP64统计生成qC/qA及一次g²收益差；教师与特征分开。

原保护、age1–6、ρ/g缺失、未知表或缓存未就绪时，保留原未知标签位置，不强制绕开支持。不支持格子无需凑数做诊断；完整分母仍保留。实际额外C/A/D改变校准／来源则技术停止，不将污染接入父路径。

## CPU完整范围

生产拟议18路径／864最大pairs保持。CPU另明确覆盖两flow×D/P两个合成来源域，每域都运行原18路径完整模板（8正式＋1warm请求，各普通／诊断）：

- 72完整CPU父路径，普通36更新共2592pairs。
- 288诊断位置，每点完整C/A/D3对，共864额外pairs。
- 合计3456pairs／6912CFG，普通因果历史1296行。
- 检查每条普通／诊断父的全部36 guided、动作、A历史、终态和mock视频等价；每点3次完整恢复及teacher目标对应，source D/P两种均保留。

使用固定上游WC/RF/UniPC/inference原函数与28层Block；权重、attention、prepare/decode/writer是明确Toy CPU，不是实际生成模型或93帧质量。合成gamma0.5/C_scale1e9用于接口覆盖，真实H1 gamma0.7235237及表不改。已有八个开发输入名称保留，不能把Toy输出当其真实教师。

[CPU预登记](../manifests/wc_w3_label64_h1_collector_cpu_prereg_r1_20261015.json)、[完整范围](../manifests/wc_w3_label64_parent18_full864_scope_r1_20261015.json)。本地3项原支持／非提交选择控制已通过；初始测试夹具漏设正出生误差及试图修改immutable calibration的错误已修正，真实参数未改。

## 查收与下一步

独立目录 `.sync/wc-w3-label64-h1-collector-cpu-r1-20261015`，预计约15–25分钟，派发后25分钟一次查收原句柄；不连续监听，不覆盖任何旧stage。原GPU窗口账本前后SHA须一致，CUDA／真实权重禁止。

通过后再接真实生产入口、原件/拒绝post与完整forecast。当前费用UNKNOWN，无新增GPU卡许可，也没有真实标签／拟合／regret或视频结果。F/B结束、主线冻结、正式补验和PA具体询问保持，不新增人评／训练／OMR。

## 原R1唯一提交与预计查收

原任务于2026-10-15T05:06:05.146219+08:00派发：source `bb1976605812971ec4852a1a7846a02f10caa3c1`，CPU PID **855862**，独立stage保持原注册。估计15至25分钟，**next_check_not_before=2026-10-15 05:31:05.146 Asia/Shanghai（unix1792013465.146）**；自动化“W3标签CPU查收”已安排05:32仅查原句柄一次，当前未验收，不SSH持续监听／重启。原launch为 `reports/wc_w3_label64_h1_collector_CPU_r1_launch_20261015.json`。

下一次只核对全部源、完整72/288/864/3456、原父36输出／动作／历史／终态／mock视频、三次恢复、只普通推进的因果历史、三项原域控制和预算前后SHA；Toy／GPU区别保持。若未完，按剩余工作估时重新安排一次查收并结束，不循环等待。
