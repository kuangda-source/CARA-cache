# 独立价格补测：真实入口通过，完整CPU数值验证运行中

原1624已完整接受，标签与Native参照继续复用；本轮没有重跑原GPU资产卡，也没有提交新GPU。动作价格仍须独占补测后才可用于PG-P1。

## 新实现与冻结身份

完整价格专用采集器、runner、原件后处理、容器supervisor及宿主机模式控制已新增，原运行源码不改。`ReadoutKernel`、C/A实现和时间边界沿已接受原件；新采集器逐格核对原source/input/older-anchor SHA，每格执行1轮warm+3轮正式，每轮3动作，检查读出一致，不再导出误差标签或区间张量。新bundle只替换价格，逐项保持原标签。

- 源码：`cecba6647fcc626887761961fc7215c6fe1afa8b`，已推送GitHub。
- stage：`/data20t/gaokuangda/worldcache_workspace/.sync/wc-policy-price-refresh-fourcard-full1624-r1-20261023`。
- CPU实际启动：2026-10-23 **09:14:02.151608**；PID915069/start950310551；容器后缀`-cpu`。
- 注册SHA：`8b35974e725fa1fbb72fb5474f10c763edb998e4b59bd21f7775e44ed3c6a00b`。
- [启动原件](../reports/wc_policy_price_refresh_full1624_CPU_launch_r1_20261023.json)；[真实入口观测](../reports/wc_policy_price_refresh_full1624_CPU_production_entry_r1_20261023.json)。GPU隐藏、只读根目录、2CPU/16GiB；未动实际GPU账本。

实际Cosmos SetupArguments与4个请求、8个无guardrail拒绝入口、原C/RF源码逆向证明、真实NLTK分词、同生产视频writer的93帧写入/逐帧读取、ffprobe、继承FD及锁释放均通过。日志里的模型缓存“Downloading”来自离线缓存解析；容器network none、CUDA隐藏，torch.load和CUDA初始化被CPU入口禁用，没有模型权重加载或网络下载。

完整数值验证单独运行：两种flow设置各14条原始Toy参照+10条新价格路径，共48完整CPU路径；原4060格/26040读出用于参照，新4060格/48720读出验证全部三轮、全36步与最终latent/RGB一致、无区间张量导出、source不符提前拒绝、正常拒绝分母、owner释放和合并标签不变。此处Toy验证不冒充真实视频实验。最终三命令bundle和独立接受尚待原进程完整退出。

## 独占生命周期检查

[独立CPU故障回执](../reports/wc_policy_price_refresh_lifecycle_CPU_capture_r1_20261023.json)绑定上述冻结supervisor与host guardian SHA，09:19:44启动，09:20:26退出0，六项全部通过：正常退出、runner失败、外部上下文、退出时遥测丢失、空闲恢复模式、外部进程出现则延迟恢复。前四项运行真实CPU子进程，验证原继承FD、握手、只终止本任务、异常后实际CPU墙钟在隔离fixture账本结算、释放锁；后两项调用真实guardian编排但替换管理命令，确认不把凭据写入文件。

该fixture用1CPU/4GiB，未调用真实sudo或nvidia-smi，未接触权威账本，不证明硬件已经启用EXCLUSIVE_PROCESS。宿主机只有指定UUID空闲时才可改模式；容器内runner保持实际CUDA上下文，唯一PID/start/UID核对通过并收到supervisor许可后才能加载权重。supervisor持续监测；停止时只处理自有runner。退出后若他人已进入则记录模式恢复延期，绝不驱逐。项目flock只承担自身协调，不代替硬件隔离。

## 本轮边界与下一步

原卡6.900544 GPUh及累计125.646552、未知旧责任16.5 GPUh保持。新完整价格卡仍为4CAL、10路径、2030总格、24360读出、单load；预测9.500278、上限11.5 GPUh，不复用旧12 GPUh授权。最新资源查询四卡仍占用，因此没有实际启用独占或预留新GPU。

先收新CPU的完整数值与三命令原件，用`scripts/audit_wc_policy_price_refresh_cpu_r1.py`同时绑定上述生命周期回执。随后补齐一次性GPU控制器、UNKNOWN原句柄恢复和独立GPU终态接受入口；当前控制器只开放prepare/deploy-cpu/capture，不能因单个生产proof布尔值通过就提前启动。新增控制器可在本地继续实现，不改正在验证的stage；若生产源码需要实质修复，保留原失败，使用新的不可变stage与对应CPU验证。

当前准备检查复用`cara-bank24-2`，半程最早09:24:02，终态最早09:44:02，按实际完成/失败收件，不回填时间。独占资源可用且全套准入通过后才单次启动价格GPU，再按实际启动安排半程与全程。价格接受后按PG-P1→P2继续；历史窗口shadow诊断与少步Native等时间对照保持648方案。

## 实际09:24技术半程与检查改绑

[09:24:29.839738原CPU回执](../reports/wc_policy_price_refresh_full1624_CPU_halfway_r1_20261023_0924.json)核对原容器仍运行、GPU设备列表为空、生产入口证明存在、完整数值与三命令bundle未完成。技术进度：flow=False的5条旧COLLECT各406格完成；新PRICE warm406格完成、formal_0_PRICE完成99/406格，已写技术进度的错误均0。只记录进度，不把部分fixture输出当接受结果。

[09:24:31资源与CPU技术进度](../reports/wc_policy_price_refresh_resources_and_CPU_progress_20261023_0924.json)：四卡仍全部占用、均Default，GPU3的PID848535保持；磁盘可用178538070016字节，内存可用74041769984字节，权威账本未变化。没有新GPU提交、模式变化或费用。

本次半程已完成，原`cara-bank24-2`一次检查已改绑**09:45**完整CPU验收与后续准入；未新增重复自动化。完整CPU仍需原数值命令、单元检查和原容器退出0；若届时尚未完成，只记录原句柄实际进度并调整同一检查。
