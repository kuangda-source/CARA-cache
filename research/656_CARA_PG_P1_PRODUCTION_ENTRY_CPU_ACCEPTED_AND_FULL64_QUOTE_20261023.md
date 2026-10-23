# CARA PG-P1：生产采样入口已接受，完整64路报价已准备

2026-10-23。本轮按用户指示在价格GPU运行期间推进P1入口、CPU验收和完整报价。**合法策略的生产采样入口已通过独立CPU接受；完整卡预计8.844444 GPUh、计费上限10.5 GPUh。没有提交PG-P1 GPU任务，也没有读取价格补测的部分科学结果。**

## 本轮交付

- `src/wcomr/policy_generator_r1/production_sampling.py`：任意合法36步interval策略的实际WC/RF采样入口。D/C/A掩码和逐区间共享alpha=.5/1均由已编译策略决定；C使用部署轨迹的真实两D窗口，A仅使用过去真实D；D36及模70计数检查保留。非有限读出恢复当前pair的缓存/RNG，再做真实D，实际回退与费用留痕。
- `production_batch.py`：完整自适应卡的执行引擎。Native warm2+FIT4 → 固定B → 首4候选 → 唯一一次至多4个邻域 → 冻结入围与simple控制 → 新SELECT Native2及至多8个端点。技术失败、拒绝和未使用的上限位置均保留；去重不补查询。
- `production_contract.py`与[完整报价](../manifests/cara_PG_P1_full64_whole_quote_r1_20261023.json)：最大64路径/2304pairs/4608CFG/单load，40候选正式+6Native正式+18warm；复用已采标签，额外标签路径和shadow为0。
- [准备包](../reports/cara_PG_P1_entry_CPU_and_full64_prepared_20261023.json)：独立重新验算CPU接受和整卡报价，并绑定已接受的生成器源码SHA。

## 真实CPU证据

四卡独立CPU目录`cara-pg-p1-CPU-r2-20261023`，冻结源码`56f31419ff58de80c036d22d4ae9f9e5992d7565`，注册SHA`f087e2116d5546b8b3fce46fc3a83e6ad96680ac67d32dc4ad8f7717ba37dac2`。容器隐藏所有GPU、只读根目录、网络关闭、限1 CPU/4 GiB；资源准入时MemAvailable 28.91 GB、磁盘112.42 GB。本轮未申请GPU、不写GPU账本、不修改共享运行时。

容器实际15:27:33启动，15:29:37退出0；完整回执实际15:30:22收取，不能把文档时间当作新GPU观测。

- [原终态](../reports/cara_PG_P1_production_CPU_terminal_r2_20261023.json)
- [独立接受](../reports/cara_PG_P1_production_CPU_accepted_r2_20261023.json)
- [62项相关本地CPU检查](../reports/cara_PG_P1_related_CPU_tests_20261023.json)

实际Cosmos `SetupArguments`、4FIT+2SELECT请求、6个guard拒绝控制、NLTK真实分词、93帧生产writer/解码/ffprobe、继承FD/父进程/隔离锁验证通过。两个flow状态各9条完整数值路径：Native与全D逐步/最终latent/CPU图像控制相等；C、A_HALF、A_ONE与混合窗口走完整36次更新；重复请求相等；注入非有限读出后回退D与独立注册D策略相等；文本拒绝与末端writer异常清理通过。额外失败控制保留。

数值路径使用声明的CPU小权重/注意力/输入/解码替身，执行固定的真实WC/RF/UniPC主体；不是Cosmos GPU视频或质量/速度结果。真实writer独立做93帧CPU编解码检查。**这次接受的是生产采样入口；整卡GPU监督器、评分回调、Native时钟接受与终态接受的最终组合尚未作PG-P1全卡接受。**

## 失败记录与修复

首个资源前检因为自设32 GiB阈值未满足而停止，远端stage尚不存在，无进程/GPU启动；固定新CPU上限4 GiB并保留至少20 GiB可用主机余量后重新进行准入。原UNKNOWN包装回执保留，已通过远端实际stage缺失与资源读取定位为CPU准入拒绝，不当作SSH故障。

R1容器实际退出1：RF模块延迟导入时离开了CPU导入专用FlashAttention探测窗口。修复为在同一明确导入窗口加载WC/RF，之后恢复探测函数；没有装包、改CUDA、改共享环境。R1回执保留于`cara_PG_P1_production_CPU_capture_r1_followup_20261023.json`，R2用新目录完整重验。

## 完整报价及边界

| 项目 | 规划秒数 |
|---|---:|
| 一次模型加载 | 174.621861 |
| 全部64路，每路按已接受BANK24中最慢完整请求306.199015秒 | 19596.736938 |
| CPU图搜索与唯一修订 | 1200 |
| 40对全93帧CPU LPIPS | 2400 |
| 原件搬运、哈希、参照核验 | 1200 |
| 独占准入、监测、安全退出 | 900 |

总和×1.25余量得到**8.844444 GPUh**；再乘1.15并向上按0.5 GPUh取整，上限**10.5 GPUh**，严格小于12。所有候选按最慢完整路径收费，不提前兑现0.8加速或物理去重。历史耗时只用于保守规划，不能作为干净动作价格或新B。没有挪用当前价格卡11.5 GPUh，也未预留新卡费用；正式准入必须再读权威余额。

## 价格完成后的衔接

1. 继续按655收取并独立接受当前唯一价格launch，完成费用与锁释放；不重跑原1624。
2. 绑定旧标签SHA与新独占价格SHA，复用本轮已验生产入口和完整报价。先把整个P1的GPU监督/评分/Native时钟/终态接受接到这套执行引擎并做对应生命周期CPU检查；不能把`production_entry_CPU_accepted`提升成整卡准入。
3. 单次新卡取得2warm+4FIT干净Native完整请求时钟，再固定B=.80和生成提案；不得使用旧受竞争Native时间。余下候选/SELECT属于同一完整卡，禁止拆卡。
4. 首次SELECT只补查新增执行元数据；固定两个SELECT身份不按结果变动。P1冻结后才做既定小历史诊断、P2少步Native等时间对照，另作完整报价。

当前价格卡的stage/source/GPU3/UUID/原句柄、17:59半程与22:59终态安排均保持。没有因为本轮文档或CPU工作刷新GPU科学状态。
