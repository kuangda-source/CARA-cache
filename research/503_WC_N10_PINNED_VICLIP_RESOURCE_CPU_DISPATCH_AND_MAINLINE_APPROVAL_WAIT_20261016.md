# ViCLIP独立资源准备已派发，N07整卡审批保持待回复

2026-10-16。**四个现有指标权重实际哈希已核对后，开始补齐原六维评价缺少的固定ViCLIP资源。** 这是不占GPU的资源准备，不是新的生成实验或质量评分卡；N07完整180与预算增量仍等待此前一次具体询问的直接回复。

## 原资源句柄

- source `3c7767fbc48d47a5e3bba3cf46f93a5f519f56d4`，stage `.sync/wc-N10-viclip-resource-r1-20261016`。
- 原PID1113019 / start_ticks542082643，2026-10-16 12:45:22.916501 Asia/Shanghai单次派发并记录原初始R身份。
- 注册SHA `851618aec56a0dfdb87b9bf235425bc53a20cfe04d316c689fc09411547d04dc`；worker SHA `d8602f2174d46035e838ba38101671b79c20ab9d04e7cc70fd3be7fb0de13ac4`。
- 原固定HF修订83290ee59b4e2c0a4d198857edbc79dd186b8d44，文件`ViClip-InternVid-10M-FLT.pth`，1710545812字节；完整SHA `7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56`。

下载位置独立于全局缓存、原N07/N05/N06 stage和运行环境；只执行纯标准库stream下载/大小与全SHA核对，CUDA可见集为空，没有模型import/load、GPU派发或账本写。完整匹配才提交正式文件；失败保留part和结果，不覆盖已存在的stage或重派原任务。下载进入项目分区，当前预核空间充足；无需移动原视频或权重。

按1.71GB公开资源的网络不确定性，先安排约30分钟后一次查收。最早13:15:22.916501（unix1792127722.9165008），**13:17一次收**，期间不持续监听。只读原PID/注册/worker/原result/target或part；终态还需collector独立重算实际target大小与SHA，才接受资源字节就绪。若仍在途，依据已收字节与经过时间估剩余，另约一次并立即结束；资源失败不视为研究方向失败。

资源worker最小CPU控制见502，四项小字节/模拟网络对照通过，包括坏SHA/短文件/超长文件/重派拒绝；并非真实权重已经下载。原公开模型身份与当前代码从已存官方元数据交叉核对，没有擅自替换模型或新增指标。

## 已具备和仍缺的证据

502回执记录DINO、AMT-S、RAFT-things、MUSIQ-SPAQ四文件全哈希与12份DINO缓存Python源，MUSIQ权重/架构与旧测量协议一致。对于另三文件，目前是实际现存字节身份，模型严格载入/推理和官方资源对照尚待；包依赖元数据不替代运行CPU。

493的固定216代码包和真实BPE词表、494的160正式/960指标位置输入桥保持；指定ViCLIP仅为完整原评分资源补全。实际模型CPU、最终全视频评分与GPU费用仍待；当前没有新语义/运动/物理质量分数。新源/数据不进入原生成器或选择器，不接触最终测试视频或泄漏教师监督。

## 审批与主线保持

N07 source140d0a6真实生产CPU在12:35已全部接受501，1725SHA/六命令/160typed/完整180保持。预计整卡15.055555556GPUh，超过用户严格<12自主范围；最新12:36原池实结93.581824657/cap104.971363333/预留0余11.389538676。此前已一次询问完整180及同一累计cap113，**尚未收到直接人类回复；没有重复提问、自行修改cap或启动GPU**。一般goal继续消息不代替这项预算/整卡批准。

主线N07→N08完整40重复clean→N09部署/N10自动质量；资源准备与当前审批无数据依赖，不阻塞任何后来已明确批准的N07执行。N08报价3.6275保持；N09/N10实际GPU费用另待核定。原origin/used历史不重置，不缩180或40绕过门槛。P/T1后排，F/B关闭，无训练、OMR、人评。

13:17资源查收完成后暂停对应heartbeat，后续模型CPU如有长任务另按ETA一次查收，不让资源派发冒充评分完成。

## 原件

- [原launch](../reports/wc_paper_N10_ViCLIP_resource_R1_launch_20261016.json) · SHA256 `5f4aac10746cf7fabd840b2dc27052185e99ecef06bd72de10f2203e6e677961`。
- [四权重与限定检索](../reports/wc_paper_N10_existing_resource_hashes_scoped_20261016.json)。
- [502资源准备](502_WC_N10_EXISTING_FOUR_WEIGHT_HASHES_AND_PINNED_VICLIP_RESOURCE_PREPARATION_20261016.md)。
- [501完整CPU与审批对象](501_WC_N07_FULL180_REAL_PRODUCTION_CPU_ACCEPTED_COMPLETE_CARD_AND_BUDGET_DECISION_20261016.md)。
