# CAL66 生产入口、历史桥接与真实质量资源准备

本轮仅CPU与资源准备，GPU提交和新GPUh预约均为0。原α、15身份/13正式角色、66路径、强基线、累计226GPUh与最终 `min(257.7712338712067秒, 0.8×fresh Native)` 不变。

## 已接受的生产入口

- source `f40cabdddea79f3ea6bda493f8d216aae9a2545f`；四卡独立GPU隐藏容器，1CPU/4GiB。
- 2026-10-25 16:29:33启动，16:40:56退出0；完整15角色×2重复×2flow=60实际采样CPU路径，60实际请求/guardrail拒绝边界，真实SetupArguments、NLTK与93帧编解码、FD锁传递。
- 两个新增 `SHARED24_A_PHASE_ALL` / `SHARED25_A_PHASE_ALL` 已覆盖原alpha和完整动作序列；重复guided/final/RGB均一致。
- 原件：[终态](../reports/cara_CAL66_entry_CPU_exited_r1_20261025.json)、[独立接受](../reports/cara_CAL66_entry_CPU_accepted_r1_20261025.json)。使用真实生产采样路径与明确小权重/解码fixture；不声称Cosmos GPU质量结果。

## 整卡组合与历史桥接

新CAL66监督、采集、释放后评分和独立终态组件保留完整66、6内部重复控制、48LPIPS/4464帧、52视频×3指标/156位置。两条外部历史桥接加原Native参考独立绑定旧104R2原件，核对视频、request、latent文件SHA和真实解码RGB。旧原件损坏拒绝；跨批数值不同则禁止历史合并，保留本批科学分母，不伪造一致。

本地首轮67项设计/终态检查通过。整卡CPU R1原派发响应超时，已恢复原句柄，仅实际执行一次；16:52:24退出1。66采集、历史原件读取、48/156评分失败恢复与真实93帧LPIPS已运行，但生命周期未完成，**整卡CPU尚不能接受**。

R1失败定位：监督器先取得空闲快照，随后ready文件刚好到达，被当成“已有ready但快照没有唯一runner”，在post_failure测试进入评分前即拒绝。真实原件见[失败终态](../reports/cara_CAL66_combination_CPU_failed_terminal_r1_20261025.json)、[生命周期诊断](../reports/cara_CAL66_combination_lifecycle_failure_diagnostic_r1_20261025.json)。新CAL66监督器改为先确定ready状态、后获取快照；未削弱唯一runner检查。加入确定性竞态CPU回归；旧106及已结束实验源码不改。

评分模型在独立模型stage中的子进程加载，继承释放后的CPU/内存限制；原始代码、权重、依赖overlay均绑定SHA，避免生产stage路径与模型CPU接受路径混用。GPU未释放、依赖改动或评分异常都拒绝。实际模型前向与93帧完整评分仍待本轮原件接受。

## 独立质量资源

复用原五模型的精确权重和原始VBench/MUSIQ源码，CAL66正式指标仍只有MUSIQ、主体一致性、运动平滑度。专用cache迁移及CPU准备不修改共用venv、旧实验或权重。依赖R1离线安装成功，但实际导入发现 `pkg_resources` / `filterpy` 缺失；原失败保留，补入固定 `setuptools==69.5.1` / `filterpy==1.4.5` 后重新导入核查。资源准备、真实模型CPU、完整视频评分探针必须分别记录，不能相互代替。

## 完整报价复核

[复算原件](../reports/cara_CAL66_combination_local_CPU_and_quote_r1_20261025.json)：

- 52正式+6计时重复+6预热+2历史桥接=66；2296pairs/4592CFG/单load。
- 生成5.13343588GPUh，加载0.15，保存/释放0.35，整体15%余量：预计 **6.47845126GPUh**；拟上限 **8GPUh**。
- GPU释放后48LPIPS/4464帧与156独立指标位置；2CPU、8GiB、6小时硬上限（最多12vCPUh）。实际质量模型吞吐仍需CPU验证，不将拟定时限写成实测完成时间。
- 当前无GPU执行授权/预约；旧两卡16.5GPUh未知责任保留。报价核实不等于新GPU准入。

本记录后续只追加实际CPU终态/资源检查，不依据未完成结果改变科学设计。


## 追加：CPU修复记录

R2于16:58:14启动、17:01:37退出1：新增竞态fixture把等待ready的屏障误放在runner生成前的idle准入检查，尚未派出fixture runner即超时。R2失败原件保留；R3将屏障移至第一次运行中快照，由真实CPU子进程与监督器明确握手，不改变生产独占门或GPU费用上限。本地组合/设计已70项通过。

依赖R2导入进一步检出原版imgaug使用 `np.sctypes`、与基础NumPy2不兼容；在专用overlay加入固定NumPy1.26.4，基础环境保持不变，随后再次核查。ViCLIP原传输达到30分钟工具时限，保留已传部分；仅在原SCP退出后核对本地/远端前缀SHA再续传，最终仍按完整原权重SHA接受，不替换模型或截断权重。
