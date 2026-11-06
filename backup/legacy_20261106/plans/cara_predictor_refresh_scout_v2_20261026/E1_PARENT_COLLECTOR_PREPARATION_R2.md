# E1 父轨迹采集准备 R2

2026-10-26。新增隔离实现 `src/wcomr/scout_parent_v22.py`；继承 V2.2，不修改原登记、DEV128 或原生产模块。本轮只在本机运行 CPU，未连接服务器、派发 GPU、预约预算或调整自动验收。

## 已接通的执行路径

固定 Shared25-C 的完整36步真实 sampler/owner 路径：D1–21、24、27、30、36。只在22、23、25、33、34、35保存两支当前特征；锚点来自实际 D20、21、24、27、30，C/候选/shadow 都不能写入锚点库。实际37 sigma与36 timestep的整表 SHA 绑定原CAL66网格，并检查每次回调的 timestep，按终端sigma=0计算xi/h/H。

选定状态先保存父pair之前的物理快照；父C实际完成后保存post快照和完整owner状态。独立源码精确dense executor从pre状态运行一次同状态DD，只作为oracle；恢复post状态后才运行六个读出。保存P0实际dense分支输出、P1实际dense hidden经原head/RF重放、P2重建WC-C对实际父C的逐位等价，不能把坐标转换差计作R4收益。

关键工程修复：旧父owner安装了投影适配器，独立teacher不能直接穿过其未绑定分支。改用既有 `PartialMLP.readonly()`，并通过 `DeploymentRoundtrip` 恢复控制器、真实D来源、投影缓存、读出历史和head/Linear诊断；物理 `CompleteStateRoundtrip` 恢复WC、solver、buffers、模式与RNG。保留父owner原context，scout context独立。包括失败路径在内均不安装或卸载父模块来绕过控制。

导出数据只含tensor与基础类型：两支原特征/锚点/teacher/六读出、条件字段、实际噪声坐标与pre-pair WC/solver/RNG快照。禁止pickle实时条件对象；CPU原件用 `weights_only=True` 回读。这仍不是可独立恢复的整条pipeline，未声称跨进程重放接受。诊断墙钟包含teacher、重放、候选、复制、哈希和sink；不含pair前快照，整卡必须把这些全部计费，不能拿它充当干净动作价格。

## 本地 CPU 证据

最终证据：[R7回执](../../reports/cara_scout_parent_CPU_v22_r7_20261026.json)。两条声明式小模型请求×flow OFF/ON×采集OFF/ON，共8条完整36步路径；24选定状态、144逻辑读出位置。使用源码精确WC/RF、真实UniPC与原守护pipeline函数，权重/attention/prepare/decode/writer为明确的小模型替身。

- 采集OFF/ON的全部36 guided输出、最终latent与模拟视频字节逐位相等。
- 所有选定状态的实际sigma/xi/两真D身份与冻结元数据一致；P0/P1/P2控制均过。
- 两种flow各检查teacher中断、最后状态writer失败、复制限额拒绝，共6次故障尝试；原始错误保留、适配器/钩子清理、无自动重派。writer失败是尝试6位置、完成5位置，不能算完整6。
- 错误timestep、非法终端sigma、另一合法但未登记的网格，每种flow各拒绝3项。
- 之前的六读出11项小张量检查再次通过。

R1本地依赖导入、R2teacher投影边界、R3实时条件对象序列化三份失败原件保留。R4/R5/R6为逐步扩大检查的CPU通过记录；R6运行期间扩充了检查器的来源清单，因此不把其中检查器文件哈希当作精确执行版本；源码停止修改后重新完整运行R7，只以R7的17文件绑定为当前准备证据。

**边界：这不是Cosmos实际权重/完整生产请求类、SM86/SM89主机、整卡监督或科学晋级接受。** 不读取DEV128候选输出；小模型误差不用于任何候选选择、门槛拟合或E2启动。

## 下一步与费用

1. 把当前调试sink改为按SHA引用的持久化writer：同一真实锚点只保存一次，显式清单、每项完整性和失败标记；CPU重载验收。当前逐状态快照存在重复，不能直接按旧64GiB草案派发。
2. 绑定两个旧CAL的真实冻结请求类、模型/条件/输入SHA及双端源码闭包；在不争用DEV128评分资源的条件下分别做受影响生产CPU验证。当前本地两条请求是替身，不是已采集的旧CAL资产。
3. 补齐完整物理矩阵、存储/显存与I/O成本、生命周期和终态验收。当前实现每12状态为12 dense teacher pairs、12 native-head replay pairs、132候选head pairs；父采集、OFF控制、warm、装载与收尾另计。
4. 具体数值误差界、候选费用门与完整报价仍待冻结；E1/E2没有新增执行授权。四卡默认、两卡兼容、累计226、最终部署min(257.7712338712067秒,.8freshNative)、原alpha与强基线均保持。
