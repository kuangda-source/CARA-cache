# WC-S1：A6000真实内核结果与下一科学瓶颈

日期：2026-10-01。状态：真实CUDA内核/派发/数值技术筛查通过；固定稀疏mask误差大，不能作为质量方案。没有模型生成、实际QKV hook、WC成本profile或新方法质量—时间结论。

固定source `cb80dd56be4286b18d0a5cfb782371ab2dd1fdb9`，原Cosmos Torch2.7.1+cu128/ABI=true，A6000 sm86。fresh UUID/VRAM24MiB/无compute PID准入、共用global GPU锁后只启动一次kernel-gpu-r1。180秒prepaid reservation终态退回未用部分，实际含import/diagnostic/释放墙钟11.726698秒；没有扩充原4GPUh额度。[部署](../reports/wc_s1_kernel_deployment_20261001.json)、[launch](../reports/wc_s1_kernel_r1_launch_20261001.json)、[终态raw repeats](../reports/wc_s1_kernel_r1_terminal_20261001.json)、[独立审计](../reports/wc_s1_kernel_r1_fresh_audit_20261001.json)、[结果重算](../reports/wc_s1_kernel_r1_summary_20261001.json)。

## 31,104 tokens：含接口开销的结果

输入B1/N31104/H16/D128，BF16；Q/K随机高斯并逐头RMS归一化、V随机高斯，seed0。N来自已记录hidden/config/checkpoint的推导，未直接hook实际模型。两种静态cyclic-band masks均事前固定且保留所有结果，不称数据驱动重要性选择。

| 核心算子 | 同步wall中位数ms（5repeat） | dense/该臂 | 相对dense RMSE | 实际块保留率 |
|---|---:|---:|---:|---:|
| 当前dense/实际Flash SDPA派发 | 70.3511 | 1.000 | 0 | 全部 |
| no-PV全块保留 | 71.6363 | 0.982 | 0.013233（1.323%） | 100% |
| no-PV约50%保留 | 39.7678 | 1.769 | 1.004365（100.436%） | 50% |
| no-PV约25%保留 | 23.6529 | 2.974 | 1.736761（173.676%） | 25.103% |

与同量化full-mask相比，两个稀疏率分别1.801×/3.029×。全块保留没有比当前dense更快，不能把换低精度后端当作已证收益。稀疏rate确实对应真实块计算跳过的速度变化；固定mask在这种输入上有很大误差，不能据速度接入生成流程或宣称保质加速。

所有8个case（N256/N31104各4臂）finite、BF16输出/正确展平形状、5个wall与event repeats完整；dense CPU dispatch profile明确有`aten::_scaled_dot_product_flash_attention`。CUDA-event中位数在大形状分别70.3236/71.5968/39.7425/23.6274ms，仍不替代同步wall。每臂计时含finite/row validation、packing、INT8 QK、FP16 V、LUT/flatten/同步；一次输入/固定mask创建不在每次重复时间中，未来动态路由/模式重建必须另加成本。

全块保留relative RMSE在N256为0.012690、N31104为0.013233，满足本次预登记<=0.05技术筛查。这个容差仅是合成QKV数值门，不是视频质量或行为门。诊断peak allocated memory大形状dense约1347.4MiB、候选约1780.4MiB，包含误差/float参考等诊断buffer，不当作部署增量显存。

## 小序列揭示接口成本

N256 dense中位数0.17696ms，full/50%/25%候选1.3434/1.3340/1.3478ms；三候选均明显更慢，不能泛化大形状内核收益到小token或cross-attention。两个稀疏mask相对dense RMSE约0.993/1.691，同样保留。验证/sync/packing开销在小序列占主导，后续优化若移除检查或缓存路由，必须同等处理两种候选控制并重新测净时间。

## 终态与下一步

独立CPU审计重新核对8-file package/4部署payload SHA、完整8case覆盖/所有5repeat中位数/派发与dtype/形状；监督、timeout与实际kernel三PIDs均退出、global锁释放、GPU无本任务compute PID。预约180秒退款168.273302秒，原账本精确结算为3.6545041399802236/4GPUh、余1243.785096秒（约20.73分钟），23 GPU jobs；无in-flight reservation、没有默认人评/训练/付费评分。

决策：保留Sparge no-PV作为当前硬件上可执行候选，**不解锁自由三档控制或直接四臂视频比较**。下一优先S0官方WC单场景剩余成本与真实QKV采集，确认deep self-attention的实际shape/stride/dtype及q/k重要性结构，再比较已有统计选择策略/匹配full-mask数值误差和路由时间。完整profile不是本轮70ms微基准，不能用Native注意力占比替代WC后的可优化占比。

固定band误差大只否定其在本输入的保质用途，不否定数据驱动稀疏注意力，也不直接切换研究方向。模型QKV上full-mask误差/任务保持仍需实测；即使kernel快也需WC后成本占比及同预算质量证据。下一GPU工作仍事前固定scope/cap并fresh准入；余额内有界S0准备可继续，超出现有4h才提重要预算决定。旧launch/kernel不重复运行。
