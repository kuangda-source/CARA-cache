# 四卡完整96模型资源：R3服务器魔搭与原HF缺失续传

2026-10-21北京时间。沿用户已授权的资源准备和立即修复，独立R3于19:50:46.056实际启动；19:51一次准入确认原Mac控制器和服务器Docker均存活，服务器正在接收原R2断点。固定96件尚未完整接受，科学GPU未启动。

## 原失败完整收件

原R2 source `7f79ceef2e382f12814816ba6ec4955df52a1bad`、PID94749于18:23:48.385失败退出，原8次相同断点的SSLEOFError及1,132,462,080字节partial保留。此次只从外盘原件保存完整result、源码/清单/退出身份和96分母，七项离线核对通过；没有进入成功全件远端哈希分支。

- [原失败完整本地收件](../reports/wc_four_card_authorized_external_models_resume_R2_failure_full_local_collection_20261021.json)
- [独立不接受及失败留存](../reports/wc_four_card_authorized_external_models_resume_R2_failure_independent_nonacceptance_20261021.json)

86个既有文件回执只合计141,176,513字节，不代表主要权重已齐。原R1/R2 job、源码、失败、断点均保留，不重派旧任务。

## 实际R3与传输职责

| 项目 | 实际记录 |
|---|---|
| 发布并执行的源码 | `3d2dd5e19fc4ac086ee7c20f3418e84d0ec186b0`，GitHub `kuangda-source/CARA-cache` |
| Mac控制器 | PID99269，lstart `Wed Oct 21 19:50:46 2026` |
| 外盘独立job | `/Volumes/data/worldcache_resource_relay_20261021/nvidia-fixed-models-hybrid-r3` |
| 服务器独立job | `/data20t/gaokuangda/worldcache_workspace/bootstrap/wc-fourcard-fixed-models-hybrid-r3-20261021` |
| 服务器实际子任务 | 19:51:01.975，Docker PID527857/start_ticks936852533 |
| 固定完整分母 | 96文件/21,358,871,258字节 |
| 传输分工 | 四Reason1 BF16分片由服务器匿名直下魔搭；其余注册仍缺文件由Mac原HF授权来源下载中转 |
| 新资源规划 | 8小时，parent最大24小时、server最大6小时；均为资源wall规划，不是GPU费用或完成保证 |

新[配方](../manifests/wc_four_card_models_hybrid_r3_20261021.json)完整继承原96资产和原HF revision/文件名/尺寸/摘要/兼容路径。魔搭仅四个与冻结NVIDIA Reason1全SHA256/大小一致的分片，完整16,584,414,544字节；ModelScope `master`只是传输定位，不声称与原HF为同一Git revision，也不替换魔搭配置或tokenizer。来源依据见[626实际路线与字节身份](626_WC_FOUR_CARD_SERVER_MIRROR_ROUTE_COMPARISON_AND_FIXED_MODELSCOPE_WEIGHT_IDENTITY_20261021.md)。

R3先重新哈希原96已有文件，只允许原10个登记缺失；将原R2的1.13GB断点单次流式复制至server独立partial，并在开始续传前核对源/目标完整prefix SHA。新server partial与最终blob位于同一cache挂载，完整SHA通过后才原子接入原HF缓存，再独立重读并建立原兼容链接。原外盘断点不删除或覆盖。

四分片通过后，控制器重新盘点全部96，再只下载其余仍缺的原HF配置、tokenizer、Predict主权重与VAE；新模型临时文件只在`/Volumes/data`，每件服务器完整SHA后即删除对应新外盘副本。HF token仅Mac0600文件与官方HF请求，跨域重定向去除Authorization，不传服务器、镜像、报告或Git。

## 实现控制和一次实际准入

[14项本地实现控制](../reports/wc_four_card_models_hybrid_R3_local_controls_20261021.json)覆盖Range、长度、短读回滚、断点保留、全SHA、坏现存件拒绝、429 Retry-After、凭据/镜像范围、重定向、deadline、符号链接与兼容别名。它们是资源实现控制，不是科学scope生产CPU或实际GPU价格。

已发布的控制器、server worker、一次启动器及一次收件器分别为：

- [混合控制器](../scripts/relay_wc_four_card_models_hybrid_r3.py)
- [server下载与共用有界HTTP核心](../scripts/prepare_wc_four_card_modelscope_hybrid_r3.py)
- [仅一次启动器](../scripts/launch_wc_four_card_models_hybrid_r3.py)
- [单次收件和离线完整接受](../scripts/capture_wc_four_card_models_hybrid_r3.py)

19:51一次原[admission原件](../reports/wc_four_card_models_hybrid_R3_original_admission_20261021.json)的[16项独立准入核对](../reports/wc_four_card_models_hybrid_R3_independent_admission_acceptance_20261021.json)全过：Mac和Docker原PID/start/source/worker/manifest一致，server原96及四分片与本机清单逐项相同；原receiver与旧remote partial不存在，资源锁检查通过后由本job持有；四分片ModelScope元数据重新匹配。fresh数据盘可用378,645,958,656字节（352.642GiB），可用主存61,390,135,296字节（57.174GiB）。这是本次资源准入快照，后续科学任务须重新检查。

执行容器复用已缓存image `sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d`，2CPU/16GiB、隐藏所有GPU、只读root，仅本job/cache数据盘可写。没有重新安装base/runtime/wheels或修改原科研stage/共享驱动/Docker daemon。0CUDA、0模型加载、0科学GPU、0账本写入。

## 已实际安排的两次检查

[launch](../reports/wc_four_card_models_hybrid_R3_launch_20261021.json)和[实际app排程读回](../reports/wc_four_card_models_hybrid_R3_actual_once_schedules_20261021.json)绑定实际19:50:46.056启动：

| 检查 | 最早允许 | app时间 | 自动化 |
|---|---|---|---|
| 一次技术半程 | 10-21 23:50:46.056 | 10-21 23:51 | `r3` |
| 一次完整收件 | 10-22 03:50:46.056 | 10-22 03:51 | `r3-96-cpu` |

原`sha`故障接续已完成删除；旧R2的00:43/07:43不再作为有效检查。两卡`worldcache-bank24`四小时只读22:12定义读回保持，没有本轮双卡SSH。收件未知只恢复原句柄，原件保存后解析仅离线修复，不循环或重复SSH、清fence、重派。

终态必须保存完整原件后离线接受，包含全部96文件独立Git-blob/SHA256/尺寸、原HF所有兼容alias、server四分片及prefix绑定、原source/worker/manifest/依赖、登记缺失请求、旧prefix保留、新外盘副本清理、原Mac/Docker与自身锁退出。子集、partial、单个worker日志不构成完整接受。仍运行时根据保存阶段/剩余量只重估一次新查收后结束。

## 后续科学队列不变

公开Qwen3Guard/SigLIP全部14件已独立接受，不重下载或SSH重验。固定96资源接受之后，依次补LPIPS官方固定资产全SHA、独立完整推理CPU及离线模型可用性、真实CUDA兼容、BANK24与完整1624各自新机生产CPU/完整报价。取得原权威v2完整历史/settlement/所有活动整卡预留及唯一写入权交接之前，不在四卡新建或重置独立账本，不用旧116.825快照开科研GPU。

科学顺序仍为BANK24完整24路径→已登记X-R/同D配额CPU诊断→完整1624→PG-P1及后续消融/迁移/独立确认。原source、四CAL gate、上游与全部分母保持。1624的具体整卡12GPUh批准继续有效，不重复询问；新机CPU/报价/BANK24完整接受/财务前置不绕过。cap226/origin79.99637737158223和历史保持。F/B关闭，无训练、人评、付费VLM或OMR。机器总表仍54科研行，本次仅新增资源证据。
