# COST112 完整CPU接受与独占实际启动

实际GPU启动：2026-10-25T01:11:58.555522+08:00；本次最新技术观测：2026-10-25T01:16:54.241596+08:00。模型已加载并开始第一条warm路径，0/112完成、1运行、0失败，四个原句柄存活；科学结果尚未验收。此前104 R2原件、分析、费用和计时失败保持。

## 最大低估与修复

原模型最大低估2.617908秒来自misc场景的PG_ALL_D对照。PG全D减Native差额由第一轮0.887066秒升至第二轮3.795811秒，统一截距1.177903秒无法覆盖；跨轮差额2.908746秒中核心1.741647秒、核心外1.167098秒。写入差额漂移约1.026605秒，不支持把全部问题归给温控、`.item()`或某个固定检查。完整分解见[686](686_CARA_COST_MODEL_ATTRIBUTION_AND_INDEPENDENT112_PREPARATION_20261025.md)及[归因原件](../reports/cara_cost112_attribution_and_frozen_model_20261025.json)。

新模型使用每个验证块之前独立取得的同输入PG全D完整请求时钟，两个动作系数由旧104两轮64条缓存时钟提前冻结。旧数据仅开发资料，拟合残差仍可达4.319612秒，不声称修复已验证。新72条目标均独立验证、不重拟合；原平均误差≤1%、最大低估≤2秒、无假可行和6秒提案余量保持。

## 完整范围与CPU

新卡112=20warm+8独立时钟参照+80正式+4诊断，4CAL、10原角色加1全D时钟角色，4032pairs/8064CFG，单load；原10角色的策略和alpha逐字相等。每块先anchor，再独立PG_ALL_D/Native，再其余布局；非参照布局保留原内部顺序。23数值控制，释放GPU并结算后72组/6696帧CPU LPIPS，1.5h/2CPU。参照成本计入总费。

CPU R1完成收集与真实评分等检查，但最终存储fixture记录SHA时误写不存在的模块名，退出1；[原失败](../reports/cara_cost112_CPU_failed_terminal_r1_20261025.json)和[修复记录](../reports/cara_cost112_CPU_entry_repair_20261025.json)保留。修复只改证据路径，重新完整CPU；R2于2026-10-25 01:09:45退出0，112序列化/23控制/72评分调度、真实93帧LPIPS、6监督生命周期、6存储满/账单恢复项、14终态及8模型检查均过；CUDA隐藏、GPU提交0、权威账本写入0。[完整CPU接受](../reports/cara_cost112_CPU_accepted_r2_20261025.json)不是GPU质量或计时结果。

## 唯一GPU身份

- launch：`35150ebb-41a4-4db7-b8fb-45f6ef49297f`；run：`cara-cost-validation112-cal4-ada-r1`。
- source：`972dda61a4a62ee0086838916e0e96c097b1bc3e`；stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-cost112-full-ada-r1-20261025`。
- GPU3 UUID：`GPU-d4868f0a-29df-9077-82db-77f7bf0f9934`；guardian PID1409902/start964698191；supervisor PID1409967/start964698390；runner PID1410046/start964698608/UID1000。
- [实际启动](../reports/cara_cost112_GPU_actual_launch_r1_20261025.json)、[技术收件](../reports/cara_cost112_GPU_live_health_r1_20261025.json)、[真实独占](../reports/cara_cost112_GPU3_exclusive_active_r1_20261025.json)。唯一原runner已获得CUDA上下文，EXCLUSIVE_PROCESS、无MPS；不改变其他卡或他人任务。

forecast10.8672024715GPUh，硬上限11.9GPUh；部署257.7712338712067秒、.80freshNative、累计226不变。新11.9已独立预约；账本used147.9959437360/reserved28.4（含旧两卡16.5）/available49.6040562640。原104 R1保守5.48与R2精确7.395282不改。

独立32GiB预分配ext4输出卷、/data1跨盘48MiB日志均实测通过。39个初始监测样本最大间隔2.332秒；日志绑定当前launch/runner。卷可用31.19GiB，主盘普通用户可用1.237TiB。新增每30秒温度/SM频率/功率/限频状态采样，只记录、不调硬件；该前缀不代替完整终态独占接受。[磁盘与日志核验](../reports/cara_cost112_storage_and_thermal_admission_20261025.json)。

## 检查与后续

按实际启动安排10月25日06:38技术半程（cara-cost112）、12:20终态检查（cara-cost112-p1），[时间绑定](../reports/cara_cost112_actual_schedule_20261025.json)。预计采集约12:04，之后最多1.5h CPU评分；12:20是检查点，若仍评分则按原句柄改绑。半程可依技术节奏提前终态检查，不以部分时钟/视频调参。

用新控制器`wc_four_card_cara_cost112_gpu_r1.py` capture/accept-gpu；UNKNOWN只recover原stage，禁止重复prepare/launch。完整协议与计时模型门槛分别接受。通过后按[新P1接续合同](../plans/cara_policy_generator_20261020/COST112_TO_P1_HANDOFF_R1_20261025.json)做新的CAL_SELECT曝光核查、强基线/原alpha/Q≤8/有限可行性恢复冻结、生产CPU及完整报价。参照获取协议与费用必须重新包含，不搬旧时钟、不直接选112最优质量布局。失败保持原判据与费用，不自动追加GPU。
