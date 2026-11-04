# sensitivity8流水线续卡：正式报价，未预留、未启动

Run `cara-native-sensitivity8-pipeline-r2-20261104`。F17原run/launch保持，本轮没有碰其容器、16GiB卷、stage、manifest或服务器执行源码，也未评分/结算F17。全部代码修改只在Mac，CPU测量代码通过stdin临时执行，没有同步或prepare服务器源码。

## 指定64GiB镜像：删除尚未完成

中央job `cara-budget-calibration-14gpuh-r1-20261030` 为SETTLED，实耗0.002315298GPUh。已核对精确物理路径：
`/media/minchen/4def5c03-8324-4cba-ac0b-9fda7c79dc7b/gkd/cara_cal66_sm86_workspace/.sync/storage-reservations/budget-calibration-r1/output.ext4`。
文件inode6495988236、owner1004、size68,719,476,736、allocated68,719,480,832 bytes；metadata/failure receipts均保留。
主机侧fuser确认空闲后已正常umount；`losetup -d`置autoclear，但F17私有mount namespace仍继承 `/dev/loop42` 的只读挂载（PID537758的mountinfo已只读确认）。主机findmnt已无该挂载，loop仍在，故**未删除镜像，实际释放0 bytes**。没有进入或修改F17 namespace，未安排自动清理；需其自然释放引用后才可继续原已授权删除。
最后一次检查13:29北京时间：`df -h` 为 `/dev/sdb1 14T 13T 293G 98%`，精确可用313,642,373,120 bytes（292.102222GiB）。即使暂未释放64GiB，现余量也足够将来另分配本续卡的64GiB输出；当前没有provision此卷。

## 流水线、保留与实现

[补充预注册](PREREGISTRATION_ADDENDUM.md)及[完整manifest/报价](manifest.json)是本卡范围。复用原SENS_003–007五条Native，重做human_034并补misc/physics两个未到达输入；按输入立即完成14后缀，删除新record的14份完整状态后再进入下一record。
旧256GiB卷全程只读，保留70份状态及小产物，完整释放/评分/原理重建后再处理其释放；本卡不会删除旧状态。70份尺寸/ZIP中央目录可读，原先没有文件SHA旁证；只有一个实际载入样本校验了嵌入digest，其他状态消费时校验一次，不称全量内容已验证。
新增卷按64GiB设计、4GiB低水位不变。新增payload保守峰值53,947,000,000 bytes（50.242059GiB），另计ext4和4GiB余量；一套record约43.80GiB，新record清理后各保留约0.378GiB（按407MB上界）。旧256GiB加新增64GiB的镜像分配总量320GiB，不把全盘占用说成44GiB。
`runner.py`增加只读复用及每组成功后的新状态删除；`sampling.py`在CPU校验一次再恢复设备/alias；`cpu_owned_state_snapshot.py`取消GPU树的重复hash，只对CPU副本做finite+digest。GPU数值公式、RNG、UniPC、C定义、原理函数和所有科学阈值不变。
`score.py`复用Native引用且不重跑不存在的clean质量位置；`analyze.py`只合并F17释放/结算后的原12LPIPS与48质量结果，不重评分。F17未完整时不能宣称两卡合并完成。报价模式的prepare/reserve/dispatch显式拒绝，尚无本卡launch_id。

本地两flow各122完整请求、28个独立完整single-C/续跑latent与RGB等价控制通过；另验证单次CPU hash、alias/重复tensor对象、损坏状态拒绝、三组新状态删除与旧70份保留、峰值仅一组新状态。CPU验证不等于GPU/完整Linux入口准入；本轮没有服务器stage或GPU提交。

## CPU实测与正式报价

Torch2.7.1+cu128，CPU容器无GPU设备，1核/8GiB/no-swap、nice19、ionice idle，CUDA_initialized=false；成功测量约106.7秒，峰值RSS7,610,208,256 bytes。先两次SDK元数据导入失败，未产生状态保存文件；最终用原源码DataType枚举声明加载元数据，不加载GPU模型。
SENS_003/t8：原状态3,330,480,363 bytes；torch.load 1.966s（有缓存），恢复等价28.871s，其中CPU hash24.686s、CPU复制/重建4.184s。原嵌入digest匹配。
同大小CPU树保存3,330,479,590 bytes（CPU RNG/device元数据少773 bytes），CPU复制+单次hash26.467s，其中hash24.263s；torch.save+fsync43.947s，保存总计70.414s。没有按“去掉重复hash”臆测加速倍数。
loop内direct-read的1.226s仍受外层镜像页缓存影响，不用作冷盘速度。另用filefrag定位原状态的实际extent，对底层image的同一已写入1GiB区域做只读O_DIRECT，115.016MB/s；外推3.33GB冷读28.957s。每次恢复报价计入该冷读＋cached torch.load＋CPU恢复≈59.794s；GPU H2D/D2H仅以CPU复制代价代理。
保存实测位于新计划镜像的同盘XFS父目录，并非尚未创建的新ext4卷；保留state路径−25%/+35%、GPU请求−5%/+15%的工程范围，中心另含10%波动、600s模型准备和600s退出。范围不是置信区间或硬保证。

| 方案 | 新请求 / paired calls | GPUh中心 | GPUh工程范围 | 建议硬限 | 单GPU墙钟中心 |
|---|---:|---:|---:|---:|---|
| **保留5控制，登记主方案** | 122 / 2112 | **10.371019** | **8.459252–11.370268** | **11.5GPUh** | 约10小时22分 |
| 去掉5控制，仅报价对照 | 117 / 1972 | 9.937369 | 8.091380–10.910263 | 11.0GPUh | 约9小时56分 |

112后缀、42次新状态保存及114次恢复（有控制）均计费；不再执行F17的16条clean，不重新收取原五条Native费用。无控制版本不是当前预注册主方案。
中央ledger最后只读快照：cap250 / used218.93254819368744 / reserved18.45 / **available12.617451806312562GPUh**，F17的1.95仍保留。
若未来批准且实际预留11.5，按该快照可用余量1.117451806GPUh；无控制11.0版本余1.617451806。不预支F17可能返还的余量。两版均>4GPUh，必须批准新数字；当前0新增预留、0新GPU。

scratch仅本轮新建：`$R/.sync/cara-pipeline-benchmark-20261104/state_same_size.pt`及其空目录，已删除；CPU容器已自动移除。direct-read写向`/dev/null`，没有其他数据文件；原五条Native、008失败证据、budget-calibration-r2、CAL35和F17均保持。测量原始输出在Mac `/tmp/cara_pipeline_CPU_IO_r3.json`、`/tmp/cara_pipeline_backing_read.json`，数值已纳入manifest，没有额外审计文档。


## 2026-11-04 实际验收：启动条件未满足

用户批准「保留5控制，约10.37GPUh，硬限11.5GPUh，F17验收通过后上卡」，并要求正式中心≤11.0、可用额度≥11.5。Step0中央ledger及服务器回执确认本run无job、无stage、无dispatch或launch；本轮未prepare/provision/reserve/launch。
F17原18/18 GPU成功，guardian实耗1.201165875084957GPUh已唯一结算seq94；ledger cap250 / used220.1337140687724 / reserved16.5 / available13.366285931227594。
同批速度1.919510545×、F17平均T_DD131.701258789s；新/旧F17 LPIPS均值0.236186453/0.238367899，固定δ0.027、70排列单侧p=0.300>0.05。非劣性未确立，独立确认FAIL，因此本续卡不启动；没有launch_id、启动/预计完成时间。正式报价10.371018501GPUh、硬11.5保持，仅满足费用门不构成启动条件。
指定budget-calibration-r1的64GiB镜像及provision.json已删除，删除前loop42/主机挂载/活动容器引用均为空；文件分配合计68,719,484,928 bytes，延迟回收后df可用357G（382,360,334,336 bytes）。r2、CAL35、旧256GiB敏感度卷及F17卷均未改动。
F17评分/分析入口和唯一结算回执见 `reports/cara_f17_confirm4_r1_20261104/` 及 `../f17_confirm4/RUN_HANDOFF.md`。没有新GPU、预留、监控或自动后继。
本续卡仍是quote-only源码：未来若另获启动许可，须先完成独立run的binding/event/addendum接线，并用release现有launch_id字段对齐确认复用入口，再做Linux入口及fresh准入；不把本地CPU dry-run称为生产可启动证明。
