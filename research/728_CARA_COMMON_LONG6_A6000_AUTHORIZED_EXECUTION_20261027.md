# 728｜R4_COMMON_LONG六路径两卡独占启动

2026-10-27。用户明确授权资源准备完成后在两卡服务器推进，并安排半程和定时验收。沿727完整六路径方案，硬上限3GPUh、累计226GPUh、最终部署预算、原α与六原强对照保持；IG暂停。不启动另一台服务器副本。

## 入口与CPU绑定

派发前代码核查发现采集进度回调没有主入口需要的status字段；补全`COMMON_LONG6_COLLECTING`并把回调字段消费加入真实小型采样CPU检查。双端独立R5均完整退出0，每端12路径/24状态/168重评分，监督/释放后评分/存储/财务组合保持通过。R4证据保留，实际运行绑定R5源闭包。控制器复用已验准入模式与私有传输，编译检查5个远端代码块；这不替代真实GPU上下文验收。

## 唯一执行身份

- launch：[原启动](../reports/cara_common_long6_A6000_launch_20261027.json)，`33fc1816-ae18-461a-a4de-a2a0a50cfc99`。
- run：`cara-common-long-newstates6-r1`；source `306e60d68ec2184a320bac50a0c9527f03e1f86e`。
- stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-common-long6-a6000-r1-20261027`；[stage-ref](../reports/cara_common_long6_A6000_stage_20261027.json)。
- GPU1 A6000：`GPU-cebf7119-cf03-23b9-e192-cd196332b704`。
- guardian PID262271/start638823024；supervisor PID262333/start638823212；runner PID262377/start638823402/UID1004。
- 实际派发2026-10-27 17:28:46.719545 +08；17:28:55唯一真实CUDA上下文grant。

真实Default→Exclusive_Process空闲准入与原runner active核验通过，GPU不与其他进程共享。[修正历史观察时钟后的技术回执](../reports/cara_common_long6_A6000_admission_historical_clock_fixed_20261027.json)：61样本、0违规、模型加载，0完成/0失败；这是前缀，不是完整终态。

初版技术收件误用当前时间校验历史监测行，将旧行误报33次stale；保存原回执，明确该违规计数无效。仅修本地收件控制器，以每行原observed_unix校验历史前缀，运行stage与实际监督未修改。真实监督始终用新鲜观察，未见独占违规。

## 范围、磁盘与费用

2warm OFF+2正式OFF+2正式ON=6，12固定状态×7读出84位置，228pairs/456CFG、186额外head pairs、一次load。两条旧CAL，不称新输入；ON是同状态shadow，不称新候选自由运行视频。双时间口径保留，ON开销标诊断，不改原部署验收。

独立32GiB ext4预留输出卷；跨盘`/home/gaokuangda/cara_control/common-long6-r1/control.journal`48MiB固定日志。准入观察输出约31.2GiB可用，宿主盘约0.95TiB可用，持续StorageGuard及连续独占监测开启。

预测2.608114273192671GPUh，硬3。中央唯一3h外部包已经预约并确认实际GPU提交，和两卡本地子账本是同一笔费用。[中央确认](../reports/cara_common_long6_A6000_central_admission_confirmed_20261027.json)：used172.2657747141984、reserved19.5（含旧16.5未知责任）、available34.234225285801614，cap226。两卡旧镜像不是额外余额；终态以原精确账单回填唯一中央包。

## 检查与验收

北京时间2026-10-27：半程**18:48**（automation `cara`），终态**21:10**（`cara-2`）。预计采集20:05，GPU释放结算后2CPU/8GiB重评分84位置，最多1h，约21:05可收件；预测不等于完成保证。硬GPU3h对应约20:29，之后CPU上限1h。依技术进展调整既有检查，不重复创建。

控制器`python scripts/wc_two_card_common_long6_gpu_r1.py`：

- 运行期间：`capture --launch-ref reports/cara_common_long6_A6000_launch_20261027.json --mode halfway --output 新唯一路径`，只返回技术字段。
- UNKNOWN：`recover --stage-ref reports/cara_common_long6_A6000_stage_20261027.json --output 新唯一路径`。已有intent，禁止再次prepare/launch。
- 完整退出：`capture --launch-ref 原件 --mode terminal --output 新终态`，随后`settle-central --capture 新终态 --output 中央结算`，再`accept --capture 新终态 --central-settlement 中央结算 --output 独立接受`。

核对原身份/SHA/6路径/84评分/原alpha/OFF-ON全36+final+video/双时钟、连续独占与末次到结算≤45s、精确单调费用、中央幂等结算、原容器和锁退出、磁盘日志及安全恢复Default。GPU释放后的CPU评分不重跑GPU。失败保留原件和费用，不自动重派；完整接受后才按冻结机制门分析，不自动晋级j1/E2/IG。

启动后续[技术观察](../reports/cara_common_long6_A6000_startup_status_20261027.json)：模型加载已结束，第一条父路径运行（0完成/1运行/0失败），130独占样本0违规。未读取科学分数。
