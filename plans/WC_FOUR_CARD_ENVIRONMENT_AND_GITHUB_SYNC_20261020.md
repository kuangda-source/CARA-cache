# 四卡备选服务器：独立环境、资产和GitHub同步

用户直接要求先确认空间，再配置四卡环境并经GitHub同步代码和最新进度。原BANK24和完整1624采集卡的冻结scope/source、已批12GPUh及原上游顺序保持；本准备不派任何GPU，不改共享驱动或Docker daemon。

工作区/data20t/gaokuangda/worldcache_workspace已创建并实际write/fsync/readback/unlink通过。当前约445.9GiB可用；规划整个工作区最多300GiB（包括原HF树约48.1GiB、环境/源码/临时空间和完整卡至少93.5GiB工作余量），另保留128GiB文件系统余量；当前空间满足。模型、独立env、HF/pip/uv/Torch缓存与tmp全部落数据盘，原系统环境不变。

四卡系统glibc2.31、驱动550.67，低于固定Cosmos SETUP文档的glibc2.35与驱动570.124.06要求。现存缓存镜像的用户态也较旧。准备使用轻量官方python:3.10.19-slim-bookworm容器，拉取后绑定实际image digest；仅CPU、只读root、隐藏GPU、2CPU/16GB限制，全部环境可写目录挂到数据盘。小镜像仍使用既有Docker存储，拉取前系统盘必须至少4GiB空余；不向该盘安装大环境或模型。不升级共享驱动；GPU驱动兼容性仍未验证。

四卡无私有GitHub读凭据。先将源/计划/状态推送原私有GitHub，核对远端main==部署commit，再用Git bundle安全转运同一个已发布commit，四卡clone后origin仍设GitHub；不复制GitHub账号密钥或token。原cache/runtime的11个执行关键源码SHA与已验CAL12 registration完全一致；单独打包该完整源码树并绑定整包SHA。它是代码同步，不是新机生产CPU通过。

环境入口scripts/bootstrap_wc_four_card_environment_r1.py，recipe在manifests/wc_four_card_environment_preparation_recipe_r1_20261020.json。安装固定Python3.10、Torch2.7.1/cu128/torchvision0.22.1、受约束Cosmos base和登记CUDA扩展，记录resolved freeze；实际CPU导入和所有命令结果分别保留。容器解决用户态依赖隔离，不宣称解决GPU驱动兼容问题。下载/安装失败保留原日志，下一独立准备版本修复；不将部分安装当production_CPU_accepted或GPU_dispatch_ready。

四卡和本机均没有HF凭据，四卡对官方HF元数据当前连接失败，不能称403或已下载。优先等双卡入口恢复后按已固定snapshot/SHA复制原模型缓存（排除token/stored_tokens等认证文件）；否则需已获授权HF访问和固定版本下载。原N07/N08/N10/Window24/CAL12不重跑，BANK24原接续不变。新机需自己的完整生产CPU、完整报价、共享权威v2与逐UUID准入；不能把双卡旧CPU/旧财务快照移作新机通过。

此次长CPU准备只单次派发，source/manifest/host PID及start_ticks与容器image分别登记；实际launch后+1800秒一次技术半程、+5400秒一次终态查收。收件只检查原句柄/环境/错误和磁盘，不看原BANK24科学partial；未完按阶段重估一次后结束。完整环境、模型资产、新scope生产CPU和GPU准入分别接受，0GPU账本写。

## 实际句柄与完整接续

R1依赖失败保留，R2基础环境22:44:35单次启动，launch=reports/wc_four_card_Ada_container_Torch_CPU_prerequisites_R2_launch_20261020.json，PID256731/start929253857。23:15技术半程、10月21日00:15完整验收已安排worldcache/worldcache-2；原BANK24仍00:20。

R2收件：python3 .sync/four-card-bootstrap-transfer-20261020/capture_prerequisites.py --kind prerequisites --mode terminal --launch-ref reports/wc_four_card_Ada_container_Torch_CPU_prerequisites_R2_launch_20261020.json --output reports/wc_four_card_container_Torch_CPU_R2_terminal_20261021.json。仅从保存原件离线运行scripts/analyze_wc_four_card_environment_r1.py --kind prerequisites --launch-ref 同原launch --capture 同原件 --output reports/wc_four_card_container_Torch_CPU_R2_independent_acceptance_20261021.json。此接受仅CPU环境基础。

通过后先运行.sync/four-card-bootstrap-transfer-20261020/sync_GitHub_mirror_for_deployment.py，复用已启动的GitHub mirror，不重克隆；fetch最新已发布main、生成完整bundle并核对主worker字节身份。再运行同目录transfer_and_launch.py，先查原job/launch/project，无旧派发才首次转运和启动；manifest强制绑定R2实际result字节SHA及独立接受。完整worker launch=reports/wc_four_card_environment_CPU_R1_launch_20261020.json，job=wc-fourcard-env-r1-20261020。真实启动后相同capture工具--kind environment --mode admission一次，按真实launch+1800/+5400各另约一次；终态仅从保存原件调用公开analyze入口--kind environment。

完整环境核对11关键runtime SHA、实际GitHub HEAD、manifest/source、全部命令、CPU请求导入和freeze；production_CPU_accepted/GPU_dispatch_ready仍false。GitHub原镜像进程若尚跑，保留并按进度另约一次，不重克隆/循环等。模型固定资产和驱动兼容单独保留，不修改共享驱动或提前跑GPU。
